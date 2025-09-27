import 'package:tflite_flutter/tflite_flutter.dart';

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
  final TfLiteType type;

  /// Nested list structure passed to `Interpreter.run` for this tensor.
  final Object data;

  static Object _createStorage(TfLiteType type, List<int> shape) {
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

  static Object _createLeaf(TfLiteType type, int length) {
    switch (type) {
      case TfLiteType.float32:
      case TfLiteType.float16:
        return List<double>.filled(length, 0.0);
      case TfLiteType.int8:
      case TfLiteType.uint8:
      case TfLiteType.int16:
      case TfLiteType.uint16:
      case TfLiteType.int32:
      case TfLiteType.int64:
        return List<int>.filled(length, 0);
      case TfLiteType.bool:
        return List<bool>.filled(length, false);
      default:
        return List<dynamic>.filled(length, _zeroValue(type));
    }
  }

  static Object _zeroValue(TfLiteType type) {
    switch (type) {
      case TfLiteType.float32:
      case TfLiteType.float16:
        return 0.0;
      case TfLiteType.bool:
        return false;
      default:
        return 0;
    }
  }
}
