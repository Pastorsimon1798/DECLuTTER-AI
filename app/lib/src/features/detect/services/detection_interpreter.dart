import 'package:tflite_flutter/tflite_flutter.dart';

/// A small abstraction over [Interpreter] so tests can supply a fake
/// implementation without requiring the native TFLite runtime.
abstract class DetectionInterpreter {
  /// Input tensor shape, typically `[1, height, width, channels]`.
  List<int> get inputShape;

  /// Data type expected by the input tensor.
  TfLiteType get inputType;

  /// Total number of output tensors.
  int get outputCount;

  /// Shape of the output tensor at [index].
  List<int> outputShape(int index);

  /// Data type of the output tensor at [index].
  TfLiteType outputType(int index);

  /// Runs inference using the provided [input] and fills [outputs].
  void run(Object input, Map<int, Object> outputs);
}

/// Default implementation backed by the real TFLite [Interpreter].
class TfliteDetectionInterpreter implements DetectionInterpreter {
  TfliteDetectionInterpreter(this._interpreter);

  final Interpreter _interpreter;

  static Future<TfliteDetectionInterpreter> fromAsset(String assetPath) async {
    final interpreter = await Interpreter.fromAsset(assetPath);
    interpreter.allocateTensors();
    return TfliteDetectionInterpreter(interpreter);
  }

  @override
  List<int> get inputShape => _interpreter.getInputTensor(0).shape;

  @override
  TfLiteType get inputType => _interpreter.getInputTensor(0).type;

  @override
  int get outputCount => _interpreter.getOutputTensorCount();

  @override
  List<int> outputShape(int index) => _interpreter.getOutputTensor(index).shape;

  @override
  TfLiteType outputType(int index) => _interpreter.getOutputTensor(index).type;

  @override
  void run(Object input, Map<int, Object> outputs) {
    _interpreter.runForMultipleInputs([input], outputs);
  }
}
