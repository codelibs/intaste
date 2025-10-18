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

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import i18n from '@/libs/i18n/config';
import { DEFAULT_LANGUAGE } from '@/libs/i18n/languages';

interface LanguageState {
  currentLanguage: string;
  changeLanguage: (lang: string) => Promise<void>;
}

export const useLanguageStore = create<LanguageState>()(
  persist(
    (set) => ({
      currentLanguage: DEFAULT_LANGUAGE,
      changeLanguage: async (lang: string) => {
        await i18n.changeLanguage(lang);
        set({ currentLanguage: lang });
        // Update HTML lang attribute
        if (typeof document !== 'undefined') {
          document.documentElement.lang = lang;
        }
      },
    }),
    {
      name: 'language-storage',
      partialize: (state) => ({ currentLanguage: state.currentLanguage }),
    }
  )
);
