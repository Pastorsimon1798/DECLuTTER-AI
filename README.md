# DECLuTTER AI 🧠✨

> *The ADHD-friendly decluttering assistant. Snap a photo, see your items grouped, and decide keep / donate / trash / relocate / maybe in a 10-minute sprint.*

[![App CI](https://github.com/Pastorsimon1798/DECLuTTER-AI/actions/workflows/flutter-test.yml/badge.svg)](https://github.com/Pastorsimon1798/DECLuTTER-AI/actions)
[![Server CI](https://github.com/Pastorsimon1798/DECLuTTER-AI/actions/workflows/server-test.yml/badge.svg)](https://github.com/Pastorsimon1798/DECLuTTER-AI/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Flutter Version](https://img.shields.io/badge/Flutter-3.19+-blue.svg)](https://flutter.dev)
[![Python Version](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)

---

## 🎯 Why DECLuTTER AI?

Adults with ADHD often feel **paralyzed by clutter**. Generic apps identify objects but don't help you *decide what to do with them*.

**DECLuTTER AI** converts a messy photo into simple, time-boxed actions with neurodivergent-friendly design:
- Large buttons, minimal text, visible progress
- Undo everything — no judgment
- Haptic feedback on every decision
- "Not today" escape route on every screen
- Shame-free language (never "mess," "junk," or "lazy")

---

## ✨ Features

| Feature | Description |
|---|---|
| 📸 **One-Tap Capture** | Take a photo of any cluttered zone — desk, closet, dresser, shelf |
| 🏷️ **Smart Grouping** | On-device AI groups items by category: cables, books, clothing, electronics |
| ⏱️ **10-Min Sprint Timer** | ADHD-friendly focus sessions with celebratory completion |
| 💰 **Resale Valuation** | See "Money on the Table" estimates for sellable items |
| 📝 **One-Tap Decisions** | Keep · Donate · Trash · Relocate · Maybe — with undo and notes |
| 📊 **CSV Export** | Track your declutter progress over time |
| 🔒 **Privacy-First** | All analysis happens on-device by default |
| 🌐 **Shareable Listings** | Generate public listing pages for resale items |

---

## 🖼️ Screenshots

> *Demo GIF and screenshots coming soon — follow [Discussions](https://github.com/Pastorsimon1798/DECLuTTER-AI/discussions) for updates!*

---

## 🚀 Quick Start

### Flutter App

```bash
# 1. Install Flutter 3.19+ from https://docs.flutter.dev/get-started/install

# 2. Clone and setup
git clone https://github.com/Pastorsimon1798/DECLuTTER-AI.git
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

# Backend
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
└─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
┌───────────────┐       ┌───────────────┐
│  FastAPI      │       │  Local SQLite │
│  Backend      │◄─────►│  (sessions)   │
│  (Python)     │       │               │
└───────────────┘       └───────────────┘
```

---

## 🛡️ Security & Privacy

- **On-device by default**: Object detection runs locally via ONNX Runtime — no photo leaves your device unless you explicitly opt in
- **Encrypted tokens**: Marketplace API credentials stored encrypted on the backend
- **EXIF stripping**: Location and metadata removed from uploaded images
- **Audit logging**: Every action traced with correlation IDs
- **Rate limiting**: 60 req/min global, 10 req/min for analysis endpoints
- **Request size caps**: 10MB maximum to prevent abuse

See [test_security.py](server/tests/test_security.py) for our security test coverage.

---

## 🧠 ADHD-First Design Principles

Every screen follows these rules:

1. **One primary action** — no decision paralysis
2. **Visible progress** — always know how far you've come
3. **Large touch targets** — minimum 48dp for all buttons
4. **Undo everywhere** — mistakes are reversible
5. **Energy modes** — "I have 2 minutes" / "I have 10 minutes" / "I can list today"
6. **"I'm stuck" rescue** — algorithm suggests donate, recycle, or "not today" based on value and effort

---

## 🗺️ Roadmap

- [x] Photo capture + on-device detection
- [x] Item grouping + decision cards (Keep/Donate/Trash/Relocate/Maybe)
- [x] Valuation + session summary
- [x] Security hardening + test coverage
- [ ] SQLite persistence for session history
- [ ] Riverpod state management
- [ ] AI-powered item analysis (backend vision model)
- [ ] eBay marketplace integration
- [ ] Listing draft generation
- [ ] Public listing pages + buyer-agent endpoints (MCP/A2A)
- [ ] iOS/Android app store release

---

## 🤝 Contributing

We love contributors! Whether you're fixing a bug, adding a feature, improving docs, or sharing feedback — you're welcome here.

- 📖 [Contributing Guide](CONTRIBUTING.md)
- 🛡️ [Code of Conduct](CODE_OF_CONDUCT.md)
- 🐛 [Report a Bug](https://github.com/Pastorsimon1798/DECLuTTER-AI/issues/new?template=bug_report.md)
- 💡 [Request a Feature](https://github.com/Pastorsimon1798/DECLuTTER-AI/issues/new?template=feature_request.md)

**Looking for your first contribution?** Check issues labeled [`good first issue`](https://github.com/Pastorsimon1798/DECLuTTER-AI/labels/good%20first%20issue).

---

## 📜 License

[MIT](LICENSE) © Simon Gonzalez de Cruz

---

## 🙏 Acknowledgments

Built with ❤️ for the ADHD and neurodivergent community. Special thanks to everyone who shares their declutter journey and helps us build something truly useful.

> *"The goal isn't perfection — it's a little more space to breathe."*
