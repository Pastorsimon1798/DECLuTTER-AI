# 2026 Launch Build Progress

This file tracks implementation progress against `DECLUTTER_AI_2026_LAUNCH_PLAN_WITH_PORTER_VALUE_CHAIN.md`.

## Completed in this commit

- ✅ WP0 (partial): repo aligned to launch plan in README.
- ✅ WP2 (starter): FastAPI backend scaffold created with required launch modules:
  - `analysis`
  - `valuation`
  - `listing_drafts`
  - `marketplace_ebay`
  - `public_listings`
  - `mcp`
  - `a2a`
  - `user_data`
- ✅ WP2 starter backend tests added for health and analysis route.
- ✅ WP3 (starter): Firebase Auth + App Check request protection added for private routes.
- ✅ WP3 (hardening): strict-mode runtime path now uses Firebase Admin SDK when configured.
- ✅ WP4 (starter): secure image intake endpoint with EXIF stripping and local storage adapter.
- ✅ WP4 (hardening starter): signed-upload session scaffold + malware scanner hook interface.
- ✅ WP5 (starter): deterministic structured analysis adapter wired to `/analysis/run`.
- ✅ WP6 (starter): comps-based valuation service with confidence + source metadata.
- ✅ WP8/WP9 (starter): listing draft generation + mock eBay publish/export flow.
- ✅ Launch ops helper: `/health/readiness` endpoint reports production dependency readiness from environment.
- ✅ Same-day launch hardening: backend CORS config, app factory, Dockerfile, env template, CI, and launch checklist.
- ✅ Same-day smoke surface: public root page, `/launch/status`, and `server/scripts/smoke_backend.py`.
- ✅ Cash-to-Clear product loop starter: durable sessions, items, decisions, valuations, listing drafts, and money-on-the-table totals.
- ✅ Flutter Cash-to-Clear client starter: sprint UI can sync backend sessions, group valuations, decisions, and Money-on-the-Table totals when configured.
- ✅ Standalone listing fallback: users can generate public HTML listing pages without eBay or marketplace publishing.
- ✅ Flutter standalone listing page starter: synced sprint groups can request and display public listing-page links.
- ✅ Session summary/history: backend session list + summary endpoints and Flutter sprint summary card.
- ✅ Hostinger VPS deploy handoff: Docker Compose + Caddy bundle, self-hosted MVP env template, and public URL smoke script.
- ✅ Self-hosted MVP readiness: shared-token auth, local uploads, and SQLite persistence can pass a separate `self_hosted_mvp_ready` gate without Firebase/S3/eBay.
- ✅ Home inference hook: optional OpenAI-compatible/LM Studio endpoint support mirrors Achiote's env pattern for using the home inference server.

## Completed — Phase 1: Barter/Trade Marketplace

- ✅ Task 1: Trade Credit System — `TradeCreditStore` with SQLite ledger, earn/spend/balance/history.
- ✅ Task 2: Trade Listing & Matching Service — create listing, nearby discovery (Haversine), propose/accept/decline, credit top-up.
- ✅ Task 3: Trade API Routes — full CRUD endpoints wired into FastAPI with scaffold auth.
- ✅ Task 4: ND-Specific UX — message templates, condition checklists, explicit trade rules.
- ✅ Task 5: Reputation System — trade reviews, avg rating, trade count, top tags.
- ✅ Task 6: Safety Checklists — 10 category-specific checklists.
- ✅ Task 7: Verified Trader Badges — email/phone/id verification.
- ✅ Task 8: Algorithmic Matching — multi-party trade loop detection (2–4 participants, DFS cycles).
- ✅ Task 9: Price Seed Expansion — 4,018 → 6,072 items across 9 categories.
- ✅ Task 10: Flutter Trade UI — browse, create listing, matches, wallet, hub screen, bottom-nav integration.
- ✅ Backend tests: 170 passing (49 trade-specific), 0 failures.

## Next implementation steps

1. Ops: deploy the self-hosted MVP container on the Hostinger VPS using `server/deploy/hostinger-vps/`.
2. UX/API: point the Flutter or web client at the VPS URL with the shared bearer token.
3. WP5: point `DECLUTTER_ANALYSIS_PROVIDER=lmstudio` at the home inference server and build an eval set for item detection quality.
4. WP6: improve valuation with local/manual comps workflow before requiring live marketplace APIs.
5. WP8/WP9: keep public HTML listing pages and manual marketplace posting as the MVP path; add OAuth/eBay API later.
6. Phase 2 trade: shipping integration, nonprofit partnerships, distributed moderation.
7. Later production: provision Firebase Admin credentials + production token validation smoke tests only when real public user accounts are needed.
8. Later production: replace local uploads with object storage only when VPS disk is no longer enough.
