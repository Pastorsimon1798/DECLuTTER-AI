# Contributing to DECLuTTER AI

Thank you for your interest in making DECLuTTER AI better! This document will help you get started.

## Code of Conduct

This project adheres to a standard of respectful, inclusive collaboration. Please read our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before participating.

## How Can I Contribute?

### Reporting Bugs

- Check if the issue already exists in [Issues](https://github.com/Pastorsimon1798/DECLuTTER-AI/issues).
- Open a new issue using the **Bug Report** template.
- Include steps to reproduce, expected vs. actual behavior, and your environment (OS, Flutter version, device).

### Suggesting Features

- Open a new issue using the **Feature Request** template.
- Explain the problem you're solving and why it matters for ADHD/neurodivergent users.

### Pull Requests

1. Fork the repository and create your branch from `main`.
2. If you've changed APIs, update the relevant documentation.
3. Ensure your code follows the existing style.
4. Add tests for Flutter features (`flutter test`) and backend features (`pytest`).
5. Make sure all tests pass.
6. Fill out the Pull Request template completely.

## Development Setup

### Flutter App

```bash
cd app
flutter pub get
flutter analyze
flutter test
```

### Backend

```bash
cd server
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Style Guidelines

- **Flutter**: Follow the official [Dart style guide](https://dart.dev/effective-dart/style).
- **Python**: Follow PEP 8. Run `ruff check .` before committing.
- **Commit messages**: Use conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`).

## Areas Where Help is Needed

- 🎨 **UI/UX improvements** for ADHD accessibility (especially trade flow ND-friction reduction)
- 🌍 **Internationalization (i18n)** — Spanish, French, and other language support
- 📱 **iOS-specific optimizations** and App Store prep
- 🧪 **Flutter widget tests** for trade screens (`BrowseTradesScreen`, `TradeHubScreen`, etc.)
- 🔄 **Phase 2 trade features** — shipping integration, nonprofit partnerships, distributed moderation
- 🧠 **ONNX Runtime migration** — replace TFLite as default inference backend
- 🗄️ **Drift/SQLite persistence** — session history and offline-first data
- 📖 **Documentation and tutorials** — especially trade marketplace user guides
- 🌐 **Landing page and marketing content** — update `docs/index.html` with new features

## Questions?

Feel free to open a [Discussion](https://github.com/Pastorsimon1798/DECLuTTER-AI/discussions) or reach out in an issue.

Thank you for helping make decluttering accessible to everyone! 🧠✨
