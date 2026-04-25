import 'detection_interpreter.dart';
import 'tflite_detection_interpreter.dart';

Future<DetectionInterpreter?> createTfliteInterpreter(String assetPath) async {
  return await TfliteDetectionInterpreter.fromAsset(assetPath);
}
