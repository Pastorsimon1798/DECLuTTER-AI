# DECLuTTER AI 🧠✨

> *The ADHD-friendly decluttering assistant. Snap a photo, see your items grouped, decide keep / donate / trash / relocate / maybe in a 10-minute sprint — then trade what you don't need with people nearby.*

[![App CI](https://github.com/KyaniteLabs/DECLuTTER-AI/actions/workflows/flutter-test.yml/badge.svg)](https://github.com/KyaniteLabs/DECLuTTER-AI/actions)
[![Server CI](https://github.com/KyaniteLabs/DECLuTTER-AI/actions/workflows/server-test.yml/badge.svg)](https://github.com/KyaniteLabs/DECLuTTER-AI/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Flutter Version](https://img.shields.io/badge/Flutter-3.19+-blue.svg)](https://flutter.dev)
[![Python Version](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)

---


## Public Discovery

**DECLuTTER AI** is an ADHD-friendly decluttering app for neurodivergent people, families, organizers, and resale workflows. It combines on-device object detection, simple decision cards, resale valuation, and local barter/trade tools so a messy room becomes a short, shame-free action sprint.

**AI discovery:** [`llms.txt`](llms.txt) provides a compact project summary for AI assistants and search crawlers.

**Best-fit searches:** ADHD decluttering app, AI decluttering assistant, neurodivergent productivity tool, Flutter object detection app, FastAPI marketplace backend, resale valuation app, local barter marketplace, privacy-first organization app.

## 🎯 Why DECLuTTER AI?

Adults with ADHD often feel **paralyzed by clutter**. Generic apps identify objects but don't help you *decide what to do with them*.

**DECLuTTER AI** converts a messy photo into simple, time-boxed actions with neurodivergent-friendly design:
- Large buttons, minimal text, visible progress
- Undo everything — no judgment
- Haptic feedback on every decision
- "Not today" escape route on every screen
- Shame-free language (never "mess," "junk," or "lazy")
- **NEW:** Trade your decluttered items locally — no cash, no apps, no hassle

---

## ✨ Features

### Core Declutter Flow
| Feature | Description |
|---|---|
| 📸 **One-Tap Capture** | Take a photo of any cluttered zone — desk, closet, dresser, shelf |
| 🏷️ **Smart Grouping** | On-device AI groups items by category: cables, books, clothing, electronics |
| ⏱️ **10-Min Sprint Timer** | ADHD-friendly focus sessions with celebratory completion |
| 💰 **Resale Valuation** | See "Money on the Table" estimates for sellable items (6,072 seeded prices + LLM fallback) |
| 📝 **One-Tap Decisions** | Keep · Donate · Trash · Relocate · Maybe — with undo and notes |
| 📊 **CSV Export** | Track your declutter progress over time |
| 🔒 **Privacy-First** | All analysis happens on-device by default |

### Barter/Trade Marketplace (NEW)
| Feature | Description |
|---|---|
| 🔄 **Local Trade Listings** | List items you decluttered for trade using fair-market credit values |
| 📍 **Nearby Discovery** | Find trade listings within a radius using Haversine distance filtering |
| 💳 **Non-Monetary Credits** | 1 credit = $1 fair value. Earn by trading, spend on items you want. No cash needed |
| 🧩 **Algorithmic Matching** | Multi-party trade loop detection (2–4 participants) finds circular trades where everyone wins |
| ⭐ **Reputation System** | Rate traders after each exchange. View average rating, trade count, and trust tags |
| 🛡️ **Safety Checklists** | Category-specific safety guides (electronics, baby, disability, plants, art, and more) |
| ✅ **Verified Trader Badges** | Email, phone, and ID verification badges build community trust |
| 💬 **ND-Friendly Messaging** | Built-in message templates, condition checklists, and explicit trade rules reduce social friction |

---

## 🖼️ Screenshots

> *Demo GIF and screenshots coming soon — follow [Discussions](https://github.com/KyaniteLabs/DECLuTTER-AI/discussions) for updates!*

---

## 🚀 Quick Start

### Flutter App

```bash
# 1. Install Flutter 3.19+ from https://docs.flutter.dev/get-started/install

# 2. Clone and setup
git clone https://github.com/KyaniteLabs/DECLuTTER-AI.git
cd DECLuTTER-AI/app
flutter pub get

# 3. Run on device or simulator
flutter run
```

### Backend

```bash
cd DECLuTTER-AI/server
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
PYTHONPATH=app uvicorn app.main:app --reload
```

### Run Tests

```bash
# Flutter
cd app && flutter analyze && flutter test

# Backend (170 tests, all passing)
cd server && source .venv/bin/activate && pytest -x -q
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         Flutter Mobile App (Dart)       │
│  ┌─────────┐ ┌─────────┐ ┌──────────┐  │
│  │ Capture │ │ Detect  │ │  Decide  │  │
│  │  📸     │ │  🔍     │ │  ✅     │  │
│  └────┬────┘ └────┬────┘ └────┬─────┘  │
│       └───────────┴───────────┘         │
│              ONNX Runtime               │
│         (on-device, private)            │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │     🔄 Trade Marketplace UI       │  │
│  │  Browse · List · Match · Wallet   │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
┌───────────────┐       ┌───────────────┐
│  FastAPI      │◄─────►│  Local SQLite │
│  Backend      │       │  (sessions +  │
│  (Python)     │       │   trade data) │
└───────────────┘       └───────────────┘
        │
        ▼
┌───────────────────────────────────────┐
│  Trade Services: matching, credits,   │
│  reputation, verification, safety,    │
│  algorithmic loops (DFS cycle detect) │
└───────────────────────────────────────┘
```

---

## 🛡️ Security & Privacy

- **On-device by default**: Object detection runs locally via ONNX Runtime — no photo leaves your device unless you explicitly opt in
- **Encrypted tokens**: Marketplace API credentials stored encrypted on the backend
- **EXIF stripping**: Location and metadata removed from uploaded images
- **Audit logging**: Every action traced with correlation IDs
- **Rate limiting**: 60 req/min global, 10 req/min for analysis endpoints
- **Request size caps**: 10MB maximum to prevent abuse
- **Trade safety**: No self-trades, credit balance validation, pending-listing locking

See [test_security.py](server/tests/test_security.py) for our security test coverage.

---

## 🧠 ADHD-First Design Principles

Every screen follows these rules:

1. **One primary action** — no decision paralysis
2. **Visible progress** — always know how far you've come
3. **Large touch targets** — minimum 48dp for all buttons
4. **Undo everywhere** — mistakes are reversible
5. **Energy modes** — "I have 2 minutes" / "I have 10 minutes" / "I can list today"
6. **"I'm stuck" rescue** — algorithm suggests donate, recycle, trade, or "not today" based on value and effort

---

## 🏆 Why DECLuTTER AI?

| | DECLuTTER AI | Tody | Decluttr | General AI Apps |
|---|---|---|---|---|
| **Open Source** | ✅ MIT | ❌ Paid | ❌ | ⚠️ Rare |
| **ADHD-Focused** | ✅ Core mission | ❌ | ❌ | ❌ |
| **On-Device Detection** | ✅ ONNX | ❌ N/A | ❌ | ❌ Cloud-only |
| **Resale Valuation** | ✅ Built-in (6K+ items) | ❌ | ✅ | ❌ |
| **Local Barter Trading** | ✅ No cash needed | ❌ | ❌ | ❌ |
| **Privacy-First** | ✅ Default | ⚠️ | ❌ | ❌ |
| **Free** | ✅ | ❌ Paid | ❌ Takes cut | ⚠️ Freemium |

---

## 🗺️ Roadmap

### Completed ✅
- [x] Photo capture + on-device detection
- [x] Item grouping + decision cards (Keep/Donate/Trash/Relocate/Maybe)
- [x] Valuation + session summary
- [x] Security hardening + test coverage (170 tests)
- [x] **Phase 1 — Barter/Trade Marketplace:**
  - [x] Trade credit system (non-monetary credits)
  - [x] Trade listings + nearby discovery
  - [x] Propose / accept / decline trade flow
  - [x] ND-friendly UX (templates, checklists, rules)
  - [x] Reputation + review system
  - [x] Safety checklists (10 categories)
  - [x] Verified trader badges
  - [x] Algorithmic multi-party trade matching
  - [x] Expanded valuation engine (4,018 → 6,072 items)
  - [x] Flutter trade UI (browse, list, match, wallet)

### In Progress / Next
- [ ] SQLite persistence for session history (drift)
- [ ] Riverpod state management
- [ ] AI-powered item analysis (backend vision model)
- [ ] eBay marketplace integration
- [ ] Listing draft generation
- [ ] Public listing pages + buyer-agent endpoints (MCP/A2A)
- [ ] iOS/Android app store release

See [IMPLEMENTATION_PLAN_2026.md](IMPLEMENTATION_PLAN_2026.md) and [docs/plans/2026-04-28-barter-marketplace.md](docs/plans/2026-04-28-barter-marketplace.md) for detailed specs.

---

## 🤝 Contributing

We love contributors! Whether you're fixing a bug, adding a feature, improving docs, or sharing feedback — you're welcome here.

- 📖 [Contributing Guide](CONTRIBUTING.md)
- 🛡️ [Code of Conduct](CODE_OF_CONDUCT.md)
- 🐛 [Report a Bug](https://github.com/KyaniteLabs/DECLuTTER-AI/issues/new?template=bug_report.md)
- 💡 [Request a Feature](https://github.com/KyaniteLabs/DECLuTTER-AI/issues/new?template=feature_request.md)

**Looking for your first contribution?** Check issues labeled [`good first issue`](https://github.com/KyaniteLabs/DECLuTTER-AI/labels/good%20first%20issue).

---

## 📜 License

[MIT](LICENSE) © Simon Gonzalez de Cruz

---

## 🙏 Acknowledgments

Built with ❤️ for the ADHD and neurodivergent community. Special thanks to everyone who shares their declutter journey and helps us build something truly useful.

> *"The goal isn't perfection — it's a little more space to breathe."*
