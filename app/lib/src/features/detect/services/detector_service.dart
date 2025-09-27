import 'dart:async';
import 'dart:convert';
import 'dart:io' show File, Platform;
import 'dart:ui' show Rect, Size;

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:image/image.dart' as img;
import 'package:tflite_flutter/tflite_flutter.dart';

import '../domain/detection.dart';
import 'detection_interpreter.dart';

/// Loads the object detection model and produces debug detections.
///
/// The real TFLite inference is guarded behind platform checks so the
/// development environment (which lacks the native runtime) still works by
/// returning mock detections from a JSON asset. This keeps the UI plumbing and
/// async flow realistic for the MVP.
class DetectorService {

  DetectorService({AssetBundle? bundle, DetectionInterpreter? interpreter})
      : _bundle = bundle ?? rootBundle,
        _providedInterpreter = interpreter,
        _interpreter = interpreter;

  final AssetBundle _bundle;
  final DetectionInterpreter? _providedInterpreter;
  DetectionInterpreter? _interpreter;

  List<String> _labels = const [];
  bool _isInitialized = false;
  bool _useMockDetections = false;
  final bool? _isMobileOverride;

  /// Ensures the model (or fallback) is ready before inference.
  Future<void> initialize() async {
    if (_isInitialized) {
      return;
    }

    try {
      _labels = await _loadLabels();
    } catch (error) {
      debugPrint('DetectorService: could not load labels: $error');
      _labels = const [];
    }

    if (kIsWeb) {
      _useMockDetections = true;
      _isInitialized = true;
      return;
    }


    if (_providedInterpreter != null) {
      _interpreter = _providedInterpreter;
      _useMockDetections = false;
      _isInitialized = true;
      return;
    }

    if (Platform.isAndroid || Platform.isIOS) {
      try {
        final interpreter = await TfliteDetectionInterpreter.fromAsset('model/detector.tflite');
        _interpreter = interpreter;
        _useMockDetections = false;

      } catch (error) {
        debugPrint('DetectorService: failed to load model, falling back to mock data: $error');
        _useMockDetections = true;
      }
    } else {
      // Desktop/test environments use the mock asset instead of the native model.
      _useMockDetections = true;
    }

    _isInitialized = true;
  }

  /// Runs detection on the provided [imagePath]. If the real model is not
  /// available (e.g. in CI or local tests), it returns mock detections from the
  /// debug JSON asset to unblock UI development.
  Future<DetectionResult> detectOnImage(String imagePath) async {
    await initialize();

    if (kIsWeb) {
      return const DetectionResult.empty();
    }

    final file = File(imagePath);
    if (!await file.exists()) {
      throw FlutterError('Image at $imagePath does not exist. Capture before analyzing.');
    }

    final bytes = await file.readAsBytes();
    final decoded = img.decodeImage(bytes);
    final originalSize = decoded != null
        ? Size(decoded.width.toDouble(), decoded.height.toDouble())
        : Size.zero;

    if (_useMockDetections || _interpreter == null) {
      final detections = await _loadMockDetections();
      return DetectionResult(
        detections: detections,
        originalSize: originalSize,
        isMocked: true,
        inferenceTime: const Duration(milliseconds: 120),
      );
    }

    final stopwatch = Stopwatch()..start();
    try {
      if (decoded == null) {
        throw FlutterError('Unable to decode $imagePath into an image.');
      }
      final detections = await _runInterpreterOnImage(decoded);
      stopwatch.stop();
      return DetectionResult(
        detections: detections,
        originalSize: originalSize,
        isMocked: true,
        inferenceTime: stopwatch.elapsed,
      );
    } catch (error) {
      debugPrint('DetectorService: inference failure ($error); using mock data.');
      final detections = await _loadMockDetections();
      stopwatch.stop();
      return DetectionResult(
        detections: detections,
        originalSize: originalSize,
        isMocked: true,
        inferenceTime: stopwatch.elapsed,
      );
    }
  }

  Future<List<String>> _loadLabels() async {
    try {
      final raw = await _bundle.loadString('assets/model/labels.txt');
      return raw
          .split('\n')
          .map((line) => line.trim())
          .where((line) => line.isNotEmpty)
          .toList(growable: false);
    } catch (_) {
      return const [];
    }
  }

  Future<List<Detection>> _loadMockDetections() async {
    final jsonString = await _bundle.loadString('assets/prompts/debug_sample_detections.json');
    final dynamic data = jsonDecode(jsonString);
    if (data is! Map<String, dynamic>) {
      return const [];
    }
    final detectionsData = data['detections'];
    if (detectionsData is! List) {
      return const [];
    }

    return detectionsData.map((dynamic entry) {
      if (entry is! Map<String, dynamic>) {
        return null;
      }
      final rawLabel = (entry['label'] as String?) ?? 'unknown';
      final label = _resolveLabel(rawLabel);
      final confidence = (entry['confidence'] as num?)?.toDouble() ?? 0;
      final box = entry['box'];
      if (box is! Map<String, dynamic>) {
        return Detection(label: label, confidence: confidence, boundingBox: const Rect.fromLTWH(0, 0, 0, 0));
      }
      final left = (box['left'] as num?)?.toDouble() ?? 0;
      final top = (box['top'] as num?)?.toDouble() ?? 0;
      final right = (box['right'] as num?)?.toDouble() ?? left;
      final bottom = (box['bottom'] as num?)?.toDouble() ?? top;
      return Detection(
        label: label,
        confidence: confidence,
        boundingBox: Rect.fromLTRB(left, top, right, bottom),
      ).clamp();
    }).whereType<Detection>().toList(growable: false);
}

  String _resolveLabel(String rawLabel) {
    final index = int.tryParse(rawLabel);
    if (index != null && index >= 0 && index < _labels.length) {
      return _labels[index];
    }
    return rawLabel;
  }

  Future<List<Detection>> _runInterpreterOnImage(img.Image image) async {
    final interpreter = _interpreter;
    if (interpreter == null) {
      throw StateError('Interpreter has not been initialized.');
    }

    final inputTensor = interpreter.inputShape;
    final inputType = interpreter.inputType;
    final input = _createInputTensor(image, inputTensor, inputType);

    final outputBuffers = _prepareOutputBuffers(interpreter);
    final outputs = <int, Object>{
      for (final buffer in outputBuffers) buffer.index: buffer.data,
    };

    interpreter.run(input, outputs);

    return _parseDetections(outputBuffers);
  }

  Object _createInputTensor(img.Image image, List<int> inputShape, TfLiteType type) {
    if (inputShape.length != 4 || inputShape.first != 1) {
      throw FlutterError('Expected input shape [1, height, width, channels] but found $inputShape.');
    }

    final height = inputShape[1];
    final width = inputShape[2];
    final channels = inputShape[3];

    final resized = img.copyResize(image, width: width, height: height);

    return List.generate(1, (_) {
      return List.generate(height, (y) {
        return List.generate(width, (x) {
          final pixel = resized.getPixel(x, y);
          final r = img.getRed(pixel).toDouble();
          final g = img.getGreen(pixel).toDouble();
          final b = img.getBlue(pixel).toDouble();
          final a = img.getAlpha(pixel).toDouble();
          final values = <num>[];
          if (channels >= 1) {
            values.add(_normalizeValue(r, type));
          }
          if (channels >= 2) {
            values.add(_normalizeValue(g, type));
          }
          if (channels >= 3) {
            values.add(_normalizeValue(b, type));
          }
          if (channels >= 4) {
            values.add(_normalizeValue(a, type));
          }
          return values;
        });
      });
    });
  }

  num _normalizeValue(double value, TfLiteType type) {
    switch (type) {
      case TfLiteType.float32:
      case TfLiteType.float16:
        return value / 255.0;
      default:
        return value.round();
    }
  }

  List<_OutputTensorBuffer> _prepareOutputBuffers(DetectionInterpreter interpreter) {
    final buffers = <_OutputTensorBuffer>[];
    for (var i = 0; i < interpreter.outputCount; i++) {
      final shape = interpreter.outputShape(i);
      final type = interpreter.outputType(i);
      buffers.add(_OutputTensorBuffer(index: i, shape: shape, type: type));
    }
    return buffers;
  }

  List<Detection> _parseDetections(List<_OutputTensorBuffer> buffers) {
    _OutputTensorBuffer? boxesBuffer;
    _OutputTensorBuffer? classesBuffer;
    _OutputTensorBuffer? scoresBuffer;
    _OutputTensorBuffer? countBuffer;

    for (final buffer in buffers) {
      switch (buffer.index) {
        case 0:
          boxesBuffer = buffer;
          continue;
        case 1:
          classesBuffer = buffer;
          continue;
        case 2:
          scoresBuffer = buffer;
          continue;
        case 3:
          countBuffer = buffer;
          continue;
      }

      final shape = buffer.shape;
      if (boxesBuffer == null && shape.length == 3 && shape.first == 1 && shape.last == 4) {
        boxesBuffer = buffer;
      } else if (classesBuffer == null && shape.length == 2 && shape.first == 1) {
        classesBuffer = buffer;
      } else if (scoresBuffer == null && shape.length == 2 && shape.first == 1) {
        scoresBuffer = buffer;
      } else if (countBuffer == null && shape.length == 1) {
        countBuffer = buffer;
      }
    }

    if (boxesBuffer == null || classesBuffer == null || scoresBuffer == null) {
      return const [];
    }

    final boxes = _castToBoxList(boxesBuffer!.data);
    final classes = _castToDoubleList(classesBuffer!.data);
    final scores = _castToDoubleList(scoresBuffer!.data);
    final total = countBuffer != null ? _readFirstDouble(countBuffer!.data)?.round() ?? boxes.length : boxes.length;

    final detections = <Detection>[];
    for (var i = 0; i < total && i < boxes.length && i < classes.length && i < scores.length; i++) {
      final box = boxes[i];
      if (box.length < 4) {
        continue;
      }

      final top = box[0].clamp(0.0, 1.0);
      final left = box[1].clamp(0.0, 1.0);
      final bottom = box[2].clamp(0.0, 1.0);
      final right = box[3].clamp(0.0, 1.0);
      final score = scores[i].clamp(0.0, 1.0);
      final classIndex = classes[i].round();
      final label = classIndex >= 0 && classIndex < _labels.length ? _labels[classIndex] : classIndex.toString();

      detections.add(
        Detection(
          label: label,
          confidence: score,
          boundingBox: Rect.fromLTRB(left, top, right, bottom),
        ).clamp(),
      );
    }

    return detections;
  }

  List<List<double>> _castToBoxList(Object data) {
    if (data is List && data.isNotEmpty && data.first is List) {
      final first = data.first as List<dynamic>;
      return first
          .whereType<List>()
          .map((entry) => entry.map((value) => _asDouble(value)).toList(growable: false))
          .toList(growable: false);
    }
    return const [];
  }

  List<double> _castToDoubleList(Object data) {
    if (data is List && data.isNotEmpty) {
      final target = data.first;
      if (target is List) {
        return target.map((value) => _asDouble(value)).toList(growable: false);
      }
      return data.map((value) => _asDouble(value)).toList(growable: false);
    }
    return const [];
  }

  double? _readFirstDouble(Object data) {
    if (data is List && data.isNotEmpty) {
      return _asDouble(data.first);
    }
    return null;
  }

  double _asDouble(Object? value) {
    if (value is num) {
      return value.toDouble();
    }
    if (value is bool) {
      return value ? 1.0 : 0.0;
    }
    return 0.0;
  }
}

class _OutputTensorBuffer {
  _OutputTensorBuffer({
    required this.index,
    required this.shape,
    required this.type,
  }) : data = _createZeroFilledList(type, shape);

  final int index;
  final List<int> shape;
  final TfLiteType type;
  final Object data;

  static Object _createZeroFilledList(TfLiteType type, List<int> shape) {
    if (shape.isEmpty) {
      return _zeroValue(type);
    }
    final length = shape.first;
    final tail = shape.sublist(1);
    return List.generate(length, (_) => _createZeroFilledList(type, tail));
  }

  static Object _zeroValue(TfLiteType type) {
    switch (type) {
      case TfLiteType.float32:
      case TfLiteType.float16:
        return 0.0;
      case TfLiteType.bool:
        return false;
      default:
        return 0;
    }
  }
}
