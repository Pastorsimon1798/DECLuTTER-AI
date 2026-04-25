/// Platform-agnostic tensor data type used by the detection pipeline.
///
/// This abstracts over TFLite's [TensorType] and ONNX's
/// [ONNXTensorElementDataType] so the same [ImageTensorBuilder] and
/// [OutputTensorBuffer] can work with either runtime.
enum TensorType {
  float32,
  float16,
  int8,
  uint8,
  int16,
  uint16,
  int32,
  int64,
  boolean,
}
