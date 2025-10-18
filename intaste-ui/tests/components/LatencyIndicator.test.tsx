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
import { renderWithProviders, screen } from '../utils/test-utils';
import { LatencyIndicator } from '@/components/common/LatencyIndicator';
import type { Timings } from '@/types/api';

describe('LatencyIndicator', () => {
  describe('Latency Levels', () => {
    it('shows "fast" indicator for latency <= 15000ms', () => {
      const timings: Timings = {
        total_ms: 2500,
        llm_ms: 1500,
        search_ms: 1000,
      };

      const { container } = renderWithProviders(<LatencyIndicator timings={timings} />);

      expect(screen.getByText(/fast/i)).toBeInTheDocument();
      // Check for the icon in the HTML content
      expect(container.textContent).toContain('⚡');
    });

    it('shows "normal" indicator for latency between 15000ms and 60000ms', () => {
      const timings: Timings = {
        total_ms: 30000,
        llm_ms: 18000,
        search_ms: 12000,
      };

      const { container } = renderWithProviders(<LatencyIndicator timings={timings} />);

      expect(container.textContent).toContain('Normal');
      expect(container.textContent).toContain('⏱️');
    });

    it('shows "slow" indicator for latency > 60000ms', () => {
      const timings: Timings = {
        total_ms: 70000,
        llm_ms: 40000,
        search_ms: 30000,
      };

      const { container } = renderWithProviders(<LatencyIndicator timings={timings} />);

      expect(container.textContent).toContain('Slow');
      expect(container.textContent).toContain('🐌');
    });

    it('treats exactly 15000ms as "fast"', () => {
      const timings: Timings = {
        total_ms: 15000,
        llm_ms: 9000,
        search_ms: 6000,
      };

      const { container } = renderWithProviders(<LatencyIndicator timings={timings} />);

      expect(container.textContent).toContain('Fast');
    });

    it('treats exactly 60000ms as "normal"', () => {
      const timings: Timings = {
        total_ms: 60000,
        llm_ms: 36000,
        search_ms: 24000,
      };

      const { container } = renderWithProviders(<LatencyIndicator timings={timings} />);

      expect(container.textContent).toContain('Normal');
    });
  });

  describe('Timing Display', () => {
    it('displays total milliseconds', () => {
      const timings: Timings = {
        total_ms: 2500,
        llm_ms: 1500,
        search_ms: 1000,
      };

      renderWithProviders(<LatencyIndicator timings={timings} />);

      expect(screen.getByText('2500ms')).toBeInTheDocument();
    });

    it('displays LLM and search timing details', () => {
      const timings: Timings = {
        total_ms: 3500,
        llm_ms: 2000,
        search_ms: 1500,
      };

      renderWithProviders(<LatencyIndicator timings={timings} />);

      // Check for details containing LLM and search timings
      expect(screen.getByText(/2000.*1500/)).toBeInTheDocument();
    });

    it('handles zero timings', () => {
      const timings: Timings = {
        total_ms: 0,
        llm_ms: 0,
        search_ms: 0,
      };

      renderWithProviders(<LatencyIndicator timings={timings} />);

      expect(screen.getByText('0ms')).toBeInTheDocument();
      // Should be "fast" since 0 < 3000
      expect(screen.getByText(/fast/i)).toBeInTheDocument();
    });

    it('handles very large timings', () => {
      const timings: Timings = {
        total_ms: 80000,
        llm_ms: 50000,
        search_ms: 30000,
      };

      const { container } = renderWithProviders(<LatencyIndicator timings={timings} />);

      expect(screen.getByText('80000ms')).toBeInTheDocument();
      expect(container.textContent).toContain('Slow');
    });
  });

  describe('Styling', () => {
    it('applies green color for fast latency', () => {
      const timings: Timings = {
        total_ms: 1000,
        llm_ms: 600,
        search_ms: 400,
      };

      const { container } = renderWithProviders(<LatencyIndicator timings={timings} />);

      const indicator = container.querySelector('.text-green-600');
      expect(indicator).toBeInTheDocument();
    });

    it('applies yellow color for normal latency', () => {
      const timings: Timings = {
        total_ms: 30000,
        llm_ms: 18000,
        search_ms: 12000,
      };

      const { container } = renderWithProviders(<LatencyIndicator timings={timings} />);

      // Check for yellow/amber color classes (Tailwind uses different naming)
      const hasYellowColor =
        container.querySelector('.text-yellow-600') || container.querySelector('.text-amber-600');
      expect(hasYellowColor).toBeTruthy();
    });

    it('applies red color for slow latency', () => {
      const timings: Timings = {
        total_ms: 70000,
        llm_ms: 42000,
        search_ms: 28000,
      };

      const { container } = renderWithProviders(<LatencyIndicator timings={timings} />);

      const indicator = container.querySelector('.text-red-600');
      expect(indicator).toBeTruthy();
    });

    it('applies custom className', () => {
      const timings: Timings = {
        total_ms: 2000,
        llm_ms: 1200,
        search_ms: 800,
      };

      const { container } = renderWithProviders(
        <LatencyIndicator timings={timings} className="custom-latency" />
      );

      const wrapper = container.querySelector('.custom-latency');
      expect(wrapper).toBeInTheDocument();
    });

    it('has small text size', () => {
      const timings: Timings = {
        total_ms: 2000,
        llm_ms: 1200,
        search_ms: 800,
      };

      const { container } = renderWithProviders(<LatencyIndicator timings={timings} />);

      const wrapper = container.querySelector('.text-xs');
      expect(wrapper).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles missing intent_ms field gracefully', () => {
      const timings: Timings = {
        total_ms: 3000,
        llm_ms: 2000,
        search_ms: 1000,
      };

      renderWithProviders(<LatencyIndicator timings={timings} />);

      // Should render without errors
      expect(screen.getByText('3000ms')).toBeInTheDocument();
    });

    it('displays correct breakdown when LLM time is 0', () => {
      const timings: Timings = {
        total_ms: 1000,
        llm_ms: 0,
        search_ms: 1000,
      };

      renderWithProviders(<LatencyIndicator timings={timings} />);

      expect(screen.getByText(/0.*1000/)).toBeInTheDocument();
    });

    it('displays correct breakdown when search time is 0', () => {
      const timings: Timings = {
        total_ms: 2000,
        llm_ms: 2000,
        search_ms: 0,
      };

      renderWithProviders(<LatencyIndicator timings={timings} />);

      expect(screen.getByText(/2000.*0/)).toBeInTheDocument();
    });
  });
});
