// Copyright (c) 2025 CodeLibs
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//     http://www.apache.org/licenses/LICENSE-2.0
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import { DEFAULT_LANGUAGE, FALLBACK_LANGUAGE, SUPPORTED_LANGUAGES } from './languages';

// Import translation files
const loadResources = async () => {
  const resources: Record<string, { common: any }> = {};

  for (const lang of SUPPORTED_LANGUAGES) {
    try {
      const translation = await import(`../../../public/locales/${lang.code}/common.json`);
      resources[lang.code] = {
        common: translation.default || translation,
      };
    } catch (error) {
      console.warn(`Failed to load translations for ${lang.code}:`, error);
    }
  }

  return resources;
};

export const initI18n = async () => {
  const resources = await loadResources();

  await i18n
    .use(LanguageDetector)
    .use(initReactI18next)
    .init({
      resources,
      defaultNS: 'common',
      fallbackLng: FALLBACK_LANGUAGE,
      supportedLngs: SUPPORTED_LANGUAGES.map((lang) => lang.code),

      // Language detection configuration
      detection: {
        order: ['localStorage', 'navigator', 'htmlTag'],
        caches: ['localStorage'],
        lookupLocalStorage: 'i18nextLng',
      },

      interpolation: {
        escapeValue: false, // React already escapes values
      },

      react: {
        useSuspense: false,
      },

      // Load all language codes including regional variants (zh-CN, zh-TW, etc.)
      load: 'all',

      debug: process.env.NODE_ENV === 'development',
    });

  return i18n;
};

// For SSR/initial load
export const getInitialLanguage = (): string => {
  if (typeof window === 'undefined') {
    return DEFAULT_LANGUAGE;
  }

  // Check localStorage first
  const stored = localStorage.getItem('i18nextLng');
  if (stored && SUPPORTED_LANGUAGES.some((lang) => lang.code === stored)) {
    return stored;
  }

  // Check browser language
  const browserLang = navigator.language;
  const matched = SUPPORTED_LANGUAGES.find(
    (lang) => browserLang.startsWith(lang.code) || lang.code.startsWith(browserLang)
  );

  return matched?.code || DEFAULT_LANGUAGE;
};

export default i18n;
