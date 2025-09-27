# DECLuTTER AI

This repository now includes the first Flutter scaffolding for the ADHD-friendly decluttering assistant described in the MVP docs.
The current build lets you capture a clutter "zone" photo, preview it, and jump straight into the 10-minute sprint timer with ADHD-friendly guardrails.

## Structure

- `ADHD_Vision_Organizer_MVP_Docs_v0.1.md` — product brief, user stories, and acceptance criteria.
- `app/` — Flutter application source code for the MVP prototype.
  - `lib/src/features/capture/` — camera permissions + capture screen.
  - `lib/src/features/detect/` — detector service, debug overlays, and domain models.
  - `lib/src/features/session/` — timer flow and decision prep UI.

## Getting Started

Because the container image does not ship with Flutter, install Flutter 3.19+ locally, then run:

```bash
cd app
flutter pub get
```

This pulls down the `camera`, `permission_handler`, `image`, and `tflite_flutter` packages needed for the capture + detection debug experience.

Drop your quantized model at `app/assets/model/detector.tflite` with matching labels in `app/assets/model/labels.txt` when you are ready to swap off the mock detections. The detector service automatically resizes captured images to the tensor shape reported by the interpreter and normalizes RGB values to `0.0–1.0` for float models (or keeps `0–255` ints for quantized models), so ensure your exported model expects that preprocessing. Without the file, the app loads the bundled `debug_sample_detections.json` so you can still see the overlay and UI flow.

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
