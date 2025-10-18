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

import { describe, it, expect, vi, beforeAll } from 'vitest';

// Unmock both the uuid module and crypto for this test file
vi.unmock('@/libs/uuid');

beforeAll(() => {
  // Reset crypto mock to use real crypto.randomUUID
  const realCrypto = {
    randomUUID: () => {
      // Generate a proper UUID v4
      return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
        const r = (Math.random() * 16) | 0;
        const v = c === 'x' ? r : (r & 0x3) | 0x8;
        return v.toString(16);
      });
    },
    getRandomValues: (array: any) => {
      for (let i = 0; i < array.length; i++) {
        array[i] = Math.floor(Math.random() * 256);
      }
      return array;
    },
    subtle: {} as SubtleCrypto,
  };

  vi.stubGlobal('crypto', realCrypto);
});

// Import the actual module, not the mocked version
const uuidModule = await import('../../src/libs/uuid');

describe('UUID Generation', () => {
  describe('RFC 4122 Compliance', () => {
    it('generates UUID in correct format', () => {
      const uuid = uuidModule.generateUUID();

      // UUID format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
      const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

      expect(uuid).toMatch(uuidRegex);
    });

    it('generates UUID with version 4 identifier', () => {
      const uuid = uuidModule.generateUUID();

      // The 15th character (index 14) should be '4'
      expect(uuid.charAt(14)).toBe('4');
    });

    it('generates UUID with correct variant bits', () => {
      const uuid = uuidModule.generateUUID();

      // The 20th character (index 19) should be 8, 9, a, or b
      const variantChar = uuid.charAt(19);
      expect(['8', '9', 'a', 'b', 'A', 'B']).toContain(variantChar);
    });

    it('generates UUID with correct length', () => {
      const uuid = uuidModule.generateUUID();

      expect(uuid.length).toBe(36);
    });

    it('includes correct number of hyphens', () => {
      const uuid = uuidModule.generateUUID();

      const hyphens = (uuid.match(/-/g) || []).length;
      expect(hyphens).toBe(4);
    });

    it('has hyphens in correct positions', () => {
      const uuid = uuidModule.generateUUID();

      expect(uuid.charAt(8)).toBe('-');
      expect(uuid.charAt(13)).toBe('-');
      expect(uuid.charAt(18)).toBe('-');
      expect(uuid.charAt(23)).toBe('-');
    });
  });

  describe('Uniqueness', () => {
    it('generates unique UUIDs', () => {
      const uuids = new Set();
      const count = 1000;

      for (let i = 0; i < count; i++) {
        uuids.add(uuidModule.generateUUID());
      }

      expect(uuids.size).toBe(count);
    });

    it('generates different UUIDs on consecutive calls', () => {
      const uuid1 = uuidModule.generateUUID();
      const uuid2 = uuidModule.generateUUID();
      const uuid3 = uuidModule.generateUUID();

      expect(uuid1).not.toBe(uuid2);
      expect(uuid2).not.toBe(uuid3);
      expect(uuid1).not.toBe(uuid3);
    });
  });

  describe('Character Set', () => {
    it('only contains valid hexadecimal characters', () => {
      const uuid = uuidModule.generateUUID();
      const withoutHyphens = uuid.replace(/-/g, '');

      const hexRegex = /^[0-9a-f]+$/i;
      expect(withoutHyphens).toMatch(hexRegex);
    });

    it('uses lowercase hexadecimal characters', () => {
      const uuid = uuidModule.generateUUID();
      const withoutHyphens = uuid.replace(/-/g, '');

      // Should be lowercase hex (crypto.randomUUID returns lowercase)
      const lowercaseHexRegex = /^[0-9a-f]+$/;
      expect(withoutHyphens).toMatch(lowercaseHexRegex);
    });
  });

  describe('Performance', () => {
    it('generates UUIDs quickly', () => {
      const start = Date.now();
      const count = 10000;

      for (let i = 0; i < count; i++) {
        uuidModule.generateUUID();
      }

      const duration = Date.now() - start;

      // Should generate 10000 UUIDs in less than 1 second
      expect(duration).toBeLessThan(1000);
    });
  });

  describe('Return Type', () => {
    it('returns a string', () => {
      const uuid = uuidModule.generateUUID();
      expect(typeof uuid).toBe('string');
    });

    it('does not return null or undefined', () => {
      const uuid = uuidModule.generateUUID();
      expect(uuid).toBeTruthy();
      expect(uuid).not.toBeNull();
      expect(uuid).not.toBeUndefined();
    });
  });
});
