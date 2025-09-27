import 'dart:io';

import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:image/image.dart' as img;
import 'package:tflite_flutter/tflite_flutter.dart';

import 'package:declutter_ai/src/features/detect/services/detection_interpreter.dart';
import 'package:declutter_ai/src/features/detect/services/detector_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('detector service falls back to mock detections when model is missing', () async {
    final bundle = _FakeAssetBundle(
      assets: {
        'assets/model/labels.txt': 'chair',
        'assets/prompts/debug_sample_detections.json':
            '{"detections": [{"label": "0", "confidence": 0.75, "box": {"left": 1, "top": 2, "right": 3, "bottom": 4}}]}',
      },
    );
    final service = DetectorService(
      bundle: bundle,
      interpreterFactory: () async => throw Exception('missing model'),
      isMobileOverride: true,
    );

    final tempDir = await Directory.systemTemp.createTemp('detector_test');
    final imageFile = File('${tempDir.path}/sample.jpg');
    final generated = img.Image(width: 640, height: 480);
    await imageFile.writeAsBytes(img.encodeJpg(generated));

    final result = await service.detectOnImage(imageFile.path);

    expect(result.isMocked, isTrue);
    expect(result.detections, isNotEmpty);
    expect(result.originalSize.width, greaterThan(0));
    expect(result.originalSize.height, greaterThan(0));
    expect(result.inferenceTime, equals(const Duration(milliseconds: 120)));

    await tempDir.delete(recursive: true);
  });

  test('detector service reports mock flag even when interpreter is injected', () async {
    final bundle = _FakeAssetBundle(
      assets: {
        'assets/model/labels.txt': 'chair',
        'assets/prompts/debug_sample_detections.json':
            '{"detections": [{"label": "0", "confidence": 0.42, "box": {"left": 10, "top": 20, "right": 30, "bottom": 40}}]}',
      },
    );
    final service = DetectorService(
      bundle: bundle,
      interpreterFactory: () async => _FakeInterpreter(),
      isMobileOverride: true,
    );

    final tempDir = await Directory.systemTemp.createTemp('detector_test_interpreter');
    final imageFile = File('${tempDir.path}/sample.jpg');
    final generated = img.Image(width: 320, height: 240);
    await imageFile.writeAsBytes(img.encodeJpg(generated));

    final result = await service.detectOnImage(imageFile.path);

    expect(result.isMocked, isTrue, reason: 'UI should mark interpreter mocks as mocked');
    expect(result.detections, isNotEmpty);
    expect(result.inferenceTime, isNot(const Duration(milliseconds: 120)));

    await tempDir.delete(recursive: true);
  });

  test('detector service returns detections from provided interpreter', () async {
    final bundle = _MapAssetBundle({
      'assets/model/labels.txt': 'apple\nbanana\ncarrot',
      'assets/prompts/debug_sample_detections.json': '{"detections": []}',
    });

    final interpreter = _FakeDetectionInterpreter();
    final service = DetectorService(bundle: bundle, interpreter: interpreter);

    final tempDir = await Directory.systemTemp.createTemp('detector_test_inference');
    final imageFile = File('${tempDir.path}/sample.jpg');
    final generated = img.Image(width: 8, height: 8);
    await imageFile.writeAsBytes(img.encodeJpg(generated));

    final result = await service.detectOnImage(imageFile.path);

    expect(result.isMocked, isFalse);
    expect(result.detections, hasLength(1));
    final detection = result.detections.first;
    expect(detection.label, 'banana');
    expect(detection.confidence, closeTo(0.85, 1e-6));
    expect(detection.boundingBox.left, closeTo(0.2, 1e-6));
    expect(detection.boundingBox.top, closeTo(0.1, 1e-6));
    expect(detection.boundingBox.right, closeTo(0.7, 1e-6));
    expect(detection.boundingBox.bottom, closeTo(0.6, 1e-6));
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

class _FakeDetectionInterpreter implements DetectionInterpreter {
  _FakeDetectionInterpreter()
      : _outputShapes = const [
          [1, 5, 4],
          [1, 5],
          [1, 5],
          [1],
        ];

  final List<List<int>> _outputShapes;

  @override
  List<int> get inputShape => const [1, 8, 8, 3];

  @override
  TfLiteType get inputType => TfLiteType.float32;

  @override
  int get outputCount => _outputShapes.length;

  @override
  List<int> outputShape(int index) => _outputShapes[index];

  @override
  TfLiteType outputType(int index) => TfLiteType.float32;

  @override
  void run(Object input, Map<int, Object> outputs) {
    final boxes = outputs[0] as List;
    final batch = boxes[0] as List;
    final firstBox = batch[0] as List;
    firstBox[0] = 0.1;
    firstBox[1] = 0.2;
    firstBox[2] = 0.6;
    firstBox[3] = 0.7;

    final classes = outputs[1] as List;
    final classBatch = classes[0] as List;
    classBatch[0] = 1.0;

    final scores = outputs[2] as List;
    final scoreBatch = scores[0] as List;
    scoreBatch[0] = 0.85;

    final count = outputs[3] as List;
    count[0] = 1.0;
  }
}

class _FakeInterpreter extends Fake implements Interpreter {}

class _FakeAssetBundle extends CachingAssetBundle {
  _FakeAssetBundle({required Map<String, String> assets}) : _assets = assets;

  final Map<String, String> _assets;

  @override
  Future<String> loadString(String key, {bool cache = true}) async {
    final value = _assets[key];
    if (value == null) {
      throw FlutterError('Missing fake asset for $key');
    }
    return value;
  }
}
