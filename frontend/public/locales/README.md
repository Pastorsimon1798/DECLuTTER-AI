# Translation Files

This directory contains all translation files for CommunityCircle.

## Structure

```
locales/
  en/           ← English (base language)
    common.json
    auth.json
    posts.json
    shifts.json
    resources.json
    dashboard.json
  es/           ← Spanish (example)
  fr/           ← French (example)
  ...           ← Add your language here!
```

## Adding a New Language

1. **Create a directory** with your language code (e.g., `es` for Spanish)
2. **Copy all files** from the `en/` directory
3. **Translate the values** (not the keys!)
4. **Register your language** in `frontend/src/i18n/config.js`

## Full Guide

See **[CONTRIBUTING_TRANSLATIONS.md](../../../CONTRIBUTING_TRANSLATIONS.md)** for complete instructions.

## Language Codes

Use ISO 639-1 two-letter codes:
- `es` - Spanish
- `fr` - French
- `de` - German
- `zh` - Chinese
- `ar` - Arabic
- `pt` - Portuguese
- `ja` - Japanese
- `ru` - Russian
- `hi` - Hindi
- `ko` - Korean

## File Descriptions

| File | Description | Priority |
|------|-------------|----------|
| `common.json` | Navigation, buttons, common UI elements | ⭐⭐⭐ High |
| `auth.json` | Login, signup, profile pages | ⭐⭐ Medium |
| `posts.json` | Needs & Offers board | ⭐⭐⭐ High |
| `shifts.json` | Volunteer scheduling | ⭐⭐ Medium |
| `resources.json` | Resource finder | ⭐⭐⭐ High |
| `dashboard.json` | User dashboard | ⭐ Low |

## Quick Start

```bash
# 1. Copy English templates
cp -r en/ es/

# 2. Translate all JSON files in es/

# 3. Test your translation
cd ../../../
npm run dev
```

## Need Help?

- 📖 [Full Translation Guide](../../../CONTRIBUTING_TRANSLATIONS.md)
- 💬 [GitHub Discussions](https://github.com/Pastorsimon1798/MutualAidApp/discussions)
- 🐛 [Report Issues](https://github.com/Pastorsimon1798/MutualAidApp/issues)

## Current Languages

- ✅ **English (en)** - Complete
- ⏳ **Your language** - Waiting for you!

Thank you for helping make CommunityCircle accessible to more people! 🌍
