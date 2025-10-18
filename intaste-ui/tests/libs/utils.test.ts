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

import { describe, it, expect } from 'vitest';
import { getLatencyLevel, cn } from '@/libs/utils';

describe('getLatencyLevel', () => {
  describe('Boundary Value Testing', () => {
    it('should return "good" for 0ms', () => {
      expect(getLatencyLevel(0)).toBe('good');
    });

    it('should return "good" for 15000ms (upper boundary)', () => {
      expect(getLatencyLevel(15000)).toBe('good');
    });

    it('should return "ok" for 15001ms (just above good threshold)', () => {
      expect(getLatencyLevel(15001)).toBe('ok');
    });

    it('should return "ok" for 60000ms (upper boundary)', () => {
      expect(getLatencyLevel(60000)).toBe('ok');
    });

    it('should return "slow" for 60001ms (just above ok threshold)', () => {
      expect(getLatencyLevel(60001)).toBe('slow');
    });
  });

  describe('Real-world Performance Values', () => {
    it('should return "good" for 8896ms (GPU environment)', () => {
      expect(getLatencyLevel(8896)).toBe('good');
    });

    it('should return "slow" for 63912ms (CPU environment)', () => {
      expect(getLatencyLevel(63912)).toBe('slow');
    });

    it('should return "good" for typical fast response (~5s)', () => {
      expect(getLatencyLevel(5000)).toBe('good');
    });

    it('should return "ok" for typical moderate response (~30s)', () => {
      expect(getLatencyLevel(30000)).toBe('ok');
    });

    it('should return "slow" for very slow response (~90s)', () => {
      expect(getLatencyLevel(90000)).toBe('slow');
    });
  });

  describe('Edge Cases', () => {
    it('should handle very small values correctly', () => {
      expect(getLatencyLevel(1)).toBe('good');
      expect(getLatencyLevel(100)).toBe('good');
    });

    it('should handle very large values correctly', () => {
      expect(getLatencyLevel(100000)).toBe('slow');
      expect(getLatencyLevel(1000000)).toBe('slow');
    });

    it('should handle negative values (invalid but defensive)', () => {
      // While negative values are invalid, the function should handle them gracefully
      expect(getLatencyLevel(-1)).toBe('good');
    });

    it('should handle decimal values', () => {
      expect(getLatencyLevel(14999.9)).toBe('good');
      expect(getLatencyLevel(15000.1)).toBe('ok');
      expect(getLatencyLevel(60000.1)).toBe('slow');
    });
  });

  describe('Category Distribution', () => {
    it('should categorize GPU-like responses as "good"', () => {
      // GPU environment typically 5-15s
      expect(getLatencyLevel(5000)).toBe('good');
      expect(getLatencyLevel(8000)).toBe('good');
      expect(getLatencyLevel(10000)).toBe('good');
      expect(getLatencyLevel(12000)).toBe('good');
      expect(getLatencyLevel(15000)).toBe('good');
    });

    it('should categorize moderate responses as "ok"', () => {
      // Acceptable but not fast, 15-60s range
      expect(getLatencyLevel(20000)).toBe('ok');
      expect(getLatencyLevel(30000)).toBe('ok');
      expect(getLatencyLevel(45000)).toBe('ok');
      expect(getLatencyLevel(60000)).toBe('ok');
    });

    it('should categorize problematic responses as "slow"', () => {
      // CPU environment or issues, >60s
      expect(getLatencyLevel(65000)).toBe('slow');
      expect(getLatencyLevel(70000)).toBe('slow');
      expect(getLatencyLevel(100000)).toBe('slow');
    });
  });
});

describe('cn', () => {
  it('should merge class names correctly', () => {
    expect(cn('foo', 'bar')).toBe('foo bar');
  });

  it('should handle conditional classes', () => {
    expect(cn('foo', false && 'bar', 'baz')).toBe('foo baz');
  });

  it('should handle Tailwind class conflicts', () => {
    // twMerge should handle conflicts, keeping the last one
    expect(cn('p-4', 'p-2')).toBe('p-2');
  });

  it('should handle empty input', () => {
    expect(cn()).toBe('');
  });

  it('should handle undefined and null', () => {
    expect(cn('foo', undefined, 'bar', null)).toBe('foo bar');
  });
});
