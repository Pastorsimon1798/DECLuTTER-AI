# TFLite Model Assets

This directory should contain your TensorFlow Lite object detection model files for DECLuTTER AI.

## Required Files

### 1. `detector.tflite`
Your quantized object detection model in TensorFlow Lite format.

**Requirements:**
- Input shape: `[1, height, width, 3]` (RGB image)
- Input type: `float32` (normalized 0.0-1.0) or `uint8` (0-255)
- Output format: Standard object detection with 4 tensors:
  - Tensor 0: Bounding boxes `[1, N, 4]` (top, left, bottom, right in normalized coordinates)
  - Tensor 1: Classes `[1, N]` (class indices)
  - Tensor 2: Scores `[1, N]` (confidence scores 0.0-1.0)
  - Tensor 3: Count `[1]` (number of valid detections)

### 2. `labels.txt`
Text file with one label per line, corresponding to class indices from your model.

**Format:**
```
background
cable
notebook
mug
book
pen
...
```

**Note:** Line 0 = class index 0, line 1 = class index 1, etc.

## Getting a Model

### Option 1: Use a Pre-trained Model
Download a compatible object detection model from:
- [TensorFlow Model Zoo](https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/tf2_detection_zoo.md)
- [MediaPipe Object Detection](https://developers.google.com/mediapipe/solutions/vision/object_detector)
- [TensorFlow Hub](https://tfhub.dev/s?deployment-format=lite&module-type=image-object-detection)

**Recommended for MVP:** EfficientDet-Lite0 or MobileNet SSD v2

### Option 2: Train a Custom Model
For household clutter detection, you may want to train on:
- Open Images Dataset (household objects)
- COCO dataset (common objects)
- Custom dataset of clutter items

**Training tools:**
- [TensorFlow Object Detection API](https://github.com/tensorflow/models/tree/master/research/object_detection)
- [AutoML Vision](https://cloud.google.com/automl)
- [YOLOv5/YOLOv8](https://github.com/ultralytics/ultralytics) with TFLite export

### Option 3: Development with Mock Data (Current)
If you don't have a model yet, the app will automatically use mock detections from `../prompts/debug_sample_detections.json`. This allows UI development to continue without a real model.

## Model Conversion

If you have a TensorFlow SavedModel or PyTorch model, convert it to TFLite:

```bash
# TensorFlow SavedModel to TFLite
tflite_convert \
  --saved_model_dir=path/to/saved_model \
  --output_file=detector.tflite \
  --optimization_default=DEFAULT \
  --representative_dataset=representative_dataset.py

# ONNX to TFLite (via TensorFlow)
pip install tf2onnx
python -m tf2onnx.convert --opset 13 --onnx model.onnx --output model.pb
tflite_convert --graph_def_file=model.pb --output_file=detector.tflite
```

## Quantization

For better mobile performance, quantize your model:

```python
import tensorflow as tf

converter = tf.lite.TFLiteConverter.from_saved_model('path/to/saved_model')
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.target_spec.supported_types = [tf.float16]  # or tf.int8

tflite_model = converter.convert()
with open('detector.tflite', 'wb') as f:
    f.write(tflite_model)
```

## Testing Your Model

After adding `detector.tflite` and `labels.txt`:

1. Rebuild the app:
   ```bash
   cd app
   flutter clean
   flutter pub get
   flutter run
   ```

2. Capture a test photo - the app will use your real model instead of mock data

3. Check the inference time in the UI (should be < 500ms on modern devices)

4. Verify detection accuracy with the debug bounding boxes

## Performance Targets

- **Inference time:** < 500ms on mid-range mobile devices
- **Model size:** < 20MB (ideally < 10MB)
- **Accuracy:** mAP > 0.5 for common household items
- **Memory:** < 100MB peak during inference

## Troubleshooting

**Model fails to load:**
- Verify file is actually `.tflite` format (not SavedModel or ONNX)
- Check model is compatible with TFLite runtime version in `pubspec.yaml`
- Review logs for specific error messages

**Poor inference performance:**
- Use quantized model (int8 or float16)
- Reduce input resolution
- Use hardware acceleration (NNAPI on Android, Metal on iOS)

**Low detection accuracy:**
- Verify labels.txt matches model's training classes
- Check image preprocessing (normalization range)
- Ensure model was trained on similar objects/lighting conditions

## Privacy & Security

⚠️ **Important:** All model inference happens on-device. Never upload user photos to cloud services without explicit opt-in consent. This is a core privacy principle of DECLuTTER AI.

## Further Resources

- [TFLite Flutter Plugin Docs](https://pub.dev/packages/tflite_flutter)
- [TensorFlow Lite Guide](https://www.tensorflow.org/lite/guide)
- [Object Detection Best Practices](https://www.tensorflow.org/lite/examples/object_detection/overview)
