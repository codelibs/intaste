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
import { EmptyState } from '@/components/common/EmptyState';

describe('EmptyState', () => {
  it('renders with default noResults type', () => {
    renderWithProviders(<EmptyState />);

    // Should have search icon
    expect(screen.getByText('🔍')).toBeInTheDocument();
  });

  it('displays custom title when provided', () => {
    renderWithProviders(<EmptyState title="Custom Title" />);

    expect(screen.getByText('Custom Title')).toBeInTheDocument();
  });

  it('displays custom message when provided', () => {
    renderWithProviders(<EmptyState message="Custom message text" />);

    expect(screen.getByText('Custom message text')).toBeInTheDocument();
  });

  it('displays custom suggestions when provided', () => {
    const suggestions = ['Try suggestion 1', 'Try suggestion 2', 'Try suggestion 3'];

    renderWithProviders(<EmptyState suggestions={suggestions} />);

    suggestions.forEach((suggestion) => {
      expect(screen.getByText(`• ${suggestion}`)).toBeInTheDocument();
    });
  });

  it('renders welcome type with appropriate content', () => {
    renderWithProviders(<EmptyState type="welcome" />);

    // Should still have search icon
    expect(screen.getByText('🔍')).toBeInTheDocument();

    // Should have welcome-specific content (checking via i18n keys)
    // The exact text depends on translations, but we can check structure
    const heading = screen.getByRole('heading', { level: 3 });
    expect(heading).toBeInTheDocument();
  });

  it('renders noResults type with appropriate content', () => {
    renderWithProviders(<EmptyState type="noResults" />);

    // Should have search icon
    expect(screen.getByText('🔍')).toBeInTheDocument();

    // Should have no results specific content
    const heading = screen.getByRole('heading', { level: 3 });
    expect(heading).toBeInTheDocument();
  });

  it('custom values override default values', () => {
    const customTitle = 'Override Title';
    const customMessage = 'Override message';
    const customSuggestions = ['Custom 1', 'Custom 2'];

    renderWithProviders(
      <EmptyState
        type="welcome"
        title={customTitle}
        message={customMessage}
        suggestions={customSuggestions}
      />
    );

    expect(screen.getByText(customTitle)).toBeInTheDocument();
    expect(screen.getByText(customMessage)).toBeInTheDocument();
    expect(screen.getByText('• Custom 1')).toBeInTheDocument();
    expect(screen.getByText('• Custom 2')).toBeInTheDocument();
  });

  it('handles empty suggestions array', () => {
    renderWithProviders(<EmptyState suggestions={[]} />);

    // Should render without errors
    const heading = screen.getByRole('heading', { level: 3 });
    expect(heading).toBeInTheDocument();

    // No suggestions list should be visible
    const lists = screen.queryAllByRole('list');
    expect(lists.length).toBe(0);
  });

  it('applies custom className', () => {
    const { container } = renderWithProviders(<EmptyState className="custom-empty-state" />);

    const emptyState = container.querySelector('.custom-empty-state');
    expect(emptyState).toBeInTheDocument();
  });

  it('renders suggestions as bullet list', () => {
    const suggestions = ['First', 'Second', 'Third'];

    renderWithProviders(<EmptyState suggestions={suggestions} />);

    const list = screen.getByRole('list');
    expect(list).toBeInTheDocument();

    const items = screen.getAllByRole('listitem');
    expect(items).toHaveLength(3);
  });

  it('centers content with proper styling classes', () => {
    const { container } = renderWithProviders(<EmptyState />);

    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper).toHaveClass('text-center');
    expect(wrapper).toHaveClass('py-12');
  });

  it('displays icon with proper size', () => {
    renderWithProviders(<EmptyState />);

    const icon = screen.getByText('🔍');
    expect(icon).toHaveClass('text-6xl');
  });
});
