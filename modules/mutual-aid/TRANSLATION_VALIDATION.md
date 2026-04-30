# Translation Validation Guide for Native Speakers

Thank you for helping validate MutualCircle translations! This guide will help you review and improve translations for your language.

## 🎯 Purpose

All translations marked as **ALPHA** were created automatically and require validation from native speakers. Your help ensures translations are:
- **Natural** and idiomatic
- **Culturally appropriate**
- **Technically accurate**
- **Contextually correct**

## 🌍 Languages Needing Validation

### Tier 1 - Recently Added (Priority: URGENT)
- 🇮🇳 **Hindi (hi)** - 602M speakers
- 🇫🇷 **French (fr)** - 280M speakers
- 🇩🇪 **German (de)** - 134M speakers
- 🇷🇺 **Russian (ru)** - 258M speakers
- 🇯🇵 **Japanese (ja)** - 125M speakers
- 🇰🇷 **Korean (ko)** - 81M speakers

### Tier 2 - Previously Added
- 🇨🇳 **Mandarin Chinese (zh-CN)** - 1.1B speakers
- 🇸🇦 **Arabic (ar)** - 274M speakers
- 🇻🇳 **Vietnamese (vi)** - 85M speakers
- 🇵🇭 **Tagalog (tl)** - 82M speakers
- 🇭🇹 **Haitian Creole (ht)** - 12M speakers
- 🇧🇷 **Brazilian Portuguese (pt-BR)** - 215M speakers

### Production Ready
- 🇪🇸 **Spanish (es)** - No validation needed

## 📋 How to Validate Translations

### Step 1: Find Your Language

Navigate to: `frontend/public/locales/{language-code}/`

Each language has 6 translation files:
- `common.json` - Core app strings, navigation, actions, forms
- `auth.json` - Login, registration, profile management
- `posts.json` - Community posts, needs, offers
- `dashboard.json` - Dashboard interface and statistics
- `shifts.json` - Volunteer shift scheduling
- `resources.json` - Resource locator (food banks, shelters, etc.)

### Step 2: Review Translation Files

Open each JSON file and check for:

#### ✅ What to Look For

**1. Natural Language**
- Does it sound like something a native speaker would say?
- Is it conversational where appropriate, formal where needed?

**2. Cultural Appropriateness**
- Are idioms translated correctly (not literally)?
- Do examples make sense in your culture?
- Are honorifics and forms of address appropriate?

**3. Technical Accuracy**
- Are technical terms correct?
- Is terminology consistent across files?
- Are UI labels clear and concise?

**4. Context**
- Does the translation fit the context?
- Are gender-neutral options used where appropriate?
- Do plurals work correctly with `{{count}}` variables?

**5. Formatting**
- Are dates/times formatted correctly for your region?
- Are numbers and currency formatted appropriately?
- Is punctuation correct?

#### ❌ Common Issues to Fix

- Literal translations of idioms (e.g., "it's raining cats and dogs")
- Overly formal/informal tone inconsistencies
- Incorrect technical terminology
- Missing cultural context
- Awkward phrasing
- Gender assumptions
- Incorrect pluralization
- Wrong date/time formats

### Step 3: Testing Checklist

For each file, verify:

- [ ] All strings are present (compare with English `en/` folder)
- [ ] No JSON syntax errors
- [ ] Variable placeholders preserved (e.g., `{{name}}`, `{{count}}`)
- [ ] Consistent terminology across all files
- [ ] Appropriate formality level
- [ ] No grammatical errors
- [ ] Natural word order
- [ ] Culturally appropriate examples

### Step 4: Document Issues

When you find problems, note:
1. **File**: Which JSON file (e.g., `posts.json`)
2. **Key**: The JSON key path (e.g., `create.titleLabel`)
3. **Current**: The existing translation
4. **Suggested**: Your improved translation
5. **Reason**: Why the change is needed

**Example:**
```
File: posts.json
Key: create.titleLabel
Current: "Titre de poste"
Suggested: "Titre de la publication"
Reason: "Poste" means job position, not post/publication
```

### Step 5: Submit Your Feedback

#### Option A: Create an Issue (Easier)
1. Go to GitHub Issues
2. Create new issue with title: `[Translation] {Language} - {Brief description}`
3. Use this template:

```markdown
## Language
{Language name} ({code})

## Issues Found

### File: common.json
- **Key**: `navigation.home`
- **Current**: "..."
- **Suggested**: "..."
- **Reason**: ...

### File: auth.json
...

## Additional Notes
...
```

#### Option B: Submit a Pull Request (Preferred)
1. Fork the repository
2. Create a branch: `fix/translations-{language-code}`
3. Edit the translation files directly
4. Commit with message: `fix(i18n): improve {language} translations`
5. Submit pull request with description of changes

## 🎨 Style Guidelines

### Tone and Voice

**Friendly but Professional**
- Use conversational language where appropriate
- Be helpful and encouraging
- Avoid jargon unless necessary
- Keep error messages constructive

**Example (English):**
- ❌ "Invalid input detected in form submission"
- ✅ "Please check your information and try again"

### Consistency

**Use consistent terms for:**
- Button actions (Submit, Save, Cancel)
- Navigation items (Home, Dashboard, Profile)
- Status labels (Active, Pending, Completed)
- User roles (Volunteer, Organizer, Member)

**Create a glossary for your language:**
- Maintain consistency across all files
- Document technical terms
- Note regional variations

### Accessibility

**Keep translations:**
- Clear and concise
- Easy to scan
- Screen-reader friendly
- Inclusive and respectful

## 🌏 Regional Variations

If your language has significant regional differences, please note:

**French:**
- European French vs. Canadian French vs. African French
- Example: "courriel" (CA) vs. "email" (FR)

**Spanish:**
- Iberian Spanish vs. Latin American Spanish
- Example: "ordenador" (ES) vs. "computadora" (LATAM)

**Portuguese:**
- European Portuguese vs. Brazilian Portuguese (already separated)

**Arabic:**
- Modern Standard Arabic vs. dialectical variations

**Chinese:**
- Simplified (zh-CN) vs. Traditional (zh-TW)

**Document these differences in your feedback!**

## 📞 Getting Help

- **GitHub Issues**: https://github.com/anthropics/mutualcircle/issues
- **Email**: translations@mutualcircle.org
- **Discussion**: Check the repository Discussions tab

## 🏆 Recognition

All contributors will be:
- Listed in CONTRIBUTORS.md
- Credited in release notes
- Thanked in the README
- Making mutual aid accessible to millions!

## ⚖️ Translation Ethics

Please ensure translations:
- **Respect** all communities and identities
- **Include** marginalized groups
- **Avoid** stereotypes and assumptions
- **Consider** accessibility needs
- **Maintain** the platform's values of mutual aid and community support

## 📚 Resources

**Translation Tools:**
- [Google Translate](https://translate.google.com/) - Quick reference only
- [DeepL](https://www.deepl.com/) - Higher quality automatic translation
- Language-specific dictionaries and style guides
- **Native speaker communities** - Always the best resource!

**i18n Technical Resources:**
- [i18next Documentation](https://www.i18next.com/)
- [ICU Message Format](https://unicode-org.github.io/icu/userguide/format_parse/messages/)
- [CLDR Plurals](http://cldr.unicode.org/index/cldr-spec/plural-rules)

## ✨ Thank You!

Your contribution helps make mutual aid accessible to people worldwide. Every improvement you make helps someone in need connect with someone who can help.

**Together, we build stronger communities!** 🤝

---

*Last Updated: 2025-11-12*
*MutualCircle Translation Team*
