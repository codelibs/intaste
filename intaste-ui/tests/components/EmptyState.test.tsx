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
    const { container } = renderWithProviders(<EmptyState />);

    // Should have Fluent search icon (SVG)
    const icon = container.querySelector('svg');
    expect(icon).toBeInTheDocument();
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
      expect(screen.getByText(suggestion)).toBeInTheDocument();
    });
  });

  it('renders welcome type with simple message only', () => {
    const { container } = renderWithProviders(<EmptyState type="welcome" />);

    // Should have welcome message text
    const textElements = container.querySelectorAll('.fui-Text');
    expect(textElements.length).toBe(1);

    // Should NOT have search icon
    const searchIcon = container.querySelector('svg');
    expect(searchIcon).not.toBeInTheDocument();
  });

  it('renders noResults type with appropriate content', () => {
    const { container } = renderWithProviders(<EmptyState type="noResults" />);

    // Should have Fluent search icon (SVG)
    const icon = container.querySelector('svg');
    expect(icon).toBeInTheDocument();

    // Should have no results specific content
    const textElements = container.querySelectorAll('.fui-Text');
    expect(textElements.length).toBeGreaterThan(0);
  });

  it('custom values override default values for noResults type', () => {
    const customTitle = 'Override Title';
    const customMessage = 'Override message';
    const customSuggestions = ['Custom 1', 'Custom 2'];

    renderWithProviders(
      <EmptyState
        type="noResults"
        title={customTitle}
        message={customMessage}
        suggestions={customSuggestions}
      />
    );

    expect(screen.getByText(customTitle)).toBeInTheDocument();
    expect(screen.getByText(customMessage)).toBeInTheDocument();
    expect(screen.getByText('Custom 1')).toBeInTheDocument();
    expect(screen.getByText('Custom 2')).toBeInTheDocument();
  });

  it('welcome type shows custom title if provided', () => {
    renderWithProviders(<EmptyState type="welcome" title="Custom Welcome Message" />);

    // Should show custom title
    expect(screen.getByText('Custom Welcome Message')).toBeInTheDocument();
  });

  it('welcome type ignores message and suggestions props', () => {
    const { container } = renderWithProviders(
      <EmptyState type="welcome" message="Custom Message" suggestions={['Suggestion 1']} />
    );

    // Should NOT show message or suggestions (only title)
    expect(screen.queryByText('Custom Message')).not.toBeInTheDocument();
    expect(screen.queryByText('Suggestion 1')).not.toBeInTheDocument();

    // Should have only one text element (the title)
    const textElements = container.querySelectorAll('.fui-Text');
    expect(textElements.length).toBe(1);
  });

  it('handles empty suggestions array', () => {
    const { container } = renderWithProviders(<EmptyState suggestions={[]} />);

    // Should render without errors - check for Fluent Text components
    const textElements = container.querySelectorAll('.fui-Text');
    expect(textElements.length).toBeGreaterThan(0);

    // Empty suggestions array should not render any suggestion cards
    // The component should only show title and message, but no suggestions grid
    const suggestionCards = container.querySelectorAll('[class*="suggestionCard"]');
    expect(suggestionCards.length).toBe(0);
  });

  it('applies custom className', () => {
    const { container } = renderWithProviders(<EmptyState className="custom-empty-state" />);

    const emptyState = container.querySelector('.custom-empty-state');
    expect(emptyState).toBeInTheDocument();
  });

  it('renders suggestions as card grid', () => {
    const suggestions = ['First', 'Second', 'Third'];

    renderWithProviders(<EmptyState suggestions={suggestions} />);

    // Check that all suggestions are rendered
    suggestions.forEach((suggestion) => {
      expect(screen.getByText(suggestion)).toBeInTheDocument();
    });

    // Verify the number of suggestion texts matches
    const allSuggestions = screen.getAllByText(/First|Second|Third/);
    expect(allSuggestions).toHaveLength(3);
  });

  it('renders centered content with proper structure', () => {
    const { container } = renderWithProviders(<EmptyState />);

    const wrapper = container.firstChild as HTMLElement;
    // Fluent UI uses makeStyles, check for container existence
    expect(wrapper).toBeInTheDocument();
    expect(wrapper.tagName).toBe('DIV');
  });

  it('displays icon with proper size', () => {
    const { container } = renderWithProviders(<EmptyState />);

    // Fluent icon is rendered as SVG with size 48
    const icon = container.querySelector('svg');
    expect(icon).toBeInTheDocument();
    expect(icon).toHaveAttribute('height', '48');
  });
});
