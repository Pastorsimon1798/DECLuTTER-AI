import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:onnxruntime/onnxruntime.dart';

import '../domain/tensor_type.dart';
import 'detection_interpreter.dart';

/// ONNX Runtime-backed implementation of [DetectionInterpreter].
///
/// Loads a `.onnx` model from assets and runs inference via the
/// `onnxruntime` package. This adapter maps ONNX tensor metadata to the
/// platform-agnostic [TensorType] enum so the rest of the detection pipeline
/// (image tensor builder, output buffer parser) works unchanged.
///
/// To use this interpreter, place a converted ONNX model at
/// `assets/model/detector.onnx` and pass it to [DetectorService]:
///
/// ```dart
/// final interpreter = await OnnxDetectionInterpreter.fromAsset(
///   'assets/model/detector.onnx',
/// );
/// final service = DetectorService(interpreter: interpreter);
/// ```
class OnnxDetectionInterpreter implements DetectionInterpreter {
  OnnxDetectionInterpreter._(this._session, this._outputNames);

  final OrtSession _session;
  final List<String> _outputNames;

  List<int>? _inputShape;
  TensorType? _inputType;
  final Map<int, List<int>> _outputShapes = {};
  final Map<int, TensorType> _outputTypes = {};

  static Future<OnnxDetectionInterpreter> fromAsset(String assetPath) async {
    OrtEnv.instance.init();
    final rawAsset = await rootBundle.load(assetPath);
    final bytes = rawAsset.buffer.asUint8List();
    final sessionOptions = OrtSessionOptions();
    final session = OrtSession.fromBuffer(bytes, sessionOptions);
    sessionOptions.release();

    final inputNames = session.inputNames;
    final outputNames = session.outputNames;

    if (inputNames.isEmpty) {
      throw FlutterError('ONNX model has no inputs.');
    }

    return OnnxDetectionInterpreter._(
      session,
      outputNames,
    );
  }

  @override
  List<int> get inputShape {
    _inputShape ??= _fetchInputShape();
    return _inputShape!;
  }

  @override
  TensorType get inputType {
    _inputType ??= _fetchInputType();
    return _inputType!;
  }

  @override
  int get outputCount => _outputNames.length;

  @override
  List<int> outputShape(int index) {
    return _outputShapes.putIfAbsent(index, () => _fetchOutputShape(index));
  }

  @override
  TensorType outputType(int index) {
    return _outputTypes.putIfAbsent(index, () => _fetchOutputType(index));
  }

  @override
  void run(Object input, Map<int, Object> outputs) {
    // TODO: DetectionInterpreter.run() is synchronous but ONNX only provides
    // runAsync(). When ONNX is adopted, the interface needs to become async.
    throw UnsupportedError(
      'ONNX inference requires an async run() interface. '
      'Update DetectionInterpreter.run() to return Future<void> and '
      'propagate async through DetectorService.',
    );
  }

  @override
  void close() {
    _session.release();
  }

  List<int> _fetchInputShape() {
    // ONNX shape info is available via OrtValueTensor.createTensorWithDataList
    // metadata. We infer it from the model by creating a dummy tensor.
    // Alternatively, parse from model metadata if the API exposes it.
    // For now, we return a common object-detection shape and let the
    // caller (DetectorService) adjust based on actual model metadata.
    //
    // TODO: Query actual input shape from ONNX model metadata when the
    // onnxruntime package exposes it.
    return const [1, 300, 300, 3];
  }

  TensorType _fetchInputType() {
    // TODO: Query actual input type from ONNX model metadata.
    return TensorType.float32;
  }

  List<int> _fetchOutputShape(int index) {
    // TODO: Query actual output shape from ONNX model metadata.
    switch (index) {
      case 0:
        return const [1, 10, 4];
      case 1:
        return const [1, 10];
      case 2:
        return const [1, 10];
      case 3:
        return const [1];
      default:
        return const [1];
    }
  }

  TensorType _fetchOutputType(int index) {
    // TODO: Query actual output type from ONNX model metadata.
    return TensorType.float32;
  }
}
