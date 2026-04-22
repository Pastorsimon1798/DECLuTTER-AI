# DECLuTTER AI

This repository now includes the first Flutter scaffolding for the ADHD-friendly decluttering assistant described in the MVP docs, plus an initial FastAPI backend scaffold aligned to the 2026 launch plan.
The current build lets you capture a clutter "zone" photo, preview it, and jump straight into the 10-minute sprint timer with ADHD-friendly guardrails.

## Structure

- `DECLUTTER_AI_2026_LAUNCH_PLAN_WITH_PORTER_VALUE_CHAIN.md` — 2026 launch source of truth and implementation direction.
- `ADHD_Vision_Organizer_MVP_Docs_v0.1.md` — product brief, user stories, and acceptance criteria.
- `app/` — Flutter application source code for the MVP prototype.
  - `lib/src/features/capture/` — camera permissions + capture screen.
  - `lib/src/features/detect/` — detector service, debug overlays, and domain models.
  - `lib/src/features/session/` — timer flow and decision prep UI.
- `server/` — FastAPI backend scaffold for valuation/listing/agent flows.
  - `app/main.py` — API entrypoint and route registration.
  - `app/api/routes/` — launch modules (`analysis`, `valuation`, `listing_drafts`, `marketplace_ebay`, `public_listings`, `mcp`, `a2a`, `user_data`).
  - `tests/` — starter API tests.

## Getting Started

Because the container image does not ship with Flutter, install Flutter 3.19+ locally, then run:

```bash
cd app
flutter pub get
```

This pulls down the `camera`, `permission_handler`, `image`, and `tflite_flutter` packages needed for the capture + detection debug experience.

## Setting Up the TFLite Model

The app currently runs with **mock detections** for development purposes. To enable real on-device ML inference:

1. **Add your TensorFlow Lite model:**
   - Place `detector.tflite` at `app/assets/model/detector.tflite`
   - Place `labels.txt` at `app/assets/model/labels.txt`
   - See detailed requirements in `app/assets/model/README.md`

2. **Or use the example labels:**
   ```bash
   cd app/assets/model
   cp labels.txt.example labels.txt
   # Then add your detector.tflite model
   ```

3. **Recommended starter models:**
   - [EfficientDet-Lite0](https://tfhub.dev/tensorflow/efficientdet/lite0/detection/1)
   - [MobileNet SSD v2](https://tfhub.dev/tensorflow/ssd_mobilenet_v2/2)

The detector service automatically:
- Resizes captured images to match your model's input tensor shape
- Normalizes RGB values to `0.0–1.0` for float32 models
- Keeps `0–255` values for int8/uint8 quantized models
- Falls back to mock detections if model is unavailable

**Without a model file:** The app loads `debug_sample_detections.json` so you can still develop and test the UI flow.

Next, launch the app on a real device or simulator with camera support:

```bash
flutter run
```

To execute the starter widget test:

```bash
cd app
flutter test
```

## What works today

- **Capture:** Request camera access, show a live preview, and snap one focused zone.
- **Review:** Preview the saved image (mobile/desktop) or show a friendly fallback (web/tests) and offer a "Start 10-min timer" CTA.
- **Detection debug:** After each capture the app runs the detector service. Until a real `.tflite` file is present it replays a realistic mock JSON so you can see bounding boxes, labels, and confidences drawn on top of the photo.
- **Timer prep:** The sprint screen displays your captured zone, ADHD-friendly quick start guidance, and a focus timer that surfaces a celebratory checklist when it completes.
- **Decision log:** Capture quick notes for each keep/donate/trash/relocate/maybe action so the post-sprint summary is already drafted.

## Next build targets

- Replace the mock detection flow with the real tensor preprocessing + interpreter call.
- Add decision cards + four-box actions linked to the timer progress.
- Persist session metadata locally so returning users can view their declutter history.

## Backend (Scaffold)

To run the backend scaffold locally:

```bash
cd server
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn app.main:app --reload
```

Run backend tests:

```bash
cd server
source .venv/bin/activate
pytest
```
