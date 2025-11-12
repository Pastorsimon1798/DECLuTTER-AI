import 'dart:io';
import 'dart:typed_data';
import 'dart:ui';

import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:image/image.dart' as img;
import 'package:tflite_flutter/tflite_flutter.dart';

import 'package:declutter_ai/src/features/detect/services/detection_interpreter.dart';
import 'package:declutter_ai/src/features/detect/services/detector_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('DetectorService', () {
    test('falls back to mock detections when interpreter is unavailable', () async {
      final bundle = _MapAssetBundle({
        'assets/model/labels.txt': 'chair\nsofa\ntrash bag',
        'assets/prompts/debug_sample_detections.json':
            '{"detections": [{"label": "1", "confidence": 0.8, "box": {"left": 0.1, "top": 0.2, "right": 0.5, "bottom": 0.7}}]}',
      });

      final service = DetectorService(
        bundle: bundle,
        isMobileOverride: false,
      );

      final tempDir = await Directory.systemTemp.createTemp('detector_service_mock');
      final imageFile = File('${tempDir.path}/sample.jpg');
      final generated = img.Image(width: 160, height: 120);
      await imageFile.writeAsBytes(img.encodeJpg(generated));

      final result = await service.detectOnImage(imageFile.path);

      expect(result.isMocked, isTrue);
      expect(result.detections, hasLength(1));
      expect(result.detections.first.label, 'sofa');
      expect(result.originalSize, const Size(160, 120));
      expect(result.inferenceTime, const Duration(milliseconds: 120));

      await tempDir.delete(recursive: true);
    });

    test('runs interpreter and parses detections from fixture model', () async {
      final bundle = _MapAssetBundle({
        'assets/model/labels.txt': 'apple\nbanana\ncarrot',
        'assets/prompts/debug_sample_detections.json': '{"detections": []}',
      });

      final interpreter = _FixtureDetectionInterpreter();
      final service = DetectorService(
        bundle: bundle,
        interpreter: interpreter,
      );

      final tempDir = await Directory.systemTemp.createTemp('detector_service_fixture');
      final imageFile = File('${tempDir.path}/fixture.png');
      final generated = img.Image(width: 8, height: 8);
      for (var y = 0; y < generated.height; y++) {
        for (var x = 0; x < generated.width; x++) {
          final value = (x + y) % 255;
          generated.setPixelRgba(x, y, value, value ~/ 2, 255 - value);
        }
      }
      await imageFile.writeAsBytes(img.encodePng(generated));

      final result = await service.detectOnImage(imageFile.path);

      expect(result.isMocked, isFalse);
      expect(result.detections, hasLength(1));
      final detection = result.detections.first;
      expect(detection.label, 'banana');
      expect(detection.confidence, closeTo(0.87, 1e-3));
      expect(detection.boundingBox.left, closeTo(0.2, 1e-6));
      expect(detection.boundingBox.top, closeTo(0.1, 1e-6));
      expect(detection.boundingBox.right, closeTo(0.75, 1e-6));
      expect(detection.boundingBox.bottom, closeTo(0.65, 1e-6));
      expect(result.inferenceTime, isNotNull);

      expect(interpreter.lastInputShape, equals(const [1, 4, 4, 3]));
      expect(interpreter.lastMinValue, greaterThanOrEqualTo(0.0));
      expect(interpreter.lastMaxValue, lessThanOrEqualTo(1.0));
      expect(
        interpreter.lastMaxValue,
        greaterThan(interpreter.lastMinValue ?? 0),
        reason: 'input should contain a range of normalized values',
      );

      await tempDir.delete(recursive: true);
    });

    test('falls back to mock detections when interpreter throws during run', () async {
      final bundle = _MapAssetBundle({
        'assets/model/labels.txt': 'apple\nbanana',
        'assets/prompts/debug_sample_detections.json':
            '{"detections": [{"label": "apple", "confidence": 0.6, "box": {"left": 0.05, "top": 0.1, "right": 0.45, "bottom": 0.5}}]}',
      });

      final interpreter = _ThrowingInterpreter();
      final service = DetectorService(
        bundle: bundle,
        interpreter: interpreter,
      );

      final tempDir = await Directory.systemTemp.createTemp('detector_service_throw');
      final imageFile = File('${tempDir.path}/fixture.png');
      final generated = img.Image(width: 8, height: 8);
      await imageFile.writeAsBytes(img.encodePng(generated));

      final result = await service.detectOnImage(imageFile.path);

      expect(result.isMocked, isTrue);
      expect(result.detections, hasLength(1));
      expect(result.detections.first.label, 'apple');

      await tempDir.delete(recursive: true);
    });
  });

  test('detector service keeps mock flag when interpreter throws', () async {
    final bundle = _MapAssetBundle({
      'assets/model/labels.txt': 'apple\nbanana',
      'assets/prompts/debug_sample_detections.json':
          '{"detections": [{"label": "0", "confidence": 0.5, "box": {"left": 0.1, "top": 0.2, "right": 0.3, "bottom": 0.4}}]}',
    });

    final interpreter = _TrackingThrowingInterpreter();
    final service = DetectorService(bundle: bundle, interpreter: interpreter);

    final tempDir = await Directory.systemTemp.createTemp('detector_test_throwing_interpreter');
    final imageFile = File('${tempDir.path}/sample.jpg');
    final generated = img.Image(width: 16, height: 16);
    await imageFile.writeAsBytes(img.encodeJpg(generated));

    final result = await service.detectOnImage(imageFile.path);

    expect(interpreter.runCallCount, greaterThan(0), reason: 'interpreter should have been invoked before falling back');
    expect(result.isMocked, isTrue);
    expect(result.detections, isNotEmpty);
    expect(result.inferenceTime, equals(const Duration(milliseconds: 120)));

    await tempDir.delete(recursive: true);
  });
}

class _MapAssetBundle extends CachingAssetBundle {
  _MapAssetBundle(this.values);

  final Map<String, String> values;

  @override
  Future<String> loadString(String key, {bool cache = true}) async {
    final value = values[key];
    if (value == null) {
      throw FlutterError('Missing asset: $key');
    }
    return value;
  }
}

class _FixtureDetectionInterpreter implements DetectionInterpreter {
  _FixtureDetectionInterpreter()
      : _boxesShape = const [1, 5, 4],
        _classesShape = const [1, 5],
        _scoresShape = const [1, 5],
        _countShape = const [1];

  final List<int> _boxesShape;
  final List<int> _classesShape;
  final List<int> _scoresShape;
  final List<int> _countShape;

  double? lastMinValue;
  double? lastMaxValue;
  List<int>? lastInputShape;

  @override
  List<int> get inputShape => const [1, 4, 4, 3];

  @override
  TfLiteType get inputType => TfLiteType.float32;

  @override
  int get outputCount => 4;

  @override
  List<int> outputShape(int index) {
    switch (index) {
      case 0:
        return _boxesShape;
      case 1:
        return _classesShape;
      case 2:
        return _scoresShape;
      case 3:
        return _countShape;
      default:
        throw RangeError.index(index, const []);
    }
  }

  @override
  TfLiteType outputType(int index) => TfLiteType.float32;

  @override
  void run(Object input, Map<int, Object> outputs) {
    expect(input, isA<List>());
    final batch = input as List<dynamic>;
    expect(batch, hasLength(1));

    final rows = batch.first as List<dynamic>;
    expect(rows, hasLength(4));
    final columns = rows.first as List<dynamic>;
    expect(columns, hasLength(4));
    final channels = columns.first as List<dynamic>;
    expect(channels, hasLength(3));

    var minValue = double.infinity;
    var maxValue = -double.infinity;
    for (final row in rows) {
      for (final column in row as List<dynamic>) {
        for (final value in column as List<dynamic>) {
          final numeric = (value as num).toDouble();
          minValue = minValue < numeric ? minValue : numeric;
          maxValue = maxValue > numeric ? maxValue : numeric;
          expect(numeric, inInclusiveRange(0.0, 1.0));
        }
      }
    }

    lastInputShape = const [1, 4, 4, 3];
    lastMinValue = minValue;
    lastMaxValue = maxValue;

    final boxes = outputs[0] as List<dynamic>;
    final boxBatch = boxes[0] as List<dynamic>;
    boxBatch[0] = Float32List.fromList([0.1, 0.2, 0.65, 0.75]);

    final classes = outputs[1] as List<dynamic>;
    classes[0] = Float32List.fromList([1, 0, 0, 0, 0]);

    final scores = outputs[2] as List<dynamic>;
    scores[0] = Float32List.fromList([0.87, 0, 0, 0, 0]);

    final count = outputs[3] as List<dynamic>;
    count[0] = Float32List.fromList([1]);
  }
}


class _ThrowingInterpreter implements DetectionInterpreter {
  @override
  List<int> get inputShape => const [1, 4, 4, 3];


  @override
  TfLiteType get inputType => TfLiteType.float32;

  @override
  int get outputCount => 4;

  @override
  List<int> outputShape(int index) => const [1, 5];

  @override
  TfLiteType outputType(int index) => TfLiteType.float32;

  @override
  void run(Object input, Map<int, Object> outputs) {
    throw StateError('inference failure');
  }
}

class _TrackingThrowingInterpreter implements DetectionInterpreter {
  int runCallCount = 0;

  @override
  List<int> get inputShape => const [1, 4, 4, 3];

  @override
  TfLiteType get inputType => TfLiteType.float32;

  @override
  int get outputCount => 4;

  @override
  List<int> outputShape(int index) => const [1, 5];

  @override
  TfLiteType outputType(int index) => TfLiteType.float32;

  @override
  void run(Object input, Map<int, Object> outputs) {
    runCallCount += 1;
    throw StateError('forced failure');
  }
}

