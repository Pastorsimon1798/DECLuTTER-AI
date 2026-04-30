import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import HttpBackend from 'i18next-http-backend';

/**
 * i18next Configuration for CommunityCircle
 *
 * This file configures internationalization for the application.
 * Translation files are loaded from /public/locales/{language}/{namespace}.json
 *
 * Supported languages are defined in supportedLanguages below.
 * To add a new language, add translation files and include the language code here.
 */

// List of supported languages
// Add new language codes here when translations are available
export const supportedLanguages = [
  { code: 'en', name: 'English', nativeName: 'English' },
  { code: 'es', name: 'Spanish', nativeName: 'Español' },
  { code: 'fr', name: 'French', nativeName: 'Français' },
  { code: 'de', name: 'German', nativeName: 'Deutsch' },
  { code: 'ar', name: 'Arabic', nativeName: 'العربية', dir: 'rtl' },
  { code: 'hi', name: 'Hindi', nativeName: 'हिन्दी' },
  { code: 'zh-CN', name: 'Chinese (Simplified)', nativeName: '简体中文' },
  { code: 'ja', name: 'Japanese', nativeName: '日本語' },
  { code: 'ko', name: 'Korean', nativeName: '한국어' },
  { code: 'pt-BR', name: 'Portuguese (Brazil)', nativeName: 'Português (Brasil)' },
  { code: 'ru', name: 'Russian', nativeName: 'Русский' },
  { code: 'vi', name: 'Vietnamese', nativeName: 'Tiếng Việt' },
  { code: 'tl', name: 'Tagalog', nativeName: 'Tagalog' },
  { code: 'ht', name: 'Haitian Creole', nativeName: 'Kreyòl Ayisyen' },
];

// Available translation namespaces
export const namespaces = [
  'common',
  'auth',
  'posts',
  'shifts',
  'resources',
  'dashboard',
];

// Preload all namespaces
export const preloadNamespaces = namespaces;

i18n
  // Load translations using http backend
  .use(HttpBackend)
  // Detect user language
  .use(LanguageDetector)
  // Pass the i18n instance to react-i18next
  .use(initReactI18next)
  // Initialize i18next
  .init({
    // Default language
    fallbackLng: 'en',

    // Supported languages
    supportedLngs: supportedLanguages.map(lang => lang.code),

    // Available namespaces
    ns: namespaces,
    defaultNS: 'common',

    // Language detection options
    detection: {
      // Order of detection methods
      order: ['localStorage', 'navigator', 'htmlTag'],
      // Cache user language selection
      caches: ['localStorage'],
      lookupLocalStorage: 'i18nextLng',
    },

    // Backend options for loading translations
    backend: {
      loadPath: '/locales/{{lng}}/{{ns}}.json',
    },

    // React i18next options
    react: {
      useSuspense: true, // Use React Suspense for loading translations
      bindI18n: 'languageChanged',
      bindI18nStore: '',
      transEmptyNodeValue: '',
      transSupportBasicHtmlNodes: true,
      transKeepBasicHtmlNodesFor: ['br', 'strong', 'i', 'p'],
    },

    // Interpolation options
    interpolation: {
      escapeValue: false, // React already escapes values
      formatSeparator: ',',
    },

    // Debug mode (set to true during development if needed)
    debug: true, // Enable to see translation loading in console

    // Show keys if translation is missing (helpful for development)
    saveMissing: false,
    missingKeyHandler: (lng, ns, key) => {
      if (process.env.NODE_ENV === 'development') {
        console.warn(`Missing translation: ${lng}:${ns}:${key}`);
      }
    },
  });

export default i18n;
