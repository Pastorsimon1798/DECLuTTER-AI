import 'dart:async';
import 'dart:convert';
import 'dart:io' show File, Platform;

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:image/image.dart' as img;

import '../domain/detection.dart';
import 'detection_interpreter.dart';
import 'image_tensor_builder.dart';
import 'onnx_detection_interpreter.dart';
import 'output_tensor_buffer.dart';
import '_tflite_initializer.dart'
    if (dart.library.html) '_tflite_initializer_web.dart';

/// Loads the object detection model and produces debug detections.
///
/// The real TFLite inference is guarded behind platform checks so the
/// development environment (which lacks the native runtime) still works by
/// returning mock detections from a JSON asset. This keeps the UI plumbing and
/// async flow realistic for the MVP.
class DetectorService {
  static const Duration _mockInferenceDuration = Duration(milliseconds: 120);

  DetectorService({
    AssetBundle? bundle,
    DetectionInterpreter? interpreter,
    bool? isMobileOverride,
    String modelAssetPath = 'model/detector.onnx',
  })  : _bundle = bundle ?? rootBundle,
        _providedInterpreter = interpreter,
        _interpreter = interpreter,
        _isMobileOverride = isMobileOverride,
        _modelAssetPath = modelAssetPath;

  final AssetBundle _bundle;
  final DetectionInterpreter? _providedInterpreter;
  DetectionInterpreter? _interpreter;

  List<String> _labels = const [];
  bool _isInitialized = false;
  bool _useMockDetections = false;
  final bool? _isMobileOverride;
  final String _modelAssetPath;

  bool get _isMobilePlatform {
    if (_isMobileOverride != null) {
      return _isMobileOverride;
    }
    if (kIsWeb) {
      return false;
    }
    return Platform.isAndroid || Platform.isIOS;
  }

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

    if (_isMobilePlatform) {
      try {
        final DetectionInterpreter interpreter;
        if (_modelAssetPath.endsWith('.onnx')) {
          interpreter =
              await OnnxDetectionInterpreter.fromAsset(_modelAssetPath);
        } else if (_modelAssetPath.endsWith('.tflite')) {
          final tfliteInterpreter =
              await createTfliteInterpreter(_modelAssetPath);
          if (tfliteInterpreter == null) {
            throw FlutterError(
              'TFLite interpreter is not available on this platform.',
            );
          }
          interpreter = tfliteInterpreter;
        } else {
          throw FlutterError(
            'Unsupported model format: $_modelAssetPath. '
            'Expected .onnx or .tflite.',
          );
        }
        _interpreter = interpreter;
        _useMockDetections = false;
      } catch (error) {
        debugPrint(
            'DetectorService: failed to load model, falling back to mock data: $error');
        _useMockDetections = true;
      }
    } else {
      // Desktop/test environments use the mock asset instead of the native model.
      _useMockDetections = true;
    }

    _isInitialized = true;
  }

  /// Releases the interpreter and clears internal state.
  void dispose() {
    _interpreter?.close();
    _interpreter = null;
    _isInitialized = false;
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
      throw FlutterError(
          'Image at $imagePath does not exist. Capture before analyzing.');
    }

    final bytes = await file.readAsBytes();

    // Decode image on a separate isolate to avoid blocking UI thread
    final decoded = await compute(_decodeImageBytes, bytes);
    final originalSize = decoded != null
        ? Size(decoded.width.toDouble(), decoded.height.toDouble())
        : Size.zero;

    if (_useMockDetections || _interpreter == null) {
      return _mockDetectionResult(
        originalSize,
        reason: _useMockDetections
            ? 'Running in demo mode — model unavailable on this platform.'
            : 'Model interpreter not initialized.',
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
        isMocked: false,
        inferenceTime: stopwatch.elapsed,
      );
    } catch (error) {
      debugPrint(
          'DetectorService: inference failure ($error); using mock data.');
      stopwatch.stop();
      return _mockDetectionResult(
        originalSize,
        reason: 'Inference failed: $error',
      );
    }
  }

  /// Decodes image bytes on a separate isolate to prevent UI blocking.
  static img.Image? _decodeImageBytes(Uint8List bytes) {
    return img.decodeImage(bytes);
  }

  Future<DetectionResult> _mockDetectionResult(
    Size originalSize, {
    String? reason,
  }) async {
    final detections = await _loadMockDetections();
    return DetectionResult(
      detections: detections,
      originalSize: originalSize,
      isMocked: true,
      inferenceTime: _mockInferenceDuration,
      mockReason: reason ?? 'Using demo detections.',
    );
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
    final jsonString =
        await _bundle.loadString('assets/prompts/debug_sample_detections.json');
    final dynamic data = jsonDecode(jsonString);
    if (data is! Map<String, dynamic>) {
      return const [];
    }
    final detectionsData = data['detections'];
    if (detectionsData is! List) {
      return const [];
    }

    return detectionsData
        .map((dynamic entry) {
          if (entry is! Map<String, dynamic>) {
            return null;
          }
          final rawLabel = (entry['label'] as String?) ?? 'unknown';
          final label = _resolveLabel(rawLabel);
          final confidence = (entry['confidence'] as num?)?.toDouble() ?? 0;
          final box = entry['box'];
          if (box is! Map<String, dynamic>) {
            return Detection(
                label: label,
                confidence: confidence,
                boundingBox: const Rect.fromLTWH(0, 0, 0, 0));
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
        })
        .whereType<Detection>()
        .toList(growable: false);
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
    final input =
        ImageTensorBuilder(shape: inputTensor, type: inputType).build(image);

    final outputBuffers = _prepareOutputBuffers(interpreter);
    final outputs = <int, Object>{
      for (final buffer in outputBuffers) buffer.index: buffer.data,
    };

    await interpreter.runAsync(input, outputs);

    // Sync buffers with the outputs map. This is required for async backends
    // (e.g. ONNX) that return new data objects rather than mutating the
    // pre-allocated buffers in-place.
    for (final buffer in outputBuffers) {
      if (outputs.containsKey(buffer.index)) {
        buffer.data = outputs[buffer.index]!;
      }
    }

    return _parseDetections(outputBuffers);
  }

  List<OutputTensorBuffer> _prepareOutputBuffers(
      DetectionInterpreter interpreter) {
    final buffers = <OutputTensorBuffer>[];
    for (var i = 0; i < interpreter.outputCount; i++) {
      final shape = interpreter.outputShape(i);
      final type = interpreter.outputType(i);
      buffers.add(OutputTensorBuffer(index: i, shape: shape, type: type));
    }
    return buffers;
  }

  List<Detection> _parseDetections(List<OutputTensorBuffer> buffers) {
    OutputTensorBuffer? boxesBuffer;
    OutputTensorBuffer? classesBuffer;
    OutputTensorBuffer? scoresBuffer;
    OutputTensorBuffer? countBuffer;

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
      if (boxesBuffer == null &&
          shape.length == 3 &&
          shape.first == 1 &&
          shape.last == 4) {
        boxesBuffer = buffer;
      } else if (classesBuffer == null &&
          shape.length == 2 &&
          shape.first == 1) {
        classesBuffer = buffer;
      } else if (scoresBuffer == null &&
          shape.length == 2 &&
          shape.first == 1) {
        scoresBuffer = buffer;
      } else if (countBuffer == null && shape.length == 1) {
        countBuffer = buffer;
      }
    }

    final boxesData = boxesBuffer?.data;
    final classesData = classesBuffer?.data;
    final scoresData = scoresBuffer?.data;
    if (boxesData == null || classesData == null || scoresData == null) {
      return const [];
    }

    final boxes = _castToBoxList(boxesData);
    final classes = _castToDoubleList(classesData);
    final scores = _castToDoubleList(scoresData);
    final countData = countBuffer?.data;
    final total = countData != null
        ? _readFirstDouble(countData)?.round() ?? boxes.length
        : boxes.length;

    final detections = <Detection>[];
    for (var i = 0;
        i < total &&
            i < boxes.length &&
            i < classes.length &&
            i < scores.length;
        i++) {
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
      final label = classIndex >= 0 && classIndex < _labels.length
          ? _labels[classIndex]
          : classIndex.toString();

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
    final batch = _unwrapBatch(data);
    return batch
        .map((entry) =>
            _toIterable(entry).map(_asDouble).toList(growable: false))
        .where((entry) => entry.isNotEmpty)
        .toList(growable: false);
  }

  List<double> _castToDoubleList(Object data) {
    final batch = _unwrapBatch(data);
    if (batch.isEmpty) {
      return const [];
    }
    return batch.map(_asDouble).toList(growable: false);
  }

  Iterable<Object?> _unwrapBatch(Object? data) {
    final iterable = _toIterable(data);
    if (iterable.isEmpty) {
      return const <Object?>[];
    }
    final list = iterable.toList(growable: false);
    if (list.isEmpty) {
      return const <Object?>[];
    }
    final first = list.first;
    if (first is Iterable) {
      return first.cast<Object?>();
    }
    return list;
  }

  Iterable<Object?> _toIterable(Object? value) {
    if (value is Iterable) {
      return value.cast<Object?>();
    }
    return const <Object?>[];
  }

  double? _readFirstDouble(Object data) {
    for (final value in _toIterable(data)) {
      return _asDouble(value);
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
