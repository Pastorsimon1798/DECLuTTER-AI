import 'dart:io';

import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:image/image.dart' as img;
import 'package:tflite_flutter/tflite_flutter.dart';

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
