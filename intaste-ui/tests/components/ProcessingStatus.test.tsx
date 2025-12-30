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
import { ProcessingStatus } from '@/components/common/ProcessingStatus';

describe('ProcessingStatus', () => {
  const mockIntentData = {
    normalized_query: 'machine learning algorithms',
    filters: { site: 'example.com' },
    followups: ['What is supervised learning?', 'What is unsupervised learning?'],
  };

  const mockCitationsData = {
    total: 5,
    topResults: ['Document 1', 'Document 2', 'Document 3'],
  };

  describe('Intent Phase', () => {
    it('shows analyzing query message when intent data is not available', () => {
      const { container } = renderWithProviders(<ProcessingStatus phase="intent" />);

      expect(container.textContent).toContain('Analyzing query...');
    });

    it('displays normalized query when intent data is available', () => {
      renderWithProviders(<ProcessingStatus phase="intent" intentData={mockIntentData} />);

      expect(screen.getByText('"machine learning algorithms"')).toBeInTheDocument();
    });

    it('displays filters when present in intent data', () => {
      const { container } = renderWithProviders(
        <ProcessingStatus phase="intent" intentData={mockIntentData} />
      );

      // Filters are now displayed as Lozenge badges with format "key: value"
      expect(container.textContent).toContain('site');
      expect(container.textContent).toContain('example.com');
    });

    it('displays followup questions when available', () => {
      const { container } = renderWithProviders(
        <ProcessingStatus phase="intent" intentData={mockIntentData} />
      );

      // The component adds colon in code: t('processing.relatedQuestions') + ':'
      expect(container.textContent).toContain('Related Questions:');
      expect(container.textContent).toContain('What is supervised learning?');
      expect(container.textContent).toContain('What is unsupervised learning?');
    });

    it('does not display filters when none are present', () => {
      const intentDataNoFilters = {
        ...mockIntentData,
        filters: {},
      };

      const { container } = renderWithProviders(
        <ProcessingStatus phase="intent" intentData={intentDataNoFilters} />
      );

      // When filters are empty, no Lozenge badges should be displayed
      // The filter key from mockIntentData ("site") should not appear
      expect(container.textContent).not.toContain('site:');
    });

    it('does not display followups when array is empty', () => {
      const intentDataNoFollowups = {
        ...mockIntentData,
        followups: [],
      };

      renderWithProviders(<ProcessingStatus phase="intent" intentData={intentDataNoFollowups} />);

      expect(screen.queryByText(/relatedQuestions/i)).not.toBeInTheDocument();
    });
  });

  describe('Search Phase', () => {
    it('shows searching indicator', () => {
      renderWithProviders(<ProcessingStatus phase="search" />);

      expect(screen.getByText(/searching/i)).toBeInTheDocument();
    });

    it('displays phase icon with animation during search', () => {
      const { container } = renderWithProviders(<ProcessingStatus phase="search" />);

      // Check that the phase icon container exists with glassmorphism
      const iconContainer = container.querySelector('.glass');
      expect(iconContainer).toBeInTheDocument();
    });

    it('shows animate-pulse class for search indicator', () => {
      const { container } = renderWithProviders(<ProcessingStatus phase="search" />);

      // Find the parent div with animate-pulse class
      const pulseElement = container.querySelector('.animate-pulse');
      expect(pulseElement).toBeInTheDocument();
    });
  });

  describe('Compose Phase', () => {
    it('shows generating answer indicator', () => {
      const { container } = renderWithProviders(<ProcessingStatus phase="compose" />);

      expect(container.textContent).toContain('Generating answer...');
    });

    it('displays phase icon with glassmorphism during composition', () => {
      const { container } = renderWithProviders(<ProcessingStatus phase="compose" />);

      // Check that the phase icon container exists with glassmorphism
      const iconContainer = container.querySelector('.glass');
      expect(iconContainer).toBeInTheDocument();
    });

    it('shows animate-pulse class for compose indicator', () => {
      const { container } = renderWithProviders(<ProcessingStatus phase="compose" />);

      // Find the parent div with animate-pulse class
      const pulseElement = container.querySelector('.animate-pulse');
      expect(pulseElement).toBeInTheDocument();
      expect(pulseElement?.textContent).toContain('Generating answer...');
    });
  });

  describe('Citations Data', () => {
    it('displays total number of results found', () => {
      renderWithProviders(<ProcessingStatus phase="search" citationsData={mockCitationsData} />);

      expect(screen.getByText('5 results found')).toBeInTheDocument();
    });

    it('displays top results titles', () => {
      const { container } = renderWithProviders(
        <ProcessingStatus phase="search" citationsData={mockCitationsData} />
      );

      // The component adds colon in code
      expect(container.textContent).toContain('Top Results:');
      // Titles are displayed separately from numbers in the new design
      expect(screen.getByText('Document 1')).toBeInTheDocument();
      expect(screen.getByText('Document 2')).toBeInTheDocument();
      expect(screen.getByText('Document 3')).toBeInTheDocument();
      // Check that numbers are present in the content
      expect(container.textContent).toContain('1.');
      expect(container.textContent).toContain('2.');
      expect(container.textContent).toContain('3.');
    });

    it('does not display citations when total is 0', () => {
      const emptyCitationsData = {
        total: 0,
        topResults: [],
      };

      renderWithProviders(<ProcessingStatus phase="search" citationsData={emptyCitationsData} />);

      expect(screen.queryByText(/results found/i)).not.toBeInTheDocument();
    });

    it('handles citations without top results', () => {
      const citationsNoTopResults = {
        total: 5,
        topResults: [],
      };

      const { container } = renderWithProviders(
        <ProcessingStatus phase="search" citationsData={citationsNoTopResults} />
      );

      expect(screen.getByText('5 results found')).toBeInTheDocument();
      expect(container.textContent).not.toContain('Top Results:');
    });
  });

  describe('Combined Data Display', () => {
    it('displays both intent and citations data', () => {
      const { container } = renderWithProviders(
        <ProcessingStatus
          phase="compose"
          intentData={mockIntentData}
          citationsData={mockCitationsData}
        />
      );

      // Intent data
      expect(screen.getByText('"machine learning algorithms"')).toBeInTheDocument();

      // Citations data
      expect(screen.getByText('5 results found')).toBeInTheDocument();

      // Compose phase indicator
      expect(container.textContent).toContain('Generating answer...');
    });

    it('shows intent data with search phase indicator', () => {
      renderWithProviders(<ProcessingStatus phase="search" intentData={mockIntentData} />);

      expect(screen.getByText('"machine learning algorithms"')).toBeInTheDocument();
      expect(screen.getByText(/searching/i)).toBeInTheDocument();
    });
  });

  describe('Icons and Styling', () => {
    it('displays search icon for search keywords', () => {
      const { container } = renderWithProviders(
        <ProcessingStatus phase="intent" intentData={mockIntentData} />
      );

      // Fluent UI icons render as SVG elements
      const svgIcons = container.querySelectorAll('svg');
      expect(svgIcons.length).toBeGreaterThan(0);
      // Verify the "Search Keywords" section is rendered
      expect(container.textContent).toContain('Search Keywords');
    });

    it('displays checkmark icon for results found', () => {
      const { container } = renderWithProviders(
        <ProcessingStatus phase="search" citationsData={mockCitationsData} />
      );

      // Fluent UI CheckmarkCircleRegular renders as SVG
      const svgIcons = container.querySelectorAll('svg');
      expect(svgIcons.length).toBeGreaterThan(0);
      // Verify results found section is rendered
      expect(container.textContent).toContain('results found');
    });

    it('displays thinking icon for related questions', () => {
      const { container } = renderWithProviders(
        <ProcessingStatus phase="intent" intentData={mockIntentData} />
      );

      // The 💡 emoji is still used for related questions
      expect(container.textContent).toContain('💡');
    });

    it('displays document icon for top results', () => {
      const { container } = renderWithProviders(
        <ProcessingStatus phase="search" citationsData={mockCitationsData} />
      );

      // Fluent UI DocumentRegular renders as SVG
      const svgIcons = container.querySelectorAll('svg');
      expect(svgIcons.length).toBeGreaterThan(0);
      // Verify top results section is rendered
      expect(container.textContent).toContain('Top Results');
    });
  });
});
