import 'dart:async';
import 'dart:convert';
import 'dart:io' show File, Platform;
import 'dart:ui' show Rect, Size;

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:image/image.dart' as img;
import 'package:tflite_flutter/tflite_flutter.dart';

import '../domain/detection.dart';

/// Loads the object detection model and produces debug detections.
///
/// The real TFLite inference is guarded behind platform checks so the
/// development environment (which lacks the native runtime) still works by
/// returning mock detections from a JSON asset. This keeps the UI plumbing and
/// async flow realistic for the MVP.
class DetectorService {
  DetectorService({
    AssetBundle? bundle,
    FutureOr<Interpreter?> Function()? interpreterFactory,
    bool? isMobileOverride,
  })  : _bundle = bundle ?? rootBundle,
        _interpreterFactory =
            interpreterFactory ?? (() => Interpreter.fromAsset('model/detector.tflite')),
        _isMobileOverride = isMobileOverride;

  final AssetBundle _bundle;
  final FutureOr<Interpreter?> Function() _interpreterFactory;
  Interpreter? _interpreter;
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

    final bool isMobile = _isMobileOverride ?? (Platform.isAndroid || Platform.isIOS);

    if (isMobile) {
      try {
        final interpreter = await _interpreterFactory();
        if (interpreter != null) {
          _interpreter = interpreter;
          _useMockDetections = false;
        } else {
          _useMockDetections = true;
        }
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
      // TODO: Wire real preprocessing and interpreter invocation.
      // The structure is left in place so mobile engineers can plug in the
      // actual tensor conversion code once the model file is available.
      final detections = await _loadMockDetections();
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
}
