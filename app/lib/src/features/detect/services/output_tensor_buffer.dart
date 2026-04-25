import '../domain/tensor_type.dart';

/// Utility holder for allocating zero-filled output buffers that match the
/// interpreter's tensor metadata. The interpreter will mutate the nested list
/// in-place during [DetectionInterpreter.run].
class OutputTensorBuffer {
  OutputTensorBuffer({
    required this.index,
    required this.shape,
    required this.type,
  }) : data = _createStorage(type, shape);

  final int index;
  final List<int> shape;
  final TensorType type;

  /// Nested list structure passed to `Interpreter.run` for this tensor.
  ///
  /// This is mutable so async backends (e.g. ONNX) can replace the buffer
  /// with a new data object after inference.
  Object data;

  static Object _createStorage(TensorType type, List<int> shape) {
    if (shape.isEmpty) {
      return _zeroValue(type);
    }

    final length = shape.first;
    final tail = shape.sublist(1);

    if (tail.isEmpty) {
      return _createLeaf(type, length);
    }

    return List.generate(length, (_) => _createStorage(type, tail));
  }

  static Object _createLeaf(TensorType type, int length) {
    switch (type) {
      case TensorType.float32:
      case TensorType.float16:
        return List<double>.filled(length, 0.0);
      case TensorType.int8:
      case TensorType.uint8:
      case TensorType.int16:
      case TensorType.uint16:
      case TensorType.int32:
      case TensorType.int64:
        return List<int>.filled(length, 0);
      case TensorType.boolean:
        return List<bool>.filled(length, false);
    }
  }

  static Object _zeroValue(TensorType type) {
    switch (type) {
      case TensorType.float32:
      case TensorType.float16:
        return 0.0;
      case TensorType.boolean:
        return false;
      default:
        return 0;
    }
  }
}
