import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { supportedLanguages } from '../i18n/config';
import { Globe } from 'lucide-react';

/**
 * Language Selector Component
 *
 * Allows users to change the application language.
 * Supports all languages defined in i18n/config.js
 */
export default function LanguageSelector({ variant = 'dropdown' }) {
  const { i18n } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const [currentLanguage, setCurrentLanguage] = useState(i18n.language);

  useEffect(() => {
    setCurrentLanguage(i18n.language);
  }, [i18n.language]);

  const changeLanguage = (langCode) => {
    i18n.changeLanguage(langCode);
    setCurrentLanguage(langCode);
    setIsOpen(false);

    // Set HTML lang attribute
    document.documentElement.lang = langCode;

    // Set direction for RTL languages
    const language = supportedLanguages.find(l => l.code === langCode);
    document.documentElement.dir = language?.dir || 'ltr';
  };

  const getCurrentLanguageName = () => {
    const lang = supportedLanguages.find(l => l.code === currentLanguage);
    return lang?.nativeName || lang?.name || currentLanguage;
  };

  if (variant === 'inline') {
    // Inline buttons for each language (good for settings pages)
    return (
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          <Globe className="inline mr-2" size={16} />
          Language / Idioma / Langue
        </label>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {supportedLanguages.map((lang) => (
            <button
              key={lang.code}
              onClick={() => changeLanguage(lang.code)}
              className={`px-4 py-2 rounded-lg border transition-colors ${
                currentLanguage === lang.code
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              {lang.nativeName}
            </button>
          ))}
        </div>
      </div>
    );
  }

  // Dropdown variant (default, good for navigation bars)
  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
        aria-label="Select language"
      >
        <Globe size={20} />
        <span className="hidden md:inline">{getCurrentLanguageName()}</span>
        <svg
          className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />

          {/* Dropdown menu */}
          <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-gray-200 z-20">
            <div className="py-1">
              {supportedLanguages.map((lang) => (
                <button
                  key={lang.code}
                  onClick={() => changeLanguage(lang.code)}
                  className={`w-full text-left px-4 py-2 transition-colors ${
                    currentLanguage === lang.code
                      ? 'bg-blue-50 text-blue-700 font-medium'
                      : 'text-gray-700 hover:bg-gray-50'
                  }`}
                  dir={lang.dir || 'ltr'}
                >
                  <div className="flex items-center justify-between">
                    <span>{lang.nativeName}</span>
                    {currentLanguage === lang.code && (
                      <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                    )}
                  </div>
                  <div className="text-xs text-gray-500">{lang.name}</div>
                </button>
              ))}
            </div>

            {/* Contribute link */}
            <div className="border-t border-gray-200 px-4 py-2 bg-gray-50">
              <a
                href="https://github.com/Pastorsimon1798/MutualAidApp/blob/main/CONTRIBUTING_TRANSLATIONS.md"
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                Help translate to your language →
              </a>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
