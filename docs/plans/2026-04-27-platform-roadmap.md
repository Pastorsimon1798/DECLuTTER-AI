# DECLuTTER AI — Platform Roadmap

> **Status:** Future plan. Not yet scheduled for implementation.
> **Created:** 2026-04-27
> **Purpose:** Bridge the gap between Phase 1 (Barter/Trade Marketplace, complete) and a full production platform.
> **Audience:** AI coding agents, maintainers, product reviewers.
> **Supersedes:** Nothing. Builds on `2026-04-28-barter-marketplace.md` Phase 2 specs.

---

## Executive Summary

Phase 1 gave us a **working trade marketplace** with credits, listings, matching, reputation, safety, verification, algorithmic loops, and a Flutter UI. This is a feature-complete barter system.

What we do **not** have is a **platform**: real user identities, production data infrastructure, distribution, monetization, legal compliance, or operational tooling. This document maps the shortest path from "working app" to "shippable platform."

---

## Guiding Principles

1. **Neurodivergent-first at every layer.** Auth, onboarding, error messages, and payment flows must be ADHD-friendly.
2. **Privacy-first by default.** On-device ML where possible. No photo leaves the device unless the user opts in.
3. **No mock-only code paths in production.** Anything a real user touches must work with real infrastructure.
4. **Ship P0 before touching P1.** Foundation blocks everything. Do not build moderation before auth.
5. **Keep Flutter. Keep the trade UI.** Do not rewrite existing screens. Add, don't replace.

---

## P0 — Platform Foundation

*Without these, nothing else matters. Estimated: 3–4 weeks.*

---

### P0.1 — Real User Authentication

**Goal:** Replace scaffold/shared-token auth with Firebase Auth. Anonymous-first, upgradeable to email/Google/Apple.

**Why it blocks everything:** All trade features (reputation, credits, verification, listings) currently map to `uid: "scaffold-user"`. Real users need real identities.

**Changes:**
- `server/app/services/auth.py` (new): Firebase Admin SDK token verification. Keep scaffold mode as `DECLUTTER_AUTH_MODE=scaffold` for tests/local dev.
- `server/app/dependencies.py`: Update `protected` dependency to validate Firebase ID tokens when `auth_mode != scaffold`.
- `app/lib/src/features/auth/` (new): Firebase Auth integration.
  - `auth_service.dart` — anonymous sign-in, email/password link, Google Sign-In, Apple Sign-In.
  - `auth_guard.dart` — route guard for protected screens.
- `app/pubspec.yaml`: Add `firebase_auth`, `firebase_core`, `google_sign_in`, `sign_in_with_apple`.
- `server/.env.example`: Add `FIREBASE_PROJECT_ID`, `FIREBASE_ADMIN_SDK_PATH`.

**Acceptance:**
- `pytest` passes in scaffold mode with zero regressions.
- New test `test_firebase_auth.py` validates token parsing with mocked Firebase Admin.
- Flutter app can sign in anonymously and receive a real UID.
- All existing trade endpoints work with real Firebase UIDs.

**Anti-requirements:**
- Do NOT remove scaffold mode. It is essential for CI and local dev.
- Do NOT require email verification for anonymous users.
- Do NOT add phone number auth in P0 (deferred to P1).

---

### P0.2 — Production Database Migration

**Goal:** Move from SQLite to PostgreSQL with SQLAlchemy 2 + Alembic migrations.

**Why it blocks everything:** SQLite cannot handle concurrent writes, has no replication, and lives on a single VPS disk. One `rm` and the platform is gone.

**Changes:**
- `server/app/db/` (new):
  - `engine.py` — SQLAlchemy async engine factory (sync for now if async is hard).
  - `session.py` — dependency-injectable DB sessions.
- `server/alembic/` (new): Alembic migration environment.
- `server/app/models/` — Convert all SQLite raw-SQL models to SQLAlchemy declarative models:
  - `session_store.py` → `models/session.py`
  - `trade.py` → `models/trade.py`
  - `trade_service.py` tables → `models/trade_listing.py`, `models/trade_match.py`, `models/trade_review.py`, `models/user_verification.py`
- `server/docker-compose.yml`: Add `postgres:16` service.
- `server/.env.example`: Add `DATABASE_URL=postgresql://...`.

**Migration strategy (zero-downtime for existing data):**
1. Write SQLAlchemy models that mirror existing SQLite schema.
2. Write one-time export script: SQLite → JSON → PostgreSQL import.
3. Run import on staging.
4. Switch `DATABASE_URL` env var.
5. Old SQLite file kept as backup.

**Acceptance:**
- All 170 existing backend tests pass against PostgreSQL in CI.
- `alembic upgrade head` runs cleanly on a fresh database.
- `alembic downgrade -1` works (verify rollback).
- Trade data can be exported from SQLite and imported into Postgres without loss.

**Anti-requirements:**
- Do NOT use an ORM for the Flutter app. Keep drift deferred until P0 is stable.
- Do NOT add read replicas in P0. Single Postgres instance is fine.

---

### P0.3 — Flutter Drift Persistence

**Goal:** Sessions, decisions, and trade data survive app restarts.

**Why it blocks retention:** Users lose all progress when they close the app. No history = no reason to return.

**Changes:**
- `app/pubspec.yaml`: Add `drift`, `drift_flutter`, `path_provider`, `path`. Dev deps: `drift_dev`, `build_runner`.
- **Critical:** Commit generated `.g.dart` files so CI does not need `build_runner`.
- `app/lib/src/data/db/` (new):
  - `app_database.dart` — drift database with tables: `sessions`, `groups`, `decisions`, `valuations`, `trade_listings`, `trade_matches`, `credit_transactions`, `rules`.
  - `daos/session_dao.dart`, `daos/decision_dao.dart`, `daos/valuation_dao.dart`, `daos/trade_dao.dart`.
- Wire `SessionTimerScreen`, `DecisionCard`, and trade screens to persist through DAOs.
- `HistoryScreen` (new): list of past sessions with counts, trade history, total value cleared.

**Acceptance:**
- Capture → decide → kill app → relaunch → history shows the prior session.
- Create trade listing → kill app → relaunch → listing appears in "My Listings."
- `flutter test` has at least one DAO round-trip test per table using drift's in-memory executor.

**Anti-requirements:**
- Do NOT sync drift to cloud in P0. Local-only is fine.
- Do NOT build a full offline trade experience. Trade requires network.

---

### P0.4 — App Store Submission Prep

**Goal:** Get DECLuTTER onto the iOS App Store and Google Play Store.

**Why it blocks users:** 99% of mobile users discover apps through stores. Sideloading is a non-starter.

**Changes:**
- `app/ios/`: Configure signing, bundle ID, app icons, launch screen.
- `app/android/`: Configure signing, bundle ID, app icons, adaptive icons.
- `app/lib/src/features/settings/presentation/settings_screen.dart`: Add "Delete Account" button (App Store requirement).
- `docs/app-store-assets/` (new): Screenshots, feature graphics, promo video script.
- `PRIVACY_POLICY.md` (new): Plain-language privacy policy (required for stores).
- `TERMS_OF_SERVICE.md` (new): Basic ToS covering trade marketplace liability.
- App Store Connect + Google Play Console accounts set up.

**Acceptance:**
- `flutter build ios --release` produces an archive that passes Xcode validation.
- `flutter build appbundle --release` produces an AAB under 150MB.
- App passes Apple App Review (no crashes, no private API usage, proper permissions).
- App passes Google Play Review (no policy violations, proper content rating).

**Anti-requirements:**
- Do NOT add in-app purchases in P0. The app is free with no monetization.
- Do NOT add app review prompts in P0.

---

### P0.5 — ONNX Runtime + Moondream 2 Integration

**Goal:** Replace TFLite + mocks with real on-device item recognition.

**Why it blocks credibility:** The core promise is "AI detects your clutter." If it doesn't actually detect anything, users will churn immediately.

**Changes:**
- `app/assets/model/README.md`: Document Moondream 2 ONNX int8 acquisition. Do not commit weights.
- `app/lib/src/features/detect/services/moondream_service.dart` (new): Wraps ONNX Runtime session.
  - `Future<List<DetectedItem>> describe(File image)` — returns `{label, category, confidence, boundingBox?}`.
- `app/lib/src/features/detect/domain/detection.dart`: Extend `Detection` with `category` and optional `description` fields. Do not break existing consumers.
- Wire `DetectorService` to prefer Moondream when model file is present; fall back to mock JSON only when missing.
- Remove `tflite_flutter` from `pubspec.yaml` once ONNX is validated.

**Acceptance:**
- With Moondream ONNX file placed in `app/assets/model/`, capturing a photo produces real labeled detections.
- Inference completes under ~5s on a mid-range 2023+ phone.
- No network calls during detection.
- `flutter test` passes with ONNX mocks when no model file is present.
- No `tflite_flutter` references remain in `lib/` or `test/`.

**Anti-requirements:**
- Do NOT commit model weights.
- Do NOT use Ultralytics YOLOv8/v11 (AGPL).

---

## P1 — Growth & Trust

*Need these to acquire and retain users. Estimated: 2–3 weeks.*

---

### P1.1 — Push Notifications

**Goal:** Notify users of trade proposals, acceptances, messages, and safety reminders.

**Changes:**
- `app/pubspec.yaml`: Add `firebase_messaging`.
- `server/app/services/notifications.py` (new): FCM push sender.
- `server/app/api/routes/trade.py`: Trigger push on `propose_trade`, `accept_trade`.
- `app/lib/src/features/notifications/` (new): Notification handler, permission request, deep-link routing.

**Acceptance:**
- User A proposes a trade → User B receives push notification within 5 seconds.
- Tapping notification opens `TradeDetailScreen` for the relevant match.

---

### P1.2 — Content Moderation & Reporting

**Goal:** Let users report listings/matches. Auto-flag suspicious content.

**Changes:**
- `server/app/models/moderation.py` (new): `reports` table with `reporter_id`, `target_type`, `target_id`, `reason`, `status`.
- `server/app/api/routes/moderation.py` (new): `POST /reports`, `GET /moderation/queue` (admin only).
- `server/app/services/moderation_service.py` (new): Keyword detection, repeat-complainer flagging.
- Flutter: "Report" button on every listing and match.

**Acceptance:**
- Report submission returns confirmation.
- Admin endpoint lists open reports sorted by severity.

---

### P1.3 — Legal Compliance Framework

**Goal:** Meet App Store, GDPR, and marketplace liability requirements.

**Changes:**
- `PRIVACY_POLICY.md`: Firebase Auth data, location data (trade radius), photo handling, data retention.
- `TERMS_OF_SERVICE.md`: Trade marketplace liability, dispute resolution, prohibited items, account termination.
- `COOKIE_POLICY.md` (if web presence grows).
- `server/app/middleware/gdpr.py` (new): Right-to-deletion endpoint `DELETE /me/account`.
- Flutter: "Download my data" button in settings.

**Acceptance:**
- App Review does not reject for missing legal docs.
- `DELETE /me/account` removes all user data from Postgres within 30 days (soft delete + hard delete job).

---

### P1.4 — Enhanced Verification Pipeline

**Goal:** Make "verified" actually mean something.

**Changes:**
- Integrate Stripe Identity for automated ID verification.
- Phone verification via Twilio or Firebase Phone Auth.
- Manual review queue for edge cases.
- Flutter: Verification badge UI with tooltip explaining the verification level.

**Acceptance:**
- User can complete email → phone → ID verification in under 3 minutes.
- Stripe Identity webhook updates verification status automatically.

---

## P2 — Revenue & Scale

*Turn the platform into a business. Estimated: 4–6 weeks.*

---

### P2.1 — Shipping Label Integration

**Goal:** Users buy discounted shipping labels in-app. Platform takes a cut.

**Changes:**
- `server/app/services/shipping.py` (new): EasyPost or Pirate Ship API client.
- `server/app/api/routes/shipping.py` (new): `POST /shipping/quote`, `POST /shipping/label`.
- Flutter: "Ship this trade" flow with address form, rate selection, label generation.
- `server/app/models/shipping.py` (new): `shipping_labels` table with tracking numbers.

**Acceptance:**
- User can generate a USPS label for under $5.
- Platform earns $0.50–$1 per label.
- Tracking number is visible in the match detail screen.

---

### P2.2 — Premium Tier (DECLuTTER Pro)

**Goal:** Freemium model with meaningful upgrades.

**Changes:**
- `server/app/models/subscription.py` (new): `subscriptions` table with `tier`, `expires_at`.
- `server/app/services/billing.py` (new): Stripe Checkout integration.
- Flutter: "Upgrade to Pro" screen.

**Pro features:**
- Verified badge included.
- Trade radius: 50km vs 10km free.
- Priority matching (your listings appear first).
- Unlimited listings (free tier: 5 active).
- Credit purchase top-up (buy credits with real money).

**Acceptance:**
- Stripe Checkout session completes successfully.
- Webhook updates subscription status.
- Free-tier limits are enforced server-side.

---

### P2.3 — Nonprofit Partnerships

**Goal:** Integrate with disability equipment reuse networks for mission credibility and grant funding.

**Changes:**
- `server/app/services/nonprofits.py` (new): Pass It On Center, TechOWL, REquipment, CReATE APIs or CSV imports.
- `server/app/api/routes/nonprofits.py` (new): `GET /nonprofits/nearby`, `POST /nonprofits/donate`.
- Flutter: "Donate to nonprofit" option alongside "List for trade."
- Equipment safety recall database integration (CPSC API).

**Acceptance:**
- User can search nonprofit partners by ZIP code.
- Donation handoff generates a receipt for tax purposes.

---

### P2.4 — Tax Compliance

**Goal:** Handle 1099-B equivalent for high-volume traders.

**Changes:**
- `server/app/services/tax_reporting.py` (new): Annual trade value summary per user.
- `server/app/api/routes/tax.py` (new): `GET /tax/summary?year=2026`.
- Flutter: Tax dashboard in settings.
- Legal review of credit system classification (barter vs currency).

**Acceptance:**
- Users with >$600 trade value receive a downloadable summary.
- Summary includes date, item, value, counterparty (anonymized).

---

### P2.5 — Infrastructure Scaling

**Goal:** Move from single VPS to production-grade infrastructure.

**Changes:**
- **Object storage:** Migrate local image storage to S3-compatible (Cloudflare R2, Wasabi, or AWS S3).
- **CDN:** Serve public listing images via CDN.
- **Monitoring:** Add Sentry for error tracking, Prometheus + Grafana for metrics.
- **Backups:** Automated daily Postgres backups to object storage.
- **Staging environment:** Separate VPS or Cloud Run instance for pre-prod testing.

**Acceptance:**
- Image upload/download works via presigned S3 URLs.
- Sentry captures unhandled exceptions with stack traces.
- Backups are restorable within 1 hour.

---

## P3 — Moat & Differentiation

*What makes DECLuTTER uniquely DECLuTTER. Estimated: 3–4 weeks.*

---

### P3.1 — Agent-Ready Ecosystem

**Goal:** Make DECLuTTER the most agent-friendly decluttering platform.

**Changes:**
- **MCP server:** `server/app/mcp/` — expose trade listings, reputation, safety checklists as Model Context Protocol resources.
- **A2A endpoints:** `server/app/a2a/` — buyer agents can query listings, seller agents can manage inventory.
- **OpenAPI spec:** Auto-generated from FastAPI, published at `/openapi.json`.
- **Schema.org JSON-LD:** Rich structured data on public listing pages for SEO and agent discoverability.

**Acceptance:**
- An external MCP client can list trade items and propose trades.
- A2A agent can query `/a2a/listings` and receive structured JSON-LD.

---

### P3.2 — Community & Network Effects

**Goal:** Users come back because other users are here.

**Changes:**
- **Neighborhood groups:** Geofenced trade groups ("Downtown Toronto Traders").
- **Trade circles:** Recurring multi-party trades facilitated by algorithmic matching.
- **ADHD buddy system:** Pair users for accountability declutter sprints.
- **Leaderboards:** "Most space cleared this month" (opt-in, shame-free).

**Acceptance:**
- User can join a neighborhood group and see group-only listings.
- Buddy system pairs two users for a synchronous sprint.

---

### P3.3 — Internationalization (i18n)

**Goal:** English is not the only language.

**Changes:**
- `app/lib/l10n/` (new): ARB files for Spanish, French, German.
- `server/app/i18n/` (new): Backend error messages in supported languages.
- `flutter_localizations` package.

**Acceptance:**
- App UI switches language based on device locale.
- Backend errors return localized messages when `Accept-Language` header is set.

---

## Dependency Order

```
P0.1 (Auth) ──┐
P0.2 (DB)  ───┼──► P1.1 (Push) ──┐
P0.3 (Drift) ─┤                    ├──► P2.1 (Shipping) ──┐
P0.4 (Stores)─┤                    │                       ├──► P3.1 (Agents)
P0.5 (ONNX)  ─┘                    ├──► P2.2 (Premium)   ──┤
              P1.2 (Moderation) ───┤                       ├──► P3.2 (Community)
              P1.3 (Legal) ────────┤                       ├──► P3.3 (i18n)
              P1.4 (Verify) ───────┘                       │
                                                           │
              P2.3 (Nonprofits) ───────────────────────────┘
              P2.4 (Tax) ──────────────────────────────────┘
              P2.5 (Infra) ────────────────────────────────┘
```

**Parallelizable:**
- P0.1, P0.2, P0.3 can run concurrently.
- P0.4 (stores) and P0.5 (ONNX) are mostly independent.
- P1.x tasks can run in parallel once P0.1 and P0.2 are done.
- P2.x tasks depend on P1.3 (legal) for monetization.
- P3.x tasks are mostly independent and can start once P2.2 (premium) defines the API surface.

---

## Success Metrics

| Metric | P0 Complete | P1 Complete | P2 Complete | P3 Complete |
|--------|-------------|-------------|-------------|-------------|
| Daily active users | 0 → 10 | 10 → 100 | 100 → 1,000 | 1,000 → 5,000 |
| Trade completion rate | N/A | >20% | >30% | >40% |
| App store rating | N/A | 4.0+ | 4.2+ | 4.5+ |
| Revenue | $0 | $0 | >$500/mo | >$5,000/mo |
| Verified trader % | N/A | N/A | >5% | >15% |
| Multi-party matches/week | 0 | >1 | >5 | >20 |
| On-device detection accuracy | N/A | N/A | >70% | >85% |

---

## Anti-Goals (Still)

- **Do not replace Flutter.** Not in P0, P1, P2, or P3.
- **Do not build a generic chatbot.** The product produces decisions and actions.
- **Do not scrape marketplaces.** Use official APIs or listing kits only.
- **Do not add live marketplace auto-posting in P0/P1.** eBay/Facebook auto-post is P2+ and requires legal review.
- **Do not overclaim value.** Always show "estimated" or "likely range," never "guaranteed."

---

## File Map (New Files by Phase)

### P0
- `server/app/services/auth.py`
- `server/app/db/engine.py`, `server/app/db/session.py`
- `server/alembic/`
- `server/app/models/` (SQLAlchemy conversions)
- `app/lib/src/features/auth/`
- `app/lib/src/data/db/`
- `app/lib/src/features/settings/presentation/settings_screen.dart`
- `PRIVACY_POLICY.md`
- `TERMS_OF_SERVICE.md`
- `app/lib/src/features/detect/services/moondream_service.dart`

### P1
- `server/app/services/notifications.py`
- `server/app/api/routes/moderation.py`
- `server/app/models/moderation.py`
- `server/app/middleware/gdpr.py`
- `server/app/services/verification_pipeline.py`

### P2
- `server/app/services/shipping.py`
- `server/app/api/routes/shipping.py`
- `server/app/models/shipping.py`
- `server/app/models/subscription.py`
- `server/app/services/billing.py`
- `server/app/services/nonprofits.py`
- `server/app/services/tax_reporting.py`

### P3
- `server/app/mcp/`
- `server/app/a2a/`
- `app/lib/l10n/`
- `server/app/i18n/`

---

## Rules for Agents Picking This Up

1. **Read the full phase before touching files.** P0 must be complete before P1 starts.
2. **Do not expand scope.** If a task says "Stripe Checkout," do not also build PayPal.
3. **Keep scaffold mode alive.** All tests must pass in scaffold mode. Real auth is opt-in via env var.
4. **Write the minimum tests for acceptance criteria.** No snapshot tests. No fuzzing.
5. **ADHD-friendly UX at every layer.** Onboarding must be <3 steps. Error messages must suggest a next action. No dead ends.
6. **Privacy-first by default.** Ask for location permission only when user opens trade screen. Ask for camera only when user taps capture. No preemptive permission requests.

---

*This plan is frozen as of 2026-04-27. Update it when a phase is completed or priorities change.*
