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
global.localStorage = localStorageMock as any;

// Mock fetch
global.fetch = vi.fn();

// Mock crypto API with full Web Crypto API surface
const cryptoMock = {
  randomUUID: vi.fn(() => '00000000-0000-0000-0000-000000000000'),
  getRandomValues: vi.fn((array: any) => {
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
