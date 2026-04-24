# Remaining Issues — Sorted by ROI & Leverage

> Generated from comprehensive codebase audit (83 findings: 43 Flutter + 40 backend).
> Sorted by: (user impact × stability impact × security risk) / effort, then by architectural leverage.

---

## ✅ Already Fixed (This Session)

| # | Issue | Files |
|---|---|---|
| 1 | SyntaxError in `_sanitize_host` blocked all backend tests | `launch.py`, `operator.py`, `public_listings.py` |
| 2 | Fenced-JSON regex permanently failing on markdown code blocks | `analysis_adapter.py` |
| 3 | SQLite connection leaks (no commit/close in raw `_connect()`) | `session_store.py` |
| 4 | Missing database indexes causing full table scans | `session_store.py` |
| 5 | Import-time filesystem crash from module-level upload adapter | `analysis.py` |
| 6 | Camera controller disposed inside `setState()` race condition | `capture_screen.dart` |
| 7 | Native TFLite interpreter leak (no `close()` chain) | `detection_interpreter.dart`, `detector_service.dart`, `capture_screen.dart` |
| 8 | Decision queue re-queued entire batch on single failure | `session_timer_screen.dart` |
| 9 | Null-dict crash on `decision_counts` schema default | `session.py` schema |
| 10 | Seller routes had no opt-in auth protection | `main.py` |
| 11 | Dead `return host` code from failed patch injection | `operator.py`, `public_listings.py` |

---

## 🔴 TIER 0 — Security Critical (Fix Today)

> Exploitable now. Every item is ≤30 minutes.

### 0.1 Reflected XSS via `Host` header in `launch.py`
- **File:** `server/app/api/routes/launch.py:139-142, 180-183`
- **Issue:** `_sanitize_host` blocks `<"'\n\r\t` but **not `>` or `&`**. The canonical URL is inserted into HTML via `.replace('__CANONICAL_URL__', url)` **without `html.escape()`**. `Host: evil.com><script>alert(1)</script>` breaks out of the `<link>` tag.
- **Fix:** Add `html.escape(canonical_url)` in the template replacement; strengthen `_sanitize_host` to block `&`, `>`, spaces, backticks.
- **Effort:** XS (~15 min)

### 0.2 Basic Auth Username Not Validated (Any Username Works)
- **File:** `server/app/api/routes/operator.py:102-105`
- **Issue:** `secrets.compare_digest()` only checks `credentials.password`. Any username is accepted if the password matches `DECLUTTER_OPERATOR_PASSWORD`.
- **Fix:** Add username comparison against an expected operator username env var.
- **Effort:** XS (~10 min)

### 0.3 Sensitive Error Disclosure Leaks Firebase Internals
- **File:** `server/app/security/dependencies.py:43-51`
- **Issue:** `str(exc)` is returned directly in 401/503 detail fields, leaking internal Firebase SDK errors, token validation messages, and stack info.
- **Fix:** Return generic messages ("Authentication failed.", "Service unavailable.") and log the real error server-side.
- **Effort:** XS (~10 min)

### 0.4 CORS Credentials + Wildcard Origin Risk
- **File:** `server/app/main.py:28-34`, `server/app/core/settings.py:177-179`
- **Issue:** `allow_credentials=True` is paired with `allow_origins` read blindly from env. If `DECLUTTER_CORS_ALLOW_ORIGINS=*`, browsers will send credentials to any origin.
- **Fix:** Reject `*` in origins when credentials are enabled; validate origin format.
- **Effort:** XS (~15 min)

### 0.5 LLM Prompt Injection via `image_storage_key`
- **File:** `server/app/services/analysis_adapter.py:145-152, 163-165, 175-178`
- **Issue:** `image_storage_key` has no validation and is interpolated verbatim into the OpenAI-compatible user prompt. An attacker can inject instruction overrides.
- **Fix:** Validate `image_storage_key` against `^[a-zA-Z0-9_.-]+$` before interpolation; or `html.escape()` / sanitize before inserting into prompts.
- **Effort:** XS (~15 min)

### 0.6 Event-Loop Blocking in Async Endpoints
- **Files:** `server/app/api/routes/analysis.py:52-58`, `operator.py:128-213`, `seller.py:46-78`
- **Issue:** `async def` endpoints call sync PIL (`_strip_metadata`), SQLite, and `urllib.request` directly in the event loop, blocking ALL concurrent requests.
- **Fix:** Wrap sync I/O in `asyncio.to_thread()` or `run_in_threadpool()`.
- **Effort:** S (~1-2 hours)

---

## 🔴 TIER 1 — High ROI, Low Effort (This Week)

> Each item here is ≤1 hour and fixes a crash, security hole, data leak, or major UX papercut.

### 1.1 Backend: `list_sessions` N+1 Query Bomb
- **File:** `server/app/services/session_store.py:145-172`
- **Issue:** `list_sessions()` calls `get_session_summary()` in a loop — for *N* sessions that's *N+1* DB round-trips.
- **Fix:** Single JOIN query returning sessions + aggregated counts.
- **Effort:** XS (~15 min)

### 1.2 Backend: Public Listing Ownership Bypass
- **File:** `server/app/services/session_store.py:272-306`
- **Issue:** `get_public_listing()` and `list_recent_public_listings()` do NOT filter by `owner_uid`. Any authenticated user can read any listing.
- **Fix:** Add `owner_uid` parameter/validation to both methods.
- **Effort:** XS (~20 min)

### 1.3 Backend: CSV Injection in eBay Export
- **File:** `server/app/services/marketplace_ebay_service.py:20-23`
- **Issue:** `export_csv()` only escapes double quotes. A title like `=CMD|'!A1` becomes an executable formula in Excel. Newlines are also unescaped.
- **Fix:** Prefix risky cells with `'` or sanitize formula-triggering characters (`=`, `+`, `-`, `@`, `\t`, `\n`).
- **Effort:** XS (~15 min)

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

### 1.7 Backend: Path Traversal via Symlinks in Uploads
- **File:** `server/app/services/analysis_adapter.py:215-227`
- **Issue:** `candidate.relative_to(self.upload_dir.resolve())` blocks `..` traversal but NOT symlink escapes. A symlink inside `upload_dir` pointing to `/etc/passwd` would be served.
- **Fix:** Use `os.path.realpath()` and verify the resolved path is still under `upload_dir`.
- **Effort:** XS (~15 min)

### 1.8 Backend: Unbounded Memory for Base64 Encoding
- **File:** `server/app/services/analysis_adapter.py:226`
- **Issue:** `_image_data_url()` calls `candidate.read_bytes()`, loading the entire image into RAM. No size cap.
- **Fix:** Reject files > 5MB before reading; stream large files instead.
- **Effort:** XS (~15 min)

### 1.9 Frontend: `setState() after dispose()` in 4 Async Methods
- **File:** `app/lib/src/features/session/presentation/session_timer_screen.dart:74-77, 193-196, 226-229, 301-305`
- **Issue:** `_bootstrapCashToClearSession`, `_recordRemoteDecision`, `_flushPendingRemoteDecisions`, `_createPublicListingPage` all call `setState()` **before** the first `await` without checking `mounted`.
- **Impact:** Crash if widget is disposed while async gap elapses.
- **Fix:** Add `if (!mounted) return;` before every `setState()` inside async methods.
- **Effort:** XS (~20 min)

### 1.10 Frontend: `setState() after dispose()` in `CaptureScreen`
- **File:** `app/lib/src/features/capture/presentation/capture_screen.dart:95-103, 141-154`
- **Issue:** `PlatformException` and `CameraException` catch blocks call `setState()` without checking `mounted`.
- **Fix:** Add `if (!mounted) return;` before each `setState()` in catch blocks.
- **Effort:** XS (~10 min)

### 1.11 Frontend: `FocusTimer` `setState()` after dispose() on Resume
- **File:** `app/lib/src/features/session/presentation/widgets/focus_timer.dart:45`
- **Issue:** `didChangeAppLifecycleState` calls `setState()` without a `mounted` check. If the route is popped while backgrounded, resuming triggers a crash.
- **Fix:** Add `if (!mounted) return;` before `setState()` in `didChangeAppLifecycleState`.
- **Effort:** XS (~5 min)

### 1.12 Frontend: `Timer.periodic` Can Execute After `dispose()`
- **File:** `app/lib/src/features/session/presentation/widgets/focus_timer.dart:84-104`
- **Issue:** The timer callback can execute after `dispose()` has been called but before reaching the `if (!mounted)` guard. Also, timer drift accumulates because it subtracts 1s per tick instead of comparing against a `DateTime` target.
- **Fix:** Cancel timer in `dispose()` (already done, but also set a `_isDisposed` flag); use `DateTime` target math instead of decrementing.
- **Effort:** S (~30 min)

### 1.13 Frontend: `FocusTimer` Loses State on Process Death
- **File:** `app/lib/src/features/session/presentation/widgets/focus_timer.dart`
- **Issue:** `didChangeAppLifecycleState` handles `paused`/`resumed`, but if the OS kills the app (low memory), `_remaining` and `_isRunning` are lost.
- **Impact:** Timer resets to 10:00 mid-session. Breaks ADHD timeboxing promise.
- **Fix:** Persist `_remaining`, `_isRunning`, and `_backgroundedAt` to `SharedPreferences` in `paused`, restore in `initState`.
- **Effort:** S (~30 min)

### 1.14 Frontend: `CashToClearApiClient` Has No Request Timeout
- **File:** `app/lib/src/features/session/services/cash_to_clear_api.dart:122-148`
- **Issue:** `connectionTimeout` and `idleTimeout` are set on `HttpClient`, but `openUrl` + `close()` has no per-request timeout. A hung backend blocks the UI thread indefinitely.
- **Fix:** Wrap `_requestJson` in `Future.timeout(const Duration(seconds: 15))`.
- **Effort:** XS (~10 min)

### 1.15 Frontend: `CashToClearApiClient` No Response Size Limit
- **File:** `app/lib/src/features/session/services/cash_to_clear_api.dart:132-133`
- **Issue:** Response body is consumed with `response.transform(utf8.decoder).join()` with **no size limit**. A malicious or buggy server can stream an infinite response, exhausting memory.
- **Fix:** Cap response body at ~1MB before decoding; throw if exceeded.
- **Effort:** XS (~15 min)

### 1.16 Frontend: Decision Spam Bug (Same Group, Infinite Decisions)
- **File:** `app/lib/src/features/session/presentation/session_timer_screen.dart:146-158`
- **Issue:** Tapping "Keep" 50 times on the same group creates 50 decisions. Progress shows `50/5 sorted`. No deduplication.
- **Impact:** Corrupts session history, summary counts, and backend sync.
- **Fix:** Check if group already has a decision; replace instead of append, or increment a counter.
- **Effort:** XS (~20 min)

### 1.17 Frontend: `CaptureScreen` Silently Swallows Analysis Errors
- **File:** `app/lib/src/features/capture/presentation/capture_screen.dart:167-168`
- **Issue:** `unawaited(_analyzeCapture(capture))` — if detection throws, the error is logged and lost. User sees "Photo saved" but analysis silently failed.
- **Fix:** Wrap in try/catch and show SnackBar on failure, or await and show inline error.
- **Effort:** XS (~15 min)

### 1.18 Frontend: Camera Disposed on System Dialogs (`inactive` vs `paused`)
- **File:** `app/lib/src/features/capture/presentation/capture_screen.dart:55-67`
- **Issue:** `didChangeAppLifecycleState` disposes camera on `inactive`. On iOS, permission prompts and system dialogs trigger `inactive`, killing the camera unnecessarily.
- **Fix:** Only dispose on `paused` (or `detached`), not `inactive`.
- **Effort:** XS (~10 min)

### 1.19 Frontend: `Image.file` Re-Decodes JPEG on Every `setState`
- **File:** `app/lib/src/features/capture/presentation/capture_screen.dart:296`
- **Issue:** `Image.file(File(capture.path))` is used inside a `Stack` without any image caching. Every `setState` (e.g., analysis progress updates) re-reads the JPEG from disk and re-decodes it, causing frame drops.
- **Fix:** Use `Image.file(..., cacheWidth: 800)` or wrap in `ImageCache`.
- **Effort:** XS (~10 min)

### 1.20 Frontend: Timer Doesn't Pause/Reset on Completion
- **File:** `app/lib/src/features/session/presentation/session_timer_screen.dart:331-338`
- **Issue:** `_handleTimerCompleted` shows a bottom sheet but does **not** pause or reset the timer. If the user dismisses the sheet, the timer remains at 00:00 and the sprint can continue indefinitely.
- **Fix:** Call timer reset/pause before showing the sheet.
- **Effort:** XS (~10 min)

---

## 🟠 TIER 2 — High Leverage (Architectural, Unlocks Future Work)

> These are medium effort but unblock entire work packages or prevent entire classes of bugs.

### 2.1 WP3: Drift/SQLite Persistence (Sessions & Decisions Survive Restarts)
- **Files:** New `app/lib/src/data/db/`, refactor `session_timer_screen.dart`
- **Issue:** All session data is in-memory. Kill app = total data loss. MVP spec §6.2 requires SQLite.
- **Impact:** Core MVP requirement. Blocks history, summary, and CSV export.
- **Leverage:** Unlocks WP4 (Decision Card), WP6 (Summary + CSV), and WP8 (History screen).
- **Effort:** M (1-2 days)

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

### 3.7 Backend: SQLite WAL Mode + Composite Queries
- **File:** `server/app/services/session_store.py:541-544`
- **Issue:** `PRAGMA foreign_keys = ON` is set, but `journal_mode=WAL` is missing, creating write-lock contention under concurrent load.
- **Fix:** Add `PRAGMA journal_mode=WAL` in `_ensure_schema()`.
- **Effort:** XS (~5 min)

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

1. **Today (2 hours):** Knock out Tier 0 + Tier 1 — they're all tiny, high-impact, and many are security-critical.
2. **This Week:** WP3 (Drift persistence) — it unlocks history, summary, and CSV.
3. **Next Sprint:** WP1 (ONNX abstraction) — unblocks real inference and web builds.
4. **Then:** WP2 → WP4 → WP5 → WP6 in dependency order.

The full dependency graph:
```
Tier 0+1 fixes (parallel) ────────────────────────────┐
WP1 (ONNX) ─┐                                         │
            ├─► WP2 (Moondream) ─┐                   ├──► WP8 (Polish)
WP3 (Drift) ─┤                  ├─► WP5 (Valuation) ─┤
             └─► WP4 (Decision) ─┘                   │
                                                    ├──► WP6 (Summary + CSV)
WP7 (Server) depends on WP5 ────────────────────────┘
```
