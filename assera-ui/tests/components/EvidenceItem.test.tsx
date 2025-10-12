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
import { renderWithProviders, screen, createMockCitation } from '../utils/test-utils';
import userEvent from '@testing-library/user-event';
import EvidenceItem from '@/components/sidebar/EvidenceItem';

describe('EvidenceItem', () => {
  it('renders citation details', () => {
    const citation = createMockCitation('1');
    renderWithProviders(<EvidenceItem citation={citation} />);

    expect(screen.getByText(citation.title)).toBeInTheDocument();
    expect(screen.getByText(citation.snippet)).toBeInTheDocument();
    expect(screen.getByText(`[${citation.id}]`)).toBeInTheDocument();
  });

  it('renders metadata', () => {
    const citation = createMockCitation('1');
    renderWithProviders(<EvidenceItem citation={citation} />);

    expect(screen.getByText(citation.metadata.site)).toBeInTheDocument();
    expect(screen.getByText(citation.metadata.type)).toBeInTheDocument();
  });

  it('renders score', () => {
    const citation = createMockCitation('1');
    renderWithProviders(<EvidenceItem citation={citation} />);

    expect(screen.getByText(/0\.9/)).toBeInTheDocument();
  });

  it('applies active styling when selected', () => {
    const citation = createMockCitation('1');
    const { container } = renderWithProviders(
      <EvidenceItem citation={citation} isActive={true} />
    );

    const card = container.firstChild;
    expect(card).toHaveClass('ring-2');
  });

  it('calls onClick when clicked', async () => {
    const handleClick = vi.fn();
    const user = userEvent.setup();
    const citation = createMockCitation('1');

    renderWithProviders(<EvidenceItem citation={citation} onClick={handleClick} />);

    const card = screen.getByText(citation.title).closest('div');
    if (card) {
      await user.click(card);
      expect(handleClick).toHaveBeenCalled();
    }
  });

  it('renders Open in Fess link', () => {
    const citation = createMockCitation('1');
    renderWithProviders(<EvidenceItem citation={citation} />);

    const link = screen.getByText(/open in fess/i);
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', citation.url);
    expect(link).toHaveAttribute('target', '_blank');
  });

  it('sanitizes HTML in snippet', () => {
    const citation = {
      ...createMockCitation('1'),
      snippet: '<script>alert("xss")</script>Safe content <em>emphasized</em>',
    };
    renderWithProviders(<EvidenceItem citation={citation} />);

    // Script should be removed, but em should remain
    expect(screen.queryByText(/alert/)).not.toBeInTheDocument();
    const emphasized = screen.getByText(/emphasized/);
    expect(emphasized.tagName).toBe('EM');
  });

  it('removes inline event handlers from snippet', () => {
    const citation = {
      ...createMockCitation('1'),
      snippet: '<div onclick="alert(\'xss\')">Click me</div>',
    };
    const { container } = renderWithProviders(<EvidenceItem citation={citation} />);

    // Should not contain onclick attribute
    const divs = container.querySelectorAll('div[onclick]');
    expect(divs.length).toBe(0);
    expect(screen.getByText(/Click me/)).toBeInTheDocument();
  });

  it('removes javascript: URLs from snippet', () => {
    const citation = {
      ...createMockCitation('1'),
      snippet: '<a href="javascript:alert(\'xss\')">Malicious link</a>',
    };
    const { container } = renderWithProviders(<EvidenceItem citation={citation} />);

    // Should not contain javascript: URLs
    const links = container.querySelectorAll('a[href^="javascript:"]');
    expect(links.length).toBe(0);
  });

  it('preserves safe formatting tags in snippet', () => {
    const citation = {
      ...createMockCitation('1'),
      snippet: 'Text with <em>emphasis</em>, <strong>bold</strong>, and <mark>highlighted</mark> content',
    };
    renderWithProviders(<EvidenceItem citation={citation} />);

    expect(screen.getByText(/emphasis/).tagName).toBe('EM');
    expect(screen.getByText(/bold/).tagName).toBe('STRONG');
    expect(screen.getByText(/highlighted/).tagName).toBe('MARK');
  });

  it('handles snippet with safe HTTPS links', () => {
    const citation = {
      ...createMockCitation('1'),
      snippet: 'Visit <a href="https://docs.example.com">documentation</a> for details',
    };
    const { container } = renderWithProviders(<EvidenceItem citation={citation} />);

    const link = container.querySelector('a[href="https://docs.example.com"]');
    expect(link).toBeInTheDocument();
    expect(link?.textContent).toContain('documentation');
  });

  it('is keyboard accessible', async () => {
    const handleClick = vi.fn();
    const user = userEvent.setup();
    const citation = createMockCitation('1');

    renderWithProviders(<EvidenceItem citation={citation} onClick={handleClick} />);

    const card = screen.getByText(citation.title).closest('div[role="button"]');
    if (card) {
      card.focus();
      await user.keyboard('{Enter}');
      expect(handleClick).toHaveBeenCalled();
    }
  });
});
