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

/**
 * UI store for managing theme, language, and UI preferences.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Language, Theme } from '@/types/ui';

interface UIState {
  lang: Language;
  theme: Theme;
  apiToken: string | null;
  sidebarOpen: boolean;
  streamingEnabled: boolean;

  setLang: (lang: Language) => void;
  setTheme: (theme: Theme) => void;
  setApiToken: (token: string | null) => void;
  setSidebarOpen: (open: boolean) => void;
  toggleSidebar: () => void;
  setStreamingEnabled: (enabled: boolean) => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      lang: 'ja',
      theme: 'system',
      apiToken: null,
      sidebarOpen: true,
      streamingEnabled: true, // Enable streaming by default

      setLang: (lang) => set({ lang }),
      setTheme: (theme) => set({ theme }),
      setApiToken: (token) => set({ apiToken: token }),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setStreamingEnabled: (enabled) => set({ streamingEnabled: enabled }),
    }),
    {
      name: 'assera-ui-storage',
      partialize: (state) => ({
        lang: state.lang,
        theme: state.theme,
        apiToken: state.apiToken,
        streamingEnabled: state.streamingEnabled,
      }),
      onRehydrateStorage: () => (state) => {
        // Migration: Check for legacy 'assera.token' key and migrate to new storage
        if (typeof window !== 'undefined' && state) {
          const legacyToken = localStorage.getItem('assera.token');
          if (legacyToken && !state.apiToken) {
            // Migrate legacy token to new storage structure
            state.apiToken = legacyToken;
            // Remove legacy key
            localStorage.removeItem('assera.token');
          }
        }
      },
    }
  )
);
