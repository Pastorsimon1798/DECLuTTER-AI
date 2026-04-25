import 'package:tflite_flutter/tflite_flutter.dart' as tflite;

import '../domain/tensor_type.dart';
import 'detection_interpreter.dart';

/// Default implementation backed by the real TFLite [Interpreter].
class TfliteDetectionInterpreter implements DetectionInterpreter {
  TfliteDetectionInterpreter(this._interpreter);

  final tflite.Interpreter _interpreter;

  static Future<TfliteDetectionInterpreter> fromAsset(String assetPath) async {
    final interpreter = await tflite.Interpreter.fromAsset(assetPath);
    interpreter.allocateTensors();
    return TfliteDetectionInterpreter(interpreter);
  }

  @override
  List<int> get inputShape => _interpreter.getInputTensor(0).shape;

  @override
  TensorType get inputType =>
      _mapTfliteType(_interpreter.getInputTensor(0).type);

  @override
  int get outputCount => _interpreter.getOutputTensors().length;

  @override
  List<int> outputShape(int index) =>
      _interpreter.getOutputTensor(index).shape;

  @override
  TensorType outputType(int index) =>
      _mapTfliteType(_interpreter.getOutputTensor(index).type);

  @override
  void run(Object input, Map<int, Object> outputs) {
    _interpreter.runForMultipleInputs([input], outputs);
  }

  @override
  Future<void> runAsync(Object input, Map<int, Object> outputs) async {
    run(input, outputs);
  }

  @override
  void close() {
    _interpreter.close();
  }

  static TensorType _mapTfliteType(tflite.TensorType type) {
    switch (type) {
      case tflite.TensorType.float32:
        return TensorType.float32;
      case tflite.TensorType.float16:
        return TensorType.float16;
      case tflite.TensorType.int8:
        return TensorType.int8;
      case tflite.TensorType.uint8:
        return TensorType.uint8;
      case tflite.TensorType.int16:
        return TensorType.int16;
      case tflite.TensorType.uint16:
        return TensorType.uint16;
      case tflite.TensorType.int32:
        return TensorType.int32;
      case tflite.TensorType.int64:
        return TensorType.int64;
      case tflite.TensorType.boolean:
        return TensorType.boolean;
      default:
        return TensorType.float32;
    }
  }
}
