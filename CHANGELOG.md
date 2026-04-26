# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Decision Card UI with 5 action buttons (Keep, Donate, Trash, Relocate, Maybe), undo, and notes
- Valuation feature: backend `POST /valuation` endpoint + Flutter service with offline fallback
- Session Summary screen with sprint stats, per-group details, and total resale value
- CSV export service with share_plus integration (mobile) and blob download (web)
- 29 backend security tests covering XSS, CSV injection, path traversal, prompt injection, auth, rate limiting, request size, CORS, and correlation ID
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
