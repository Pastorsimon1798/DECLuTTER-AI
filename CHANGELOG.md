# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added — Phase 1: Barter/Trade Marketplace
- **Task 1 — Trade Credit System**: `TradeCreditStore` in `app/models/trade.py`. SQLite-backed non-monetary credits (1 credit = $1 fair value). Earn/spend/balance/history. No cash purchases. 5 tests passing.
- **Task 2 — Trade Service**: `TradeService` in `app/services/trade_service.py`. Create listing, find nearby (Haversine), propose/accept/decline trade, credit top-up, no self-trade guard. 7 tests passing.
- **Task 3 — Trade API Routes**: `app/api/routes/trade.py` wired into `main.py`. Endpoints: `POST /trade/listings`, `GET /trade/listings/nearby`, `POST /trade/matches`, `POST /trade/matches/{id}/accept`, `POST /trade/matches/{id}/decline`, `GET /trade/credits`. Scaffold auth (`_owner_uid`, `_set_auth_mode`), `ValueError`→`HTTPException(400)` wrapping. 5 tests passing.
- **Task 4 — ND-Specific UX**: `app/services/trade_templates.py`. Message templates (propose/accept/decline/follow-up), condition checklists (new→for_parts), explicit trade rules. Endpoints: `/trade/templates/{intent}`, `/trade/conditions/{condition}`, `/trade/rules`. 3 tests passing.
- **Task 5 — Reputation System**: `trade_reviews` table. `rate_user()` and `get_reputation()` with avg rating, total trades, top tags. Endpoints: `POST /trade/matches/{id}/rate`, `GET /trade/reputation/{user_id}`. 4 tests passing.
- **Task 6 — Safety Checklists**: `app/services/safety_checklists.py`. 10 category-specific checklists (electronics, baby, disability, art, plants, books, clothing, games, sports, music). Endpoints: `/trade/safety/{tag}`, `/trade/safety`. 5 tests passing.
- **Task 7 — Verified Trader Badges**: `user_verifications` table. `verify_user()` supports email/phone/id. Endpoints: `POST /trade/verify`, `GET /trade/verify/{user_id}`. 5 tests passing.
- **Task 8 — Algorithmic Matching**: `app/services/trade_matcher.py`. Want-graph builder + DFS cycle detection for multi-party trade loops (2–4 participants) with value-match scoring. Endpoint: `GET /trade/loops`. 5 tests passing.
- **Task 9 — Price Seed Expansion**: Expanded `app/data/price_seed.json` from **4,018 → 6,072 items** across plants, gaming, disability, books, clothing, electronics, sports, baby, instruments. 170 total backend tests passing.
- **Task 10 — Flutter Trade UI**: Full feature under `lib/src/features/trade/`:
  - Models: `TradeListing`, `TradeMatch`, `CreditTransaction`, `CreditBalance`, `ReputationProfile`
  - Service: `TradeService` API client
  - Widgets: `ConditionBadge`, `TradeValueBadge`, `TemplatePicker`
  - Screens: `BrowseTradesScreen`, `TradeDetailScreen`, `CreateTradeListingScreen`, `MyMatchesScreen`, `CreditsWalletScreen`, `MyListingsScreen`, `TradeHubScreen`
  - Integration: `DeclutterHomeScreen` with bottom nav toggle between Declutter/Trade modes

### Added — Pre-Trade (MVP)
- Decision Card UI with 5 action buttons (Keep, Donate, Trash, Relocate, Maybe), undo, and notes
- Valuation feature: backend `POST /valuation` endpoint + Flutter service with offline fallback
- Session Summary screen with sprint stats, per-group details, and total resale value
- CSV export service with share_plus integration (mobile) and blob download (web)
- 29+ backend security tests covering XSS, CSV injection, path traversal, prompt injection, auth, rate limiting, request size, CORS, and correlation ID
- ONNX Runtime as default inference backend with TFLite fallback
- SessionController extracted from SessionTimerScreen for testability
- Haptic feedback and semantic labels for accessibility

### Changed
- Landing page repositioned for ADHD-friendly decluttering (not seller tool)
- SessionTimerScreen now uses ListenableBuilder with injected SessionController
- CaptureScreen copies photos to persistent path before analysis

### Fixed
- Tier 0–3 security, reliability, and architectural issues from codebase audit
- `use_build_context_synchronously` and `unnecessary_import` analyzer warnings
- Async detector flow with proper error handling via SnackBar
- Database isolation in trade tests: `tempfile.mktemp(suffix=".sqlite3")` replaces hardcoded `/tmp/` paths

## [0.1.0] - 2026-04-25

### Added
- Initial Flutter MVP: capture screen, detection service, session timer
- FastAPI backend scaffold: analysis, valuation, listing, marketplace, public pages
- Mock detection flow with debug bounding box overlays
- 10-minute sprint timer with ADHD-friendly quick-start guidance
- Cash-to-Clear backend sync for remote session management
- Basic widget and API tests

[unreleased]: https://github.com/Pastorsimon1798/DECLuTTER-AI/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Pastorsimon1798/DECLuTTER-AI/releases/tag/v0.1.0
