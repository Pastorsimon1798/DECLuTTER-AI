# Remaining Issues — Sorted by ROI & Leverage

> Generated from comprehensive codebase audit (83 findings: 43 Flutter + 40 backend).
> **Last updated:** 2026-04-24 after PR #33 (Tier 0/1/2 security, reliability, and architectural fixes).
> Sorted by: (user impact × stability impact × security risk) / effort, then by architectural leverage.

---

## ✅ Fixed in PR #33 (2026-04-24)

### Tier 0 — Security Critical

| # | Issue | Files | PR #33 Fix |
|---|---|---|---|
| 0.1 | Reflected XSS via `Host` header in `launch.py` | `launch.py` | `html.escape()` on canonical URL replacement; strengthened `_sanitize_host` |
| 0.2 | Basic Auth username not validated | `operator.py` | Username comparison added against expected operator env var |
| 0.3 | Sensitive error disclosure leaks Firebase internals | `dependencies.py` | Generic error messages returned; real errors logged server-side |
| 0.4 | CORS credentials + wildcard origin risk | `main.py`, `settings.py` | Reject `*` in origins when credentials enabled |
| 0.5 | LLM prompt injection via `image_storage_key` | `analysis_adapter.py` | Validation + sanitization before prompt interpolation |
| 0.6 | Event-loop blocking in async endpoints | `analysis.py`, `operator.py`, `seller.py` | `asyncio.to_thread()` wrappers for sync I/O |

### Tier 1 — High ROI

| # | Issue | Files | PR #33 Fix |
|---|---|---|---|
| 1.1 | `list_sessions` N+1 query bomb | `session_store.py` | Single JOIN query replacing looped lookups |
| 1.3 | CSV injection in eBay export | `marketplace_ebay_service.py` | Formula-triggering characters sanitized |
| 1.7 | Path traversal via symlinks in uploads | `analysis_adapter.py` | `realpath()` resolution + boundary validation |
| 1.8 | Unbounded memory for base64 encoding | `analysis_adapter.py` | 10MB file size caps enforced |
| 1.9 | `setState() after dispose()` in 4 async methods | `session_timer_screen.dart` | `mounted` guards added |
| 1.10 | `setState() after dispose()` in `CaptureScreen` | `capture_screen.dart` | `mounted` guards added |
| 1.11 | `FocusTimer` `setState()` after dispose on resume | `focus_timer.dart` | `mounted` guards added |
| 1.12 | `Timer.periodic` executes after `dispose()` + drift | `focus_timer.dart` | Timer lifecycle cleanup + `_timerTarget` drift fix |
| 1.13 | `FocusTimer` loses state on process death | `focus_timer.dart` | `SharedPreferences` persistence for `_remaining`, `_isRunning` |
| 1.15 | `CashToClearApiClient` no response size limit | `cash_to_clear_api.dart` | 10MB response/image caps enforced |
| 1.16 | Decision spam bug (same group, infinite decisions) | `session_timer_screen.dart` | Decision deduplication per group |
| 1.18 | Camera disposed on system dialogs (`inactive` vs `paused`) | `capture_screen.dart` | `_cameraInitFuture` + `_disposed` lifecycle cleanup |
| 1.19 | `Image.file` re-decodes JPEG on every `setState` | `capture_screen.dart` | `Image.memory` byte caching |

### Tier 2 — Architectural

| # | Issue | Files | PR #33 Fix |
|---|---|---|---|
| 2.1 | SQLite persistence (sessions survive restarts) | `focus_timer.dart` | `SharedPreferences` for timer state; **Drift deferred** (CI build_runner issue) |
| 2.4 | ONNX Runtime abstraction | `detect/services/` | `OnnxDetectionInterpreter` adapter added; `TensorType` enum extracted; **not yet wired as default** |
| — | SQLite WAL mode | `session_store.py` | `PRAGMA journal_mode=WAL` added |

---

## 🔴 TIER 0 — Security Critical (Still Open)

> None remaining after PR #33.

---

## 🔴 TIER 1 — High ROI, Low Effort (Still Open)

> These were identified in the original audit but not addressed in PR #33.

### 1.2 Backend: Public Listing Ownership Bypass
- **File:** `server/app/services/session_store.py:272-306`
- **Issue:** `get_public_listing()` and `list_recent_public_listings()` do NOT filter by `owner_uid`. Any authenticated user can read any listing.
- **Fix:** Add `owner_uid` parameter/validation to both methods.
- **Effort:** XS (~20 min)

### 1.4 Backend: Firebase Admin Init Race Condition
- **File:** `server/app/security/firebase.py:103-107, 126-130`
- **Issue:** `if not firebase_admin._apps:` is not atomic; concurrent requests can race to `initialize_app()`, causing one to raise `ValueError` → 503 error.
- **Fix:** Use a module-level `threading.Lock()` around the initialization check.
- **Effort:** XS (~15 min)

### 1.5 Backend: `list_sessions` Auth Crash = 500 Instead of 401
- **File:** `server/app/api/routes/sessions.py:32-33`
- **Issue:** `list_sessions` calls `_owner_uid(request)` which raises `HTTPException(401)`, but the route has no auth dependencies. FastAPI turns the uncaught exception into a 500.
- **Fix:** Either add `dependencies=[Depends(require_firebase_protection)]` to the router, or handle the missing claims gracefully.
- **Effort:** XS (~10 min)

### 1.6 Backend: `valuation.py` Module-Level Service (Not Thread-Safe)
- **File:** `server/app/api/routes/valuation.py:8`
- **Issue:** `valuation_service = MockCompsValuationService()` at module scope. Concurrent requests mutate shared state (if any future implementation is stateful).
- **Fix:** Move to `@lru_cache` factory + `Depends()`, matching pattern in `sessions.py`.
- **Effort:** XS (~10 min)

### 1.14 Frontend: `CashToClearApiClient` Has No Request Timeout
- **File:** `app/lib/src/features/session/services/cash_to_clear_api.dart:122-148`
- **Issue:** `connectionTimeout` and `idleTimeout` are set on `HttpClient`, but `openUrl` + `close()` has no per-request timeout. A hung backend blocks the UI thread indefinitely.
- **Fix:** Wrap `_requestJson` in `Future.timeout(const Duration(seconds: 15))`.
- **Effort:** XS (~10 min)

### 1.17 Frontend: `CaptureScreen` Silently Swallows Analysis Errors
- **File:** `app/lib/src/features/capture/presentation/capture_screen.dart:167-168`
- **Issue:** `unawaited(_analyzeCapture(capture))` — if detection throws, the error is logged and lost. User sees "Photo saved" but analysis silently failed.
- **Fix:** Wrap in try/catch and show SnackBar on failure, or await and show inline error.
- **Effort:** XS (~15 min)

### 1.20 Frontend: Timer Doesn't Pause/Reset on Completion
- **File:** `app/lib/src/features/session/presentation/session_timer_screen.dart:331-338`
- **Issue:** `_handleTimerCompleted` shows a bottom sheet but does **not** pause or reset the timer. If the user dismisses the sheet, the timer remains at 00:00 and the sprint can continue indefinitely.
- **Fix:** Call timer reset/pause before showing the sheet.
- **Effort:** XS (~10 min)

---

## 🟠 TIER 2 — High Leverage (Architectural, Unlocks Future Work)

### 2.1 WP3: Drift/SQLite Persistence (Sessions & Decisions Survive Restarts)
- **Status:** Partially addressed. `FocusTimer` now persists via `SharedPreferences`. Full session/decision persistence still requires `drift`.
- **Files:** New `app/lib/src/data/db/`, refactor `session_timer_screen.dart`
- **Issue:** All session data is in-memory. Kill app = total data loss. MVP spec §6.2 requires SQLite.
- **Impact:** Core MVP requirement. Blocks history, summary, and CSV export.
- **Leverage:** Unlocks WP4 (Decision Card), WP6 (Summary + CSV), and WP8 (History screen).
- **Effort:** M (1-2 days)
- **Note:** Drift was added then removed in PR #33 because CI cannot run `build_runner`. Reintroduction requires committing generated `.g.dart` files.

### 2.2 Extract State Management from `SessionTimerScreen`
- **File:** `app/lib/src/features/session/presentation/session_timer_screen.dart` (1,137 lines)
- **Issue:** UI widget contains API client logic, decision state, remote sync, pending queue, and public listing creation. Untestable, unmaintainable.
- **Impact:** Every new feature adds to a god-widget. Bugs hide in the noise.
- **Leverage:** Enables unit testing, WP3 DAO wiring, and WP4 Decision Card without 1,000-line diffs.
- **Effort:** M (1 day)

### 2.3 Backend: Add Rate Limiting + Request Size Limits
- **Files:** `server/app/main.py`, new middleware
- **Issue:** No rate limiting on any endpoint. `/analysis/intake` accepts unlimited file sizes. Public deployment = trivial DoS.
- **Impact:** Security baseline for any production deployment.
- **Leverage:** Unblocks WP7 (public server mode) and any cloud deployment.
- **Effort:** S (~2-3 hours)

### 2.4 WP1: ONNX Runtime Abstraction (Replace TFLite)
- **Status:** Partially addressed. `OnnxDetectionInterpreter` adapter exists with `TensorType` enum. Not yet wired as default.
- **Files:** `app/lib/src/features/detect/services/`, `pubspec.yaml`
- **Issue:** `tflite_flutter` is AGPL-adjacent (Ultralytics YOLO ecosystem), crashes on web, and blocks iOS Simulator. Implementation plan mandates ONNX.
- **Impact:** Legal compliance, web compatibility, real model loading.
- **Leverage:** Unblocks WP2 (Moondream), enables real on-device inference, removes web crash.
- **Effort:** L (2-3 days)

### 2.5 Backend: Standardize Error Handling + Request Logging Middleware
- **Files:** `server/app/main.py`, `server/app/api/`
- **Issue:** No structured request logging. Errors vary between `KeyError` → 404, `RuntimeError` → 500/503, and unhandled exceptions → 500. No correlation IDs.
- **Impact:** Debugging production issues is guesswork.
- **Leverage:** Makes all future backend work faster and safer.
- **Effort:** S (~1/2 day)

---

## 🟡 TIER 3 — Medium Impact / Medium Effort (Backlog)

### 3.1 WP4: Decision Card UI (Four-Box Wiring)
- **Issue:** MVP spec §3.2 describes a full Decision Card with suggestion, rationale, and Explain toggle. Current UI is just chips + buttons.
- **Impact:** Core MVP UX gap.
- **Effort:** M (1-2 days)

### 3.2 WP5: Valuation Feature (The Motivator)
- **Issue:** No price estimates shown per group. Implementation plan calls for on-device VLM valuation.
- **Impact:** Primary differentiator per product strategy.
- **Effort:** L (3-5 days, depends on WP2)

### 3.3 WP6: Session Summary Screen + CSV Export
- **Issue:** `_TimerCompleteSheet` is a stub. No end-of-session payoff, no CSV.
- **Impact:** MVP acceptance criterion: "CSV is saved locally."
- **Effort:** M (1-2 days, depends on WP3)

### 3.4 Frontend: Web Compatibility (`dart:io` + `tflite_flutter` Guards)
- **Files:** `detector_service.dart`, `cash_to_clear_api.dart`
- **Issue:** `dart:io Platform`, `File`, `HttpClient`, and `tflite_flutter` imports will crash on web builds.
- **Impact:** Cannot compile for web/PWA.
- **Effort:** S (~1/2 day) — mostly `kIsWeb` branches and conditional imports.
- **Note:** Partially addressed in PR #33 with conditional imports and mock fallbacks.

### 3.5 Backend: Test Coverage Gaps
- **Files:** `server/tests/`
- **Issue:** No tests for XSS, CSV injection, path traversal, prompt injection, Basic Auth bypass, CORS misconfiguration, `analysis_adapter.py`, `valuation_service.py`.
- **Impact:** Regressions in security, inference, pricing, and listing logic go undetected.
- **Effort:** M (1 day)

### 3.6 Frontend: Accessibility Pass
- **Files:** All `presentation/` widgets
- **Issue:** No semantic labels on decision buttons. Touch targets not verified ≥48dp. No haptic feedback on decisions (MVP §3.3).
- **Impact:** App Store rejection risk, exclusion of motor-impaired users.
- **Effort:** S (~1/2 day)

### 3.8 Backend: Signed-Upload Session is Non-Functional
- **File:** `server/app/api/routes/analysis.py:46-49, 52-58`
- **Issue:** `create_intake_session` returns a signed upload stub, but `intake_image` ignores the session token entirely and writes to a fresh UUID path.
- **Fix:** Either wire the session token through intake validation, or remove the stub endpoint.
- **Effort:** M (1/2 day)

### 3.9 Frontend: `CaptureScreen` Photo File Race Condition
- **File:** `capture_screen.dart:296-299`
- **Issue:** `Image.file(File(capture.path))` assumes the file exists. If the OS cleans temp files, this crashes.
- **Fix:** Copy to app documents directory before passing to `SessionTimerScreen`.
- **Effort:** S (~1 hour)

### 3.10 Backend: `analysis_adapter.py` Payload Retry Loses Original Errors
- **File:** `server/app/services/analysis_adapter.py:114-130`
- **Issue:** `run()` tries 3 payloads. If payload 1 fails with a useful error and payload 3 fails with a generic one, only the generic error is raised.
- **Fix:** Collect all errors and raise a compound exception.
- **Effort:** XS (~20 min)

---

## 🔵 TIER 4 — Large Features / Strategic (Planned WPs)

### 4.1 WP2: Moondream 2 On-Device Integration
- **Impact:** Real item recognition instead of mock JSON.
- **Effort:** L (3-5 days, depends on WP1)

### 4.2 WP7: Self-Hosted Server Mode (Settings + Ollama Reference)
- **Impact:** Power-user feature, privacy-first server option.
- **Effort:** M (2-3 days, depends on WP5 interface)

### 4.3 WP8: Full Test Suite, Polish, Empty States
- **Impact:** Ship-quality bar.
- **Effort:** M (2-3 days)

### 4.4 Multi-Photo Sessions & Zone Memory
- **Impact:** Post-MVP feature per spec §14.
- **Effort:** L (1-2 weeks)

---

## Summary: What to Do Next

1. **Today (1 hour):** Knock out remaining Tier 1 items (1.2, 1.4, 1.5, 1.6, 1.14, 1.17, 1.20) — all XS effort.
2. **This Week:** WP3 (Drift persistence) — it unlocks history, summary, and CSV.
3. **Next Sprint:** WP1 (ONNX full wiring) — unblocks real inference and web builds.
4. **Then:** WP2 → WP4 → WP5 → WP6 in dependency order.

The full dependency graph:
```
Tier 1 fixes (parallel) ───────────────────────────────┐
WP1 (ONNX full wiring) ─┐                              │
                        ├─► WP2 (Moondream) ─┐        ├──► WP8 (Polish)
WP3 (Drift) ────────────┤                  ├─► WP5 (Valuation) ─┤
                        └─► WP4 (Decision) ─┘        │
                                                     ├──► WP6 (Summary + CSV)
WP7 (Server) depends on WP5 ─────────────────────────┘
```
