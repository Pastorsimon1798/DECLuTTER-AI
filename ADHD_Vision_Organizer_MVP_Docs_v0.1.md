# ADHD Vision Organizer — MVP Documentation (v0.1)

> **Audience:** Solo builder (beginner) using AI coding assistants (Codex CLI/Web, Claude Code).  
> **Goal:** Ship a private, on‑device-first MVP that turns a photo of clutter into simple keep/donate/trash/relocate actions with a time‑boxed flow.

---

## Quick Research & Documentation Checklist (3–7 bullets)

- Validate scope: confirm MVP focuses on **single‑zone photo → grouped items → Four‑Box decision + timer**.
- Choose stack: **Flutter + TFLite** (on‑device) with optional **cloud “Explain”** toggle. Confirm device targets (iOS/Android).
- Select/prepare a **lightweight object‑detection model** (e.g., YOLOv8‑n/‑nano quantized) and labels list.
- Define **data model** (Items, Groups, Sessions, Decisions) and **local storage** (SQLite).  
- Draft **ADHD‑friendly UX** (low friction: one photo, one timer, chips, Four‑Box).
- Write **acceptance tests** and **manual test script** for a single messy‑desk scenario.
- Decide **privacy defaults** (on‑device by default; opt‑in cloud; telemetry off).

---

## 1) Product Requirements (PRD)

### 1.1 Problem
Adults with ADHD often feel overwhelmed by clutter. Generic vision tools identify objects but don’t make decisions easy. This app converts a cluttered photo into a tiny set of next steps with timeboxing.

### 1.2 Objectives (MVP)
- **Identify & group** items in a single photo (desk/shelf/dresser).
- **Guide decisions** with **Four‑Box** choices: **Keep / Donate‑Sell / Trash / Relocate / Maybe**.
- **Timebox** with a large, friendly **10‑minute** sprint timer.
- **Log decisions locally** (SQLite) and show a **short session summary** (counts + next actions).
- **Privacy‑first:** all processing on‑device by default; optional **Explain** via cloud (off by default).

### 1.3 Non‑Goals (MVP)
- Multi‑room mapping; continuous video; advanced inventory; cloud sync; donation logistics; price estimates; habit systems beyond daily reset reminder.

### 1.4 Success Metrics (qualitative for MVP)
- Can a new user complete a **single-zone** declutter flow in < **5 minutes** from install?  
- Do they complete at least **one decision** for **>60%** of detected groups?  
- Do they understand what left the device (privacy notice comprehension)?

---

## 2) User Stories (MVP)

- As a **distracted user**, I take one photo of my messy desk and see labeled groups (cables, papers, cups) with a **Start 10‑min** button so I can finish a small sprint.
- As a **values‑driven user**, I set simple rules (e.g., “duplicates >2 → donate”) so the app suggests **Keep/Donate/Trash/Relocate/Maybe** with a **2‑sentence** rationale.
- As a **privacy‑conscious user**, I keep everything on my device and can optionally enable **Explain** (cloud) per photo with a clear indicator and audit line in the session summary.

**Acceptance (MVP):** Each story is completable without crashes; decisions are stored locally; privacy indicator works.

---

## 3) UX Spec (Beginner‑Friendly)

### 3.1 First‑Run
- Splash → permissions (camera/storage) with plain‑language privacy note: “Analysis happens on your device. You can enable cloud **Explain** later.”  
- Landing: **Quick Declutter** card: “Pick a zone → Take photo → Decide with Four‑Box → Done.”

### 3.2 Core Flow (Single Zone)
1. **Zone Selector** (Desk, Dresser, Shelf) + **Start 10‑min** (big button).  
2. **Camera Capture** → run **on‑device** detection.  
3. **Groups Chips** appear: e.g., `Cables (5) • Papers (12) • Dishes (2)`.  
4. Tap a group → **Decision Card** with:  
   - **Suggestion** (e.g., “You have 5 cables; consider keeping 2, donate 3.”)  
   - **Actions:** **Keep** / **Donate‑Sell** / **Trash** / **Relocate** / **Maybe**  
   - **Why?** small text (2 sentences).  
   - **[Explain]** toggle (cloud, off by default).  
5. Bottom bar: **Timer**, **Progress (e.g., 2/4 groups decided)**, **Finish**.

### 3.3 Accessibility & ADHD Aids
- Large buttons, minimal text, progress chips, haptic feedback on decisions, optional voice hints.  
- Shortcuts: **“Decide all duplicates”**, **“Show only trash‑likely”**.  
- **Undo** for last action; **Maybe bin** with scheduled reminder.

### 3.4 Wireframe (ASCII)
```
[ Zone: Desk ]            [ 10:00 ] [ Start ]
[  Camera View  ]
[  —— Photo ——  ]  (On-device analysis ✓ Private)
Chips: [Cables(5)] [Papers(12)] [Dishes(2)]

[Decision Card: Cables]
Suggestion: Keep 2, Donate 3 (duplicates)
Why: Reduces clutter; easy to replace.
[Keep] [Donate‑Sell] [Trash] [Relocate] [Maybe]  [Explain ☐]

[Progress 2/4]                     [Finish]
```

---

## 4) Functional Requirements

### 4.1 Capture & Detection
- Capture a single photo (JPEG) at reasonable resolution (e.g., 1280–1920 px on the long edge).  
- Run **on‑device object detection** using a **quantized lightweight model** (YOLOv8‑n/‑nano).  
- Post‑process detections: merge overlaps; map labels to **categories** (Cables → Electronics).

### 4.2 Grouping & Rules
- Group by **category**; count items; detect **duplicates** (by class + visual similarity threshold).  
- **Rules Engine (local JSON):** simple predicates and actions, e.g.:
```json
{
  "name": "limit_cables",
  "when": {"category": "cable", "count_gt": 2},
  "then": {"suggest": "donate", "keep_count": 2}
}
```
- Provide a **default rule set**; allow user to toggle rules on/off.

### 4.3 Decisions & Logging
- For each group: store `{session_id, group_id, decision, rationale, count, timestamp}` in SQLite.  
- **Maybe** items get a reminder time (default +24h) stored locally.

### 4.4 Explain (Optional Cloud)
- When user taps **Explain**, send a **cropped group image + anonymized context** to the LLM endpoint.  
- Display 1–2 sentence explanation and a single alternative action.  
- **Do not** upload full original photo; redact text if present (basic OCR‑based mask optional v2).

### 4.5 Session Summary
- After **Finish**: show counts per decision, top suggestion taken, and a **short checklist** (e.g., “Place donate items in bag; set drop‑off reminder”).  
- Export CSV to device storage: `session_{date}.csv`.

---

## 5) Non‑Functional Requirements

- **Privacy:** On‑device by default; explicit per‑group **Explain** toggle for cloud. No third‑party analytics in MVP.  
- **Performance:** Analysis < 3s on mid‑range phones (optimize model size).  
- **Reliability:** Offline‑first; no hard dependency on network.  
- **Accessibility:** Large touch targets (>=48dp), readable fonts, VoiceOver/TalkBack labels.  
- **Maintainability:** Modular pipeline (capture → detect → group → decide → log).

---

## 6) Architecture

### 6.1 High‑Level
- **Flutter** UI (Dart)  
- **TFLite** runtime (platform plugins) → loads **quantized detector**  
- **Detector → Grouper → Rules Engine → Decision UI**  
- **SQLite** for local storage (e.g., `drift` on Flutter)  
- Optional **Cloud Explain** service wrapper (toggle)

### 6.2 Data Model (SQLite)
```
tables:
  sessions(id PK, zone, started_at, finished_at, device_info, explain_used BOOL)
  groups(id PK, session_id FK, category, label, count, representative_uri)
  decisions(id PK, session_id FK, group_id FK, decision ENUM, rationale TEXT, created_at)
  rules(id PK, name, json TEXT, enabled BOOL) -- seed defaults
```

### 6.3 Labels & Categories (starter set)
- cables, chargers, phone, laptop, keyboard, mouse, mug/cup, bottle, paper/document, book, pen, stapler, trash/packaging, plate/bowl, clothing/accessory.

---

## 7) Tech Stack & Tools

- **Flutter** (UI), **Dart**  
- **tflite_flutter** (on‑device inference) + a **quantized YOLOv8‑n** model file (`.tflite`)  
- **drift** (SQLite ORM)  
- **image_picker** / **camera** (capture)  
- **csv** package for export  
- Optional: **http** for Explain endpoint wrapper

**Why Flutter?** Consistent UI on iOS/Android, fast MVP for a solo dev, good TFLite support.

---

## 8) Setup & “First Build” Steps (copy‑paste friendly)

> If brand‑new to Flutter, do this once.

1) **Install Flutter**: https://docs.flutter.dev/get-started/install  
2) **Create app**
```bash
flutter create adhd_vision_organizer
cd adhd_vision_organizer
```
3) **Add packages**
```bash
flutter pub add tflite_flutter tflite_flutter_helper drift path_provider path csv camera image_picker http
flutter pub add --dev drift_dev build_runner
```
4) **Add model file**
- Place your quantized model at: `assets/models/detector.tflite` and label map at `assets/labels.txt`.
- Update `pubspec.yaml`:
```yaml
flutter:
  assets:
    - assets/models/detector.tflite
    - assets/labels.txt
```
5) **iOS/Android permissions**
- Camera/storage permissions per platform guides (Info.plist / AndroidManifest).

6) **Run**
```bash
flutter run
```

> Tip: Use Codex/Claude Code to scaffold the detector service, SQLite schema (drift), and UI screens from the specs above.

---

## 9) MVP Backlog (Ordered)

1. Project scaffold (Flutter), camera capture screen, permissions.  
2. Load TFLite model; run inference on captured image; overlay boxes (debug mode).  
3. Post‑process to **Groups** + **Categories**; compute duplicate counts.  
4. Rules engine (local JSON) with default rules; wire to suggestion text.  
5. **Decision Card** UI + **Four‑Box** actions + **Timer**.  
6. SQLite persistence (sessions, groups, decisions).  
7. Session summary + CSV export.  
8. **Explain** toggle (stub); add real call later behind a feature flag.  
9. Accessibility pass (labels, sizes) + error handling.  
10. Polish (animations, empty states, edge cases).

---

## 10) Acceptance Criteria (MVP)

- Taking a photo produces >= **3** sensible groups on a common desk scene.  
- Each group can be assigned one of the four decisions; the timer counts down; progress updates.  
- Session summary appears with correct counts; a CSV is saved locally.  
- App functions with **airplane mode** (except Explain).  
- **Privacy indicator** clearly states on‑device analysis; cloud only when Explain is toggled.

---

## 11) Error Handling & Edge Cases

- **No objects detected:** Show friendly retry + tip (“Try closer, better light”).  
- **Low memory / model load fail:** Fallback to lower‑res analysis; show “Try smaller photo.”  
- **Timer interrupted/app backgrounded:** Persist remaining time; resume on return.  
- **Explain offline:** Queue or disable; show “Explain requires internet; try again.”  
- **Storage full:** Allow skip export; prompt to free space.  
- **Undo last decision:** Always available; show toast.  

---

## 12) Privacy & Security

- Default **on‑device**; **Explain** is **explicit opt‑in per group**.  
- Minimal data collected; no account required.  
- If cloud is enabled later: send **cropped group area**, no EXIF, no user identifiers; use HTTPS; display a “What left device” line item in Session Summary.

---

## 13) Manual Test Script (10 minutes)

1. Fresh install → grant camera perm.  
2. Tap Start → capture desk photo.  
3. Verify groups show (>=3).  
4. Decide one group with **Donate‑Sell**; one with **Trash**; one **Keep**; one **Maybe**.  
5. Toggle **Explain** on one group; confirm indicator and rationale show.  
6. Let timer reach 0: verify summary and CSV export.  
7. Kill app; relaunch; open history to confirm session logged.

---

## 14) Future (Post‑MVP) Ideas

- Multi‑photo sessions; zone memory; smart reminders; donation partners; resale estimates; local‑model fine‑tuning; on‑device OCR to redact sensitive text before Explain; voice‑driven flow.

---

## 15) Repo Structure (suggested)

```
/lib
  /features/capture
  /features/detect
  /features/group
  /features/decide
  /features/session
  /data (drift db, models)
  /services (rules, explain)
/assets/models/detector.tflite
/assets/labels.txt
/test (widget/unit tests)
```

---

## 16) Prompts You Can Reuse with AI Coding Assistants

**“Detector service”**
> “Generate a Flutter service using tflite_flutter that loads `assets/models/detector.tflite`, runs inference on a `CameraImage` converted to RGB, returns a list of detections with bounding boxes, labels from `assets/labels.txt`, and confidences. Add simple NMS and a method to crop group thumbnails.”

**“Rules engine”**
> “Implement a local JSON rules engine with predicates: category, count_gt, count_lt, duplicate_gt; actions: suggest (keep/donate/trash/relocate), keep_count. Provide a function `applyRules(group)` that returns a suggestion string and optional keep_count.”

**“SQLite schema (drift)”**
> “Create drift tables for sessions, groups, decisions as per the data model; write DAOs to insert a session, upsert groups, and record decisions; add a query to fetch a session summary.”

**“UI flow”**
> “Build three Flutter screens: CaptureScreen → ReviewScreen (chips + timer) → DecisionScreen (card). Use large buttons, minimal text, and an always‑visible progress indicator.”

---

## 17) Lightweight Cost Plan (MVP)

- Flutter + TFLite: $0.  
- Model training: start with open weights/converted TFLite.  
- Cloud Explain (optional): budget $10–$50 for initial tests; keep off by default.

---

**You’re ready to build.** Start with the backlog item #1 and use the prompts to have AI scaffolding the code quickly. Keep sessions short and test on a real messy desk photo early.
