# DECLuTTER AI — 2026 Implementation Plan

> **Audience:** AI coding agents (Claude Code, Codex, etc.) picking up work packages.
> **Status:** Active. Phase 1 (Barter/Trade Marketplace) is **COMPLETE**. See §10 for completed work.
> **Last updated:** 2026-04-27 after Tasks 1–10 (Phase 1 completion).
> **Supersedes (for stack choices):** `ADHD_Vision_Organizer_MVP_Docs_v0.1.md` §6, §7, §14.
> **Does not supersede:** the UX spec, privacy stance, or ADHD-friendly principles in the MVP doc — those still hold.

---

## 1. Goals

1. Bring the repo from a mocked MVP scaffold to a shippable on-device app.
2. Add an **item valuation feature** ("how much money can I get for the stuff in the picture") as the primary motivator for decluttering.
3. Add a **barter/trade marketplace** so users can exchange decluttered items locally without cash.
4. Use **only open-source tooling**. No provider-specific SDKs. No API keys shipped with the app. No AGPL on client-shipped code.
5. Keep the existing Flutter app. Do not rewrite the frontend.

## 2. Non-Goals

- Cloud sync, accounts, habit systems.
- Live marketplace integrations that require vendor SDKs or shipped API keys.
- Replacing Flutter. Replacing the capture/timer/decision-log code that already works.
- Any provider-specific VLM (Claude, GPT-4o, Gemini, etc.).

## 3. Target Stack (definitive)

| Layer | Choice | License | Status |
|---|---|---|---|
| Frontend | Flutter (existing) | BSD-3 | ✅ Active. `camera`, `permission_handler`, `image` retained. Trade UI complete under `lib/src/features/trade/`. |
| On-device inference runtime | `onnxruntime` Flutter plugin | MIT | 🟡 Adapter (`OnnxDetectionInterpreter`) implemented but **not wired as default**. `tflite_flutter` still active. |
| On-device VLM | **Moondream 2** (ONNX, int8) | Apache 2.0 | 📋 Planned. Blocked on WP1 completion. |
| On-device detector fallback | **RT-DETR** or **YOLO-NAS** (ONNX) | Apache 2.0 | 📋 Planned. Do NOT use Ultralytics YOLOv8/v11 — AGPL. |
| Local persistence | `shared_preferences` (timer state) + `drift` (full DB) | MIT | 🟡 `SharedPreferences` for `FocusTimer` state is live. **Drift deferred** — CI cannot run `build_runner`. Reintroduction requires committing generated `.g.dart` files. |
| Optional server mode | FastAPI + LM Studio / Ollama + Qwen | MIT / Apache 2.0 | ✅ Backend deployed on Hostinger VPS at `kyanitelabs.tech/declutter`. `DECLUTTER_ANALYSIS_PROVIDER=lmstudio` via Tailscale. |
| Valuation source | Seeded price database (6,072 items) + LLM fallback | — | ✅ Complete. Expanded from 4,018 → 6,072 items across 9 categories. |
| Trade backend | FastAPI + SQLite | — | ✅ Phase 1 complete. Credits, listings, matching, reputation, verification, safety, algorithmic loops. 170 tests. |

### Licensing rules for agents
- **Anything bundled with the app must be MIT / Apache 2.0 / BSD / public domain.** No AGPL, no GPL, no "research-only" weights.
- Moondream 2 and Qwen are both Apache 2.0 — safe.
- Do not add Ultralytics packages.

## 4. Work Packages

Each WP is independently mergeable. Order follows the dependency graph in §5.

---

### WP1 — ONNX Runtime (Complete the Migration)

**Status:** 🟡 Partially complete. `OnnxDetectionInterpreter` exists with `TensorType` enum. Not yet default.

**Goal:** Replace TFLite as the default inference runtime without breaking the mock-detection UX.

**Remaining work:**
- Wire `OnnxDetectionInterpreter` into `DetectorService` as the default backend.
- Update `DetectorService` to use async inference (`runAsync` vs sync `run`).
- Remove `tflite_flutter` from `pubspec.yaml` once ONNX is fully validated.
- Update `app/assets/model/README.md` to document the ONNX path.
- Ensure `flutter test` passes with ONNX mocks.

**Acceptance:**
- `flutter pub get && flutter test` passes.
- App launches, captures a photo, and shows mock detection overlays when no model file is present.
- No `tflite_flutter` reference anywhere in `lib/` or `test/`.

**Out of scope for this WP:** loading an actual Moondream model. That's WP2.

---

### WP2 — Moondream 2 integration

**Goal:** Real on-device item recognition via Moondream 2 (ONNX int8).

**Changes:**
- Document model acquisition in `app/assets/model/README.md`: link to the official Moondream ONNX release, int8 variant. Do not commit weights.
- `app/lib/src/features/detect/services/moondream_service.dart` (new): wraps ONNX Runtime session, handles image preprocessing (resize, normalize, tensor layout per Moondream spec), exposes:
  - `Future<List<DetectedItem>> describe(File image)` — returns `{label, category, confidence, boundingBox?}`.
- `app/lib/src/features/detect/domain/detection.dart`: extend `Detection` with `category` and optional `description` fields, or add a sibling `DescribedDetection` class. Do not break existing consumers.
- Wire `DetectorService` to prefer Moondream when a model file is present; fall back to mock JSON otherwise.

**Acceptance:**
- With the Moondream ONNX file placed in `app/assets/model/`, capturing a photo produces real labeled detections on device.
- Inference completes under ~5s on a mid-range 2023+ phone. Log the time to the debug overlay.
- No network calls during detection.

---

### WP3 — Persistence (drift / SQLite)

**Status:** 🟡 Partially complete. `FocusTimer` state persists via `SharedPreferences`. Full session/decision persistence not yet implemented.

**Goal:** Implement the data model from MVP doc §6.2 so sessions and decisions survive restarts.

**Changes:**
- `app/pubspec.yaml`: add `drift`, `drift_flutter`, `path_provider`, `path`. Dev deps: `drift_dev`, `build_runner`.
- **Critical:** Commit generated `.g.dart` files so CI does not need `build_runner`.
- `app/lib/src/data/db/` (new):
  - `app_database.dart` — drift database with tables: `sessions`, `groups`, `decisions`, `valuations` (see WP5), `rules` (seed defaults).
  - `daos/session_dao.dart`, `daos/decision_dao.dart`, `daos/valuation_dao.dart`.
- Wire `SessionTimerScreen` and the decision-log widgets to persist through the DAOs instead of in-memory state.
- Add a `HistoryScreen` (basic list of past sessions with counts). Tappable, read-only for this WP.

**Acceptance:**
- Capture → decide → kill app → relaunch → history shows the prior session.
- `flutter test` has at least one DAO round-trip test using drift's in-memory executor.

---

### WP4 — Decision Card UI + Four-Box wiring

**Goal:** Close the loop the MVP doc §3.2 describes. Today, `DecisionCategory` exists but no UI lets users apply a decision to a detected group.

**Changes:**
- `app/lib/src/features/decide/presentation/decision_card.dart` (new): card showing group label, count, thumbnail, Four-Box actions + Maybe, optional note field.
- `app/lib/src/features/session/presentation/session_timer_screen.dart`: render one `DecisionCard` per detected group; show progress `X/Y groups decided`; finish button goes to summary.
- Undo for the last decision (MVP doc §3.3). Use a simple in-session stack.

**Acceptance:**
- User can tap Keep/Donate/Trash/Relocate/Maybe on each group; progress counter updates.
- Decisions are persisted via WP3 DAOs.
- Undo restores the previous decision state and the progress counter.

---

### WP5 — Valuation feature (the motivator)

**Goal:** Show "how much money you're sitting on" for each group and a running total for the session. VLM-based, on-device by default, no third-party API.

**Design:**
- Each detected group gets a `Valuation { lowUsd, highUsd, confidence, rationale, source }`.
- `source` is one of `on_device_vlm`, `self_hosted_vlm`, `user_api`. Default: `on_device_vlm`.
- UI: every group chip shows `$15–40` next to the count. The sprint screen header shows a running `$ on the table` total (sum of low-ends). When the user taps Donate or Trash, the value drops out of the running total with a small animation — this is the dopamine hit.

**Changes:**
- `app/lib/src/features/valuation/domain/valuation.dart` (new): the data class + enum.
- `app/lib/src/features/valuation/services/valuation_service.dart` (new): abstract interface with `Future<Valuation> estimate(DetectedItem item, {File? cropImage})`.
  - `OnDeviceValuationService` implementation: prompts Moondream 2 with a system instruction like *"Return a JSON object `{low_usd, high_usd, confidence, rationale}` representing the typical fair-condition used resale range for this item on general secondhand marketplaces. Be conservative."* Parse + validate.
  - `ServerValuationService` implementation: POSTs to `${settings.serverUrl}/value` with the crop. Only active when the user has configured a server URL in settings (WP7).
- Persist every valuation (WP3 `valuations` table) keyed to `group_id`.
- Action hinting tied to estimated value (friction-matched, per earlier discussion):
  - `< $10` → suggest **Donate** (primary CTA).
  - `$10–50` → suggest **Sell locally** (generic share-sheet with pre-filled text; no platform-specific SDK).
  - `> $50` → suggest **Sell online** + add to "resale queue" (just a tagged list in history).

**Acceptance:**
- With Moondream loaded, each group shows a price range within 2s of detection.
- Values sum correctly in the header; the total decreases when items are marked Donate/Trash/Keep.
- Valuation source is always visible (small label under the price).
- If Moondream returns unparseable JSON, the UI shows `—` and logs a warning; it does not crash.

---

### WP6 — Session summary + CSV export

**Goal:** MVP doc §4.5 — deliver the end-of-sprint payoff.

**Changes:**
- `app/lib/src/features/session/presentation/session_summary_screen.dart` (new): counts per decision category, total $ decided (sold/donated separately), top suggestions taken, next-action checklist.
- CSV export using `csv` package: `sessions/session_{iso_date}.csv` via `path_provider` to app documents dir. Include group, count, decision, low_usd, high_usd, source.

**Acceptance:**
- Finishing a session shows the summary with correct numbers.
- CSV file exists on disk after export; columns match the schema above.

---

### WP7 — Optional self-hosted server mode

**Status:** ✅ Backend deployed and functional. Flutter settings UI not yet wired.

**Goal:** Let power users point the app at their own LM Studio/Ollama/vLLM instance for better valuations, without any default server.

**Changes:**
- `app/lib/src/features/settings/` (new): simple screen with one text field (`Server URL`) and a toggle (`Use server for valuation`). Store in `SharedPreferences`.
- `ServerValuationService` (created in WP5) consumes this setting.
- Ship a reference server under `server/` at repo root:
  - `server/Dockerfile` — FastAPI app.
  - `server/app/main.py` — `POST /value` endpoint that forwards to a local LM Studio running Qwen, returns the same JSON schema as on-device.
  - `server/docker-compose.yml` — FastAPI + optional Ollama together.
  - `server/README.md` — how to run on a VPS, expected VRAM (~8GB for Qwen 7B), port config.

**Acceptance:**
- With no server configured, app behaves exactly as WP5.
- With a server URL configured and reachable, valuations flip to `self_hosted_vlm` source and the label reflects it.
- Server URL is never pre-populated; no domain is baked into the app.

**Security note for agents:** do not add TLS pinning, credential prompts, or auth — this is a single-user self-hosted setup. The user takes responsibility for running it behind a VPN or Tailscale.

---

### WP8 — Tests, accessibility, polish

**Changes:**
- Widget tests for `DecisionCard`, `SessionSummaryScreen`, valuation total animation.
- Accessibility: verify all CTAs have semantics labels, touch targets ≥48dp, dynamic type respected.
- Empty states: no detections, no value estimate, model missing.
- Remove dead mock paths that are no longer reachable after WP2.

**Acceptance:**
- `flutter test` green.
- Manual test script from MVP doc §13 passes end-to-end with the new stack.

---

## 5. Dependency Order

```
WP1 (ONNX Runtime)  ─┐
                     ├─► WP2 (Moondream) ─┐
                     │                    ├─► WP5 (Valuation)
WP3 (drift)  ────────┼────────────────────┤
                     │                    ├─► WP6 (Summary)
                     └─► WP4 (Decision Card) ┘
                                              ▲
                                              │
WP7 (Server mode)  depends on WP5.
WP8 runs last.
```

Parallelizable: WP1+WP3 can run concurrently. WP7 can start once WP5's interface is defined.

## 6. File Map (quick reference)

**To delete (after WP1 completes):**
- Any `tflite_flutter` import.
- `app/assets/model/labels.txt.example` once Moondream is in (Moondream doesn't use a labels file).

**To keep untouched:**
- `app/lib/src/features/capture/` (camera + permissions work fine).
- `app/lib/src/features/session/presentation/widgets/focus_timer.dart`.
- `app/lib/src/features/session/presentation/widgets/quick_start_card.dart`.
- `app/lib/main.dart`, `app/lib/src/app.dart` — touch only to register new routes.
- `app/lib/src/features/trade/` — Phase 1 complete. Add to, but don't break existing screens.

**To add:**
- `app/lib/src/data/db/` (WP3)
- `app/lib/src/features/decide/` (WP4)
- `app/lib/src/features/valuation/` (WP5)
- `app/lib/src/features/settings/` (WP7)

## 7. Branching

- Each WP should land on its own branch off `main`, named `claude/wp{N}-{slug}`. Example: `claude/wp2-moondream`.
- Do not combine WPs into a single branch unless they share files that would conflict (e.g., WP1 and WP2 can share a branch).
- The Barter/Trade Marketplace Phase 1 used a dedicated plan file: `docs/plans/2026-04-28-barter-marketplace.md`. Future phases should use the same pattern.

## 8. Definition of Done (whole project)

- [ ] TFLite is gone. App runs inference via ONNX Runtime + Moondream 2.
- [ ] All tooling, dependencies, and shipped weights are MIT/Apache/BSD/public-domain. No AGPL, no proprietary SDKs.
- [ ] Sessions and decisions persist across restarts (drift/SQLite).
- [ ] Every detected group shows a resale value range. Session header shows running total.
- [ ] User can decide every group via the Four-Box UI and see a summary + CSV at the end.
- [ ] Optional self-hosted server mode works but nothing is pre-configured.
- [ ] Manual test script (MVP doc §13) passes.
- [ ] `flutter test` green.

## 9. Definition of Done — Phase 1 (Barter/Trade) ✅

- [x] Trade credit ledger (earn/spend/balance/history) with SQLite persistence.
- [x] Trade listings with geolocation, condition, and valuation-backed credit pricing.
- [x] Nearby discovery with Haversine distance filtering.
- [x] Full trade lifecycle: propose → accept/decline → credit transfer → completion.
- [x] ND-friendly UX: message templates, condition checklists, explicit trade rules.
- [x] Reputation + review system (avg rating, trade count, tags).
- [x] Safety checklists for 10 categories.
- [x] Verified trader badges (email/phone/id).
- [x] Algorithmic multi-party trade loop detection (DFS cycles, 2–4 participants).
- [x] Expanded valuation engine: 6,072 seeded items across 9 categories.
- [x] Flutter trade UI: browse, create listing, matches, wallet, hub screen.
- [x] All trade endpoints tested: 49 trade-specific tests passing.
- [x] Total backend test count: 170 passing, 0 failures.

## 10. Rules for Agents Picking This Up

1. **Read the WP in full before touching files.** Acceptance criteria are the contract.
2. **Do not expand scope.** If you see adjacent code that looks wrong, note it and move on unless it blocks the WP.
3. **Do not add provider-specific code.** If a dependency's license isn't MIT / Apache / BSD / public domain, stop and ask.
4. **Do not commit model weights.** Document how to obtain them in `app/assets/model/README.md`.
5. **Do not introduce mock-only code paths that aren't gated behind "model file missing."** The mock JSON fallback exists for one reason: developer ergonomics without weights on disk.
6. **Write the minimum tests needed for the acceptance criteria.** No snapshot tests, no exhaustive fuzz suites.
7. **Keep the ADHD-friendly UX principles:** large buttons, minimal text, one-glance reads, haptic feedback on decisions. Do not add settings pages for things that aren't in WP7.
8. **Trade UI additions must not break existing declutter flow.** The app has two modes now; keep them independent.

---

**WP1 is the blocker for everything else. Complete the ONNX wiring first.**
**Phase 1 (Trade) is DONE. See [docs/plans/2026-04-28-barter-marketplace.md](docs/plans/2026-04-28-barter-marketplace.md) for Phase 2 plans.**
