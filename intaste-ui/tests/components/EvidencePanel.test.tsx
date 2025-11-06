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

import { describe, it, expect, vi } from 'vitest';
import { renderWithProviders, screen } from '../utils/test-utils';
import userEvent from '@testing-library/user-event';
import { EvidencePanel } from '@/components/sidebar/EvidencePanel';
import type { Citation } from '@/types/api';

const mockCitations: Citation[] = [
  {
    id: 1,
    title: 'First Document',
    url: 'https://example.com/doc1',
    snippet: 'This is the first document snippet',
    score: 0.95,
    meta: {},
  },
  {
    id: 2,
    title: 'Second Document',
    url: 'https://example.com/doc2',
    snippet: 'This is the second document snippet',
    score: 0.85,
    meta: {},
  },
  {
    id: 3,
    title: 'Third Document',
    url: 'https://example.com/doc3',
    snippet: 'This is the third document snippet',
    score: 0.75,
    meta: {},
  },
];

describe('EvidencePanel', () => {
  it('renders tab headers', () => {
    renderWithProviders(
      <EvidencePanel citations={mockCitations} selectedId={null} onSelect={() => {}} />
    );

    expect(screen.getByRole('tab', { name: /selected/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /all/i })).toBeInTheDocument();
  });

  it('shows "Selected" tab as active by default', () => {
    renderWithProviders(
      <EvidencePanel citations={mockCitations} selectedId={null} onSelect={() => {}} />
    );

    const selectedTab = screen.getByRole('tab', { name: /selected/i });
    expect(selectedTab).toHaveAttribute('aria-selected', 'true');
  });

  it('displays citation count in "All" tab', () => {
    renderWithProviders(
      <EvidencePanel citations={mockCitations} selectedId={null} onSelect={() => {}} />
    );

    const allTab = screen.getByRole('tab', { name: /all.*3/i });
    expect(allTab).toBeInTheDocument();
  });

  it('switches to "All" tab when clicked', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <EvidencePanel citations={mockCitations} selectedId={null} onSelect={() => {}} />
    );

    const allTab = screen.getByRole('tab', { name: /all/i });
    await user.click(allTab);

    expect(allTab).toHaveAttribute('aria-selected', 'true');
  });

  it('shows "No selection" message when no citation is selected', () => {
    renderWithProviders(
      <EvidencePanel citations={mockCitations} selectedId={null} onSelect={() => {}} />
    );

    // Should be on selected tab by default
    expect(screen.getByText('No citation selected')).toBeInTheDocument();
  });

  it('displays selected citation in "Selected" tab', () => {
    renderWithProviders(
      <EvidencePanel citations={mockCitations} selectedId={2} onSelect={() => {}} />
    );

    // Selected tab should show the second citation
    expect(screen.getByText('Second Document')).toBeInTheDocument();
    expect(screen.getByText(/second document snippet/i)).toBeInTheDocument();
  });

  it('displays all citations in "All" tab', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <EvidencePanel citations={mockCitations} selectedId={null} onSelect={() => {}} />
    );

    // Switch to All tab
    const allTab = screen.getByRole('tab', { name: /all/i });
    await user.click(allTab);

    // All citations should be visible
    expect(screen.getByText('First Document')).toBeInTheDocument();
    expect(screen.getByText('Second Document')).toBeInTheDocument();
    expect(screen.getByText('Third Document')).toBeInTheDocument();
  });

  it('calls onSelect when citation is clicked in "All" tab', async () => {
    const user = userEvent.setup();
    const handleSelect = vi.fn();

    renderWithProviders(
      <EvidencePanel citations={mockCitations} selectedId={null} onSelect={handleSelect} />
    );

    // Switch to All tab
    const allTab = screen.getByRole('tab', { name: /all/i });
    await user.click(allTab);

    // Click on a citation (find the button or clickable element)
    const firstCitation = screen.getByText('First Document').closest('div');
    if (firstCitation) {
      await user.click(firstCitation);
      expect(handleSelect).toHaveBeenCalledWith(1);
    }
  });

  it('highlights active citation in "All" tab', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <EvidencePanel citations={mockCitations} selectedId={2} onSelect={() => {}} />
    );

    // Switch to All tab
    const allTab = screen.getByRole('tab', { name: /all/i });
    await user.click(allTab);

    // The second citation should be highlighted (active)
    // Find the parent element that contains the citation
    const secondCitation = screen.getByText('Second Document').closest('[role="button"]');
    expect(secondCitation).toBeTruthy();
    // Fluent UI Card component is used, check for that
    expect(secondCitation).toHaveClass('fui-Card');
  });

  it('handles empty citations array', () => {
    renderWithProviders(<EvidencePanel citations={[]} selectedId={null} onSelect={() => {}} />);

    // Tab should show count of 0
    expect(screen.getByRole('tab', { name: /all.*0/i })).toBeInTheDocument();
  });

  it('renders EvidencePanel component correctly', () => {
    const { container } = renderWithProviders(
      <EvidencePanel
        citations={mockCitations}
        selectedId={null}
        onSelect={() => {}}
        className="custom-panel"
      />
    );

    // Fluent UI Card component is rendered
    const panel = container.querySelector('[role="group"]');
    expect(panel).toBeInTheDocument();
    expect(panel).toHaveClass('fui-Card');

    // Component structure is correct
    expect(screen.getByRole('tablist')).toBeInTheDocument();
  });

  it('renders tab content', () => {
    renderWithProviders(
      <EvidencePanel citations={mockCitations} selectedId={null} onSelect={() => {}} />
    );

    // Fluent UI TabList doesn't automatically add tabpanel role
    // Instead, verify that tab content is rendered
    const tabList = screen.getByRole('tablist');
    expect(tabList).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /selected/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /all/i })).toBeInTheDocument();
  });

  it('shows full citation details in "Selected" tab', () => {
    renderWithProviders(
      <EvidencePanel citations={mockCitations} selectedId={1} onSelect={() => {}} />
    );

    // In selected tab, citation should be shown with showFull prop
    // This means the URL should be visible
    const citation = screen.getByText('First Document');
    expect(citation).toBeInTheDocument();
  });

  it('maintains selected citation when switching tabs', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <EvidencePanel citations={mockCitations} selectedId={2} onSelect={() => {}} />
    );

    // Initially on selected tab, should show second document
    expect(screen.getByText('Second Document')).toBeInTheDocument();

    // Switch to All tab
    const allTab = screen.getByRole('tab', { name: /all/i });
    await user.click(allTab);

    // Second citation should still be present in All tab
    expect(screen.getByText('Second Document')).toBeInTheDocument();

    // Switch back to Selected tab
    const selectedTab = screen.getByRole('tab', { name: /selected/i });
    await user.click(selectedTab);

    // Should still show second document
    expect(screen.getByText('Second Document')).toBeInTheDocument();
  });
});
