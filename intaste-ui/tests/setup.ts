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

import '@testing-library/jest-dom';
import { afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
global.localStorage = localStorageMock as unknown as Storage;

// Mock fetch
global.fetch = vi.fn();

// Mock ResizeObserver (required for Fluent UI components)
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
} as unknown as typeof ResizeObserver;

// Mock crypto API with full Web Crypto API surface
const cryptoMock = {
  randomUUID: vi.fn(() => '00000000-0000-0000-0000-000000000000'),
  getRandomValues: vi.fn((array: Uint8Array) => {
    for (let i = 0; i < array.length; i++) {
      array[i] = Math.floor(Math.random() * 256);
    }
    return array;
  }),
  subtle: {} as SubtleCrypto,
};

// Set crypto on both global and window
vi.stubGlobal('crypto', cryptoMock);
Object.defineProperty(global, 'crypto', {
  value: cryptoMock,
  writable: true,
});

// Mock uuid utility
vi.mock('@/libs/uuid', () => ({
  generateUUID: vi.fn(() => '00000000-0000-0000-0000-000000000000'),
}));

// Mock i18n config
vi.mock('@/libs/i18n/config', () => ({
  default: {
    changeLanguage: vi.fn(() => Promise.resolve()),
    language: 'en',
    t: (key: string) => key,
  },
}));

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, options?: Record<string, unknown>) => {
      // Translation map for common keys
      const translations: Record<string, string> = {
        'header.title': 'Intaste',
        'header.streaming': 'Streaming...',
        'header.setApiToken': 'Set API Token',
        'header.apiTokenPrompt': 'Enter your API token:',
        'input.placeholder': 'Enter your question here...',
        'input.helper': 'Enter to send • Shift+Enter for new line',
        'input.characterCount': '{{count}} / 4096',
        'answer.viewCitation': 'View citation {{id}}',
        'answer.relatedQuestions': 'Related questions:',
        'answer.fallbackNotice': '⚠️',
        'processing.searchKeywords': 'Search Keywords',
        'processing.filters': 'Filters',
        'processing.relatedQuestions': 'Related Questions',
        'processing.searching': 'Searching...',
        'processing.resultsFound': '{{count}} results found',
        'processing.topResults': 'Top Results',
        'processing.generatingAnswer': 'Generating answer...',
        'processing.analyzingQuery': 'Analyzing query...',
        'evidence.selected': 'Selected',
        'evidence.all': 'All ({{count}})',
        'evidence.noSelection': 'No citation selected',
        'history.title': 'Search History',
        'history.clear': 'Clear',
        'empty.welcome.title': 'Welcome to Intaste',
        'empty.welcome.message':
          'Enter your question above to get started with AI-assisted search.',
        'empty.noResults.title': 'No sources found',
        'empty.noResults.message': 'Try different keywords or check your search criteria.',
        'error.title': 'Error occurred',
        'error.retry': 'Retry',
        'error.dismiss': '✕',
        'loading.searching': 'Searching...',
        'latency.fast': 'Fast',
        'latency.normal': 'Normal',
        'latency.slow': 'Slow',
        'latency.details': '(LLM: {{llm}}ms, Search: {{search}}ms)',
        'footer.version': 'Intaste v{{version}}',
        'footer.license': 'Apache License 2.0',
        'footer.github': 'GitHub',
      };

      // Handle returnObjects for arrays
      if (options?.returnObjects) {
        if (key === 'empty.welcome.suggestions') {
          return [
            'Ask questions in natural language',
            'Results will include citations and sources',
            'Click citation numbers to view details',
          ];
        }
        if (key === 'empty.noResults.suggestions') {
          return ['Use broader search terms', 'Check spelling', 'Try related keywords'];
        }
      }

      // Get the translation or fallback to key
      let result = translations[key] || key;

      // Handle interpolation
      if (options && typeof options === 'object') {
        Object.keys(options).forEach((optKey) => {
          if (optKey !== 'returnObjects') {
            result = result.replace(`{{${optKey}}}`, String(options[optKey]));
          }
        });
      }

      return result;
    },
    i18n: {
      language: 'en',
      changeLanguage: vi.fn(() => Promise.resolve()),
    },
  }),
  I18nextProvider: ({ children }: { children: React.ReactNode }) => children,
  initReactI18next: {
    type: '3rdParty',
    init: vi.fn(),
  },
}));
