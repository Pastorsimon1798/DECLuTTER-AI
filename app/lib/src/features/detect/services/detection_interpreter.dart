import '../domain/tensor_type.dart';

/// A small abstraction over the underlying inference runtime so tests can
/// supply a fake implementation without requiring a native runtime.
///
/// The interface is intentionally runtime-agnostic — it works with both
/// TFLite and ONNX backends.
abstract class DetectionInterpreter {
  /// Input tensor shape, typically `[1, height, width, channels]`.
  List<int> get inputShape;

  /// Data type expected by the input tensor.
  TensorType get inputType;

  /// Total number of output tensors.
  int get outputCount;

  /// Shape of the output tensor at [index].
  List<int> outputShape(int index);

  /// Data type of the output tensor at [index].
  TensorType outputType(int index);

  /// Runs inference using the provided [input] and fills [outputs].
  void run(Object input, Map<int, Object> outputs);

  /// Runs inference asynchronously using the provided [input] and fills [outputs].
  ///
  /// The default implementation delegates to [run] so existing TFLite-backed
  /// interpreters do not need to change during the ONNX migration.
  Future<void> runAsync(Object input, Map<int, Object> outputs) async {
    run(input, outputs);
  }

  /// Releases native resources held by the interpreter.
  void close();
}
