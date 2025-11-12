# Contributing Translations to CommunityCircle 🌍

Thank you for your interest in translating CommunityCircle! Your contribution will help make mutual aid accessible to more communities worldwide.

## Table of Contents

- [Quick Start](#quick-start)
- [Translation Structure](#translation-structure)
- [Step-by-Step Guide](#step-by-step-guide)
- [Translation Guidelines](#translation-guidelines)
- [Testing Your Translation](#testing-your-translation)
- [Submitting Your Translation](#submitting-your-translation)
- [Maintaining Translations](#maintaining-translations)
- [FAQ](#faq)

---

## Quick Start

**Time Required:** 2-4 hours for a complete translation
**Prerequisites:** None! Just fluency in your target language
**Tools Needed:** Text editor (VS Code, Sublime, or even Notepad)

### What You'll Be Translating

CommunityCircle has **6 translation files** organized by feature:

1. **common.json** - Navigation, buttons, errors (most important!)
2. **auth.json** - Login, signup, profile
3. **posts.json** - Needs & Offers board
4. **shifts.json** - Volunteer scheduling
5. **resources.json** - Resource finder
6. **dashboard.json** - User dashboard

---

## Translation Structure

Translation files are located in:
```
frontend/public/locales/{language-code}/
```

For example, Spanish translations go in:
```
frontend/public/locales/es/
  common.json
  auth.json
  posts.json
  shifts.json
  resources.json
  dashboard.json
```

### Language Codes

Use [ISO 639-1](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) two-letter codes:

- **es** - Spanish (Español)
- **fr** - French (Français)
- **ar** - Arabic (العربية)
- **zh** - Chinese (中文)
- **hi** - Hindi (हिन्दी)
- **pt** - Portuguese (Português)
- **de** - German (Deutsch)
- **ja** - Japanese (日本語)
- **ru** - Russian (Русский)
- **ko** - Korean (한국어)

---

## Step-by-Step Guide

### Step 1: Choose Your Language

Pick a language you're fluent in. Check if it already exists in `frontend/public/locales/`. If not, you're starting fresh!

### Step 2: Create Language Directory

Create a new folder for your language:
```bash
mkdir -p frontend/public/locales/{your-language-code}
```

Example for Spanish:
```bash
mkdir -p frontend/public/locales/es
```

### Step 3: Copy English Templates

Copy all English translation files to your language folder:
```bash
cp frontend/public/locales/en/* frontend/public/locales/es/
```

### Step 4: Translate JSON Files

Open each file and translate the **values** (keep the keys in English):

#### ❌ WRONG - Don't do this:
```json
{
  "navegación": {
    "casa": "Casa",
    "publicaciones": "Publicaciones"
  }
}
```

#### ✅ CORRECT - Do this:
```json
{
  "navigation": {
    "home": "Casa",
    "posts": "Publicaciones"
  }
}
```

**Important:**
- ✅ Translate the **values** (right side)
- ❌ **Never** translate the **keys** (left side)
- ✅ Keep all `{{variables}}` exactly as they are
- ✅ Preserve HTML tags like `<strong>`, `<br>`
- ✅ Keep punctuation appropriate for your language

### Step 5: Handle Variables

Many strings contain variables in `{{double braces}}`. Keep them exactly as-is:

**English:**
```json
"welcome": {
  "title": "Welcome, {{name}}!"
}
```

**Spanish:**
```json
"welcome": {
  "title": "¡Bienvenido, {{name}}!"
}
```

**French:**
```json
"welcome": {
  "title": "Bienvenue, {{name}} !"
}
```

### Step 6: Handle Pluralization

Some languages have different plural rules. We use the `count` variable:

**English:**
```json
"resultsCount": "{{count}} resources found"
```

For languages with complex plurals, i18next supports:
```json
"resultsCount": "{{count}} recurso encontrado",
"resultsCount_plural": "{{count}} recursos encontrados"
```

### Step 7: Register Your Language

Add your language to `frontend/src/i18n/config.js`:

```javascript
export const supportedLanguages = [
  { code: 'en', name: 'English', nativeName: 'English' },
  { code: 'es', name: 'Spanish', nativeName: 'Español' },  // ← Add this line
];
```

For right-to-left languages (Arabic, Hebrew, etc.):
```javascript
{ code: 'ar', name: 'Arabic', nativeName: 'العربية', dir: 'rtl' },
```

---

## Translation Guidelines

### 1. Context Matters

Understand what you're translating. If unsure, look at the English version in the actual app or ask in the GitHub issue.

### 2. Cultural Adaptation (Localization)

Don't just translate word-for-word. Adapt for your culture:

**English:** "Sign up"
**Spanish (Spain):** "Registrarse"
**Spanish (Latin America):** "Crear cuenta"

### 3. Formality Level

Choose appropriate formality:
- **French:** Use "vous" (formal) for general audience
- **Spanish:** Use "tú" (informal) for community feel
- **German:** Use "Sie" (formal) for professional contexts

Be consistent throughout your translation.

### 4. Keep It Concise

UI space is limited. Keep translations similar in length to English when possible.

**English:** "Get Directions" (14 chars)
**Spanish:** "Ver Mapa" (8 chars) ✅ Good
**Spanish:** "Obtener Direcciones Completas" (29 chars) ❌ Too long

### 5. Common Terms

Create a consistency guide for recurring terms:

| English | Spanish | French | Arabic |
|---------|---------|--------|--------|
| Post | Publicación | Publication | منشور |
| Need | Necesidad | Besoin | احتياج |
| Offer | Oferta | Offre | عرض |
| Shift | Turno | Créneau | نوبة |
| Resource | Recurso | Ressource | مورد |

### 6. Special Characters

Ensure your text editor saves as UTF-8 to preserve special characters:
- Spanish: á, é, í, ó, ú, ñ, ¿, ¡
- French: à, â, ç, é, è, ê, ë, î, ï, ô, û, ù
- German: ä, ö, ü, ß
- Arabic, Chinese, Japanese, etc.

---

## Testing Your Translation

### Option 1: Run Locally (Recommended)

1. **Install dependencies:**
```bash
cd frontend
npm install
```

2. **Start the dev server:**
```bash
npm run dev
```

3. **Change language:**
   - Open the app in your browser
   - Click the globe icon 🌐
   - Select your language
   - Navigate through the app to test

### Option 2: Visual Inspection

Open your JSON files and verify:
- ✅ No syntax errors (matching brackets, commas)
- ✅ All keys present (same as English version)
- ✅ Variables preserved: `{{name}}`, `{{count}}`, etc.
- ✅ No broken HTML tags

### Option 3: JSON Validator

Use [JSONLint](https://jsonlint.com/) to validate your files:
1. Copy your translation file content
2. Paste into JSONLint
3. Click "Validate JSON"
4. Fix any errors shown

---

## Submitting Your Translation

### Step 1: Fork the Repository

Click "Fork" on the [GitHub repository](https://github.com/Pastorsimon1798/MutualAidApp).

### Step 2: Create a Branch

```bash
git checkout -b add-spanish-translation
```

Use a descriptive name like:
- `add-spanish-translation`
- `add-french-translation`
- `update-german-translation`

### Step 3: Commit Your Changes

```bash
git add frontend/public/locales/es/
git add frontend/src/i18n/config.js
git commit -m "Add Spanish (Español) translation"
```

### Step 4: Push and Create Pull Request

```bash
git push origin add-spanish-translation
```

Then create a Pull Request on GitHub with:
- **Title:** "Add [Language] translation"
- **Description:**
  ```
  ## Translation Details
  - **Language:** Spanish (Español)
  - **Language Code:** es
  - **Translator:** @yourusername
  - **Files Translated:** All 6 files (100% complete)
  - **Tested:** Yes / No

  ## Notes
  - Used Latin American Spanish
  - Informal "tú" for community feel
  - All UI elements tested in browser
  ```

---

## Maintaining Translations

### When New Features Are Added

When CommunityCircle adds new features, English translations will be updated. To keep your translation current:

1. **Watch for notifications** about new translation keys
2. **Compare with English** to see what's new
3. **Add missing keys** to your language files
4. **Submit update PR**

### Translation Completeness

You can check completeness:
```bash
# Count keys in English
cat frontend/public/locales/en/*.json | grep -o '": "' | wc -l

# Count keys in your language
cat frontend/public/locales/es/*.json | grep -o '": "' | wc -l
```

Both numbers should match!

---

## FAQ

### Q: How long does a full translation take?

**A:** 2-4 hours for a fluent speaker. You can also translate files one at a time!

### Q: Can I translate just one file?

**A:** Yes! `common.json` alone covers 60% of the app. Start there.

### Q: What if I make a mistake?

**A:** No problem! Reviewers will help, and you can always update your PR.

### Q: Can two people work on the same language?

**A:** Coordinate in GitHub Issues to avoid duplicate work. One person per language works best.

### Q: What about regional variants (e.g., Brazilian vs. European Portuguese)?

**A:** Start with the most widely understood variant. Later, we can add:
- `pt` - Portuguese (general)
- `pt-BR` - Brazilian Portuguese
- `pt-PT` - European Portuguese

### Q: How do I translate month/day names?

**A:** These are in `common.json` under `time.daysOfWeek` and `time.months`.

### Q: Should I translate brand names?

**A:** No. Keep "CommunityCircle" as-is in all languages.

### Q: What about measurement units (km, miles)?

**A:** Keep the units from the English version. We'll add user preferences later.

### Q: Can I use translation tools like Google Translate?

**A:** Only as a starting point. **Always** review and correct machine translations for:
- Natural phrasing
- Cultural appropriateness
- UI context
- Consistency

Machine translation alone is **not acceptable**.

---

## Translation Checklist

Before submitting, verify:

- [ ] All 6 JSON files created for your language
- [ ] All keys match the English version (no missing or extra keys)
- [ ] All values translated (no English strings left)
- [ ] Variables preserved: `{{name}}`, `{{count}}`, etc.
- [ ] HTML tags preserved: `<strong>`, `<br>`, etc.
- [ ] JSON syntax valid (no syntax errors)
- [ ] Language added to `frontend/src/i18n/config.js`
- [ ] Language code correct (ISO 639-1)
- [ ] Native name correct (e.g., "Español" not "Spanish")
- [ ] RTL direction set if applicable (Arabic, Hebrew, etc.)
- [ ] Tested in browser (if possible)
- [ ] Consistent terminology throughout
- [ ] Appropriate formality level
- [ ] Cultural adaptations made where needed

---

## Translation File Templates

### common.json
**Priority:** ⭐⭐⭐ (Highest - covers navigation, buttons, errors)
**Keys:** ~80
**Estimated Time:** 30-45 minutes

### auth.json
**Priority:** ⭐⭐ (Medium - login/signup screens)
**Keys:** ~40
**Estimated Time:** 15-20 minutes

### posts.json
**Priority:** ⭐⭐⭐ (High - main community feature)
**Keys:** ~60
**Estimated Time:** 30-40 minutes

### shifts.json
**Priority:** ⭐⭐ (Medium - volunteer scheduling)
**Keys:** ~50
**Estimated Time:** 25-35 minutes

### resources.json
**Priority:** ⭐⭐⭐ (High - resource finder)
**Keys:** ~90
**Estimated Time:** 45-60 minutes

### dashboard.json
**Priority:** ⭐ (Low - quick actions and stats)
**Keys:** ~30
**Estimated Time:** 15-20 minutes

---

## Getting Help

- **Questions?** Open a [GitHub Discussion](https://github.com/Pastorsimon1798/MutualAidApp/discussions)
- **Found a typo in English?** Open an issue!
- **Need context?** Comment on the translation PR
- **Stuck on a phrase?** Ask in the pull request

---

## Thank You! 🙏

Your translation helps make mutual aid accessible to more communities. Every language added removes a barrier to community care.

**Current Translation Status:**
- ✅ English (en) - Complete
- ⏳ Your language - In progress!

---

## Language-Specific Tips

### Spanish (Español)

- Use "tú" for informal community feel
- Latin American vs. Spain variants: Document which you chose
- Common terms:
  - "Post" → "Publicación"
  - "Need" → "Necesidad"
  - "Offer" → "Oferta"

### French (Français)

- Use "vous" for general audience
- Watch for gendered nouns
- Common terms:
  - "Post" → "Publication"
  - "Need" → "Besoin"
  - "Offer" → "Offre"

### Arabic (العربية)

- Set `dir: 'rtl'` in config
- Right-align text
- Consider Egyptian Arabic vs. Modern Standard Arabic
- Test UI layout with RTL

### Chinese (中文)

- Simplified vs. Traditional: Document which you chose
- Consider mainland China vs. Taiwan variants
- Keep sentences concise for UI space

### Portuguese (Português)

- Brazilian vs. European: Document which you chose
- Use "você" for general audience
- Watch for formal vs. informal

---

## Credits

Translations contributed by:
- 🇺🇸 English - CommunityCircle Team
- (Your name will be here!)

---

**Last Updated:** November 2024
**Translation System Version:** 1.0
**Total Translatable Strings:** ~350
