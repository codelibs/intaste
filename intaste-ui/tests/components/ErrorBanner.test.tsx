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
import { ErrorBanner } from '@/components/common/ErrorBanner';

describe('ErrorBanner', () => {
  it('renders with error message', () => {
    renderWithProviders(<ErrorBanner message="Something went wrong" />);

    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });

  it('renders Fluent MessageBar component', () => {
    const { container } = renderWithProviders(<ErrorBanner message="Error occurred" />);

    // Fluent UI MessageBar is rendered
    const messageBar = container.querySelector('.fui-MessageBar');
    expect(messageBar).toBeInTheDocument();
  });

  it('has proper accessibility attributes', () => {
    const { container } = renderWithProviders(<ErrorBanner message="Error message" />);

    // Fluent MessageBar has role attribute
    const messageBar = container.querySelector('[role]');
    expect(messageBar).toBeInTheDocument();
  });

  it('shows error title', () => {
    renderWithProviders(<ErrorBanner message="Test error" />);

    // Looking for the translated error title from i18n
    expect(screen.getByText('Error occurred')).toBeInTheDocument();
  });

  describe('Retry Button', () => {
    it('shows retry button when onRetry is provided', () => {
      const handleRetry = vi.fn();
      renderWithProviders(<ErrorBanner message="Error" onRetry={handleRetry} />);

      expect(screen.getByText(/retry/i)).toBeInTheDocument();
    });

    it('does not show retry button when onRetry is not provided', () => {
      renderWithProviders(<ErrorBanner message="Error" />);

      expect(screen.queryByText(/retry/i)).not.toBeInTheDocument();
    });

    it('calls onRetry when retry button is clicked', async () => {
      const user = userEvent.setup();
      const handleRetry = vi.fn();

      renderWithProviders(<ErrorBanner message="Error" onRetry={handleRetry} />);

      const retryButton = screen.getByText(/retry/i);
      await user.click(retryButton);

      expect(handleRetry).toHaveBeenCalledTimes(1);
    });
  });

  describe('Dismiss Button', () => {
    it('shows dismiss button when onDismiss is provided', () => {
      const handleDismiss = vi.fn();
      renderWithProviders(<ErrorBanner message="Error" onDismiss={handleDismiss} />);

      // Fluent MessageBar has dismiss button with aria-label="Dismiss"
      const dismissButton = screen.getByLabelText(/^dismiss$/i);
      expect(dismissButton).toBeInTheDocument();
    });

    it('does not show dismiss button when onDismiss is not provided', () => {
      renderWithProviders(<ErrorBanner message="Error" />);

      const dismissButton = screen.queryByLabelText(/^dismiss$/i);
      expect(dismissButton).not.toBeInTheDocument();
    });

    it('calls onDismiss when dismiss button is clicked', async () => {
      const user = userEvent.setup();
      const handleDismiss = vi.fn();

      renderWithProviders(<ErrorBanner message="Error" onDismiss={handleDismiss} />);

      const dismissButton = screen.getByLabelText(/^dismiss$/i);
      await user.click(dismissButton);

      expect(handleDismiss).toHaveBeenCalledTimes(1);
    });

    it('has accessible aria-label on dismiss button', () => {
      const handleDismiss = vi.fn();
      renderWithProviders(<ErrorBanner message="Error" onDismiss={handleDismiss} />);

      const dismissButton = screen.getByLabelText(/^dismiss$/i);
      expect(dismissButton).toBeInTheDocument();
    });
  });

  describe('Both Buttons', () => {
    it('shows both retry and dismiss buttons when both handlers are provided', () => {
      const handleRetry = vi.fn();
      const handleDismiss = vi.fn();

      renderWithProviders(
        <ErrorBanner message="Error" onRetry={handleRetry} onDismiss={handleDismiss} />
      );

      expect(screen.getByText(/retry/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/^dismiss$/i)).toBeInTheDocument();
    });

    it('calls correct handlers independently', async () => {
      const user = userEvent.setup();
      const handleRetry = vi.fn();
      const handleDismiss = vi.fn();

      renderWithProviders(
        <ErrorBanner message="Error" onRetry={handleRetry} onDismiss={handleDismiss} />
      );

      await user.click(screen.getByText(/retry/i));
      expect(handleRetry).toHaveBeenCalledTimes(1);
      expect(handleDismiss).not.toHaveBeenCalled();

      await user.click(screen.getByLabelText(/^dismiss$/i));
      expect(handleDismiss).toHaveBeenCalledTimes(1);
      expect(handleRetry).toHaveBeenCalledTimes(1); // Still only once
    });
  });

  describe('Styling', () => {
    it('applies custom className', () => {
      const { container } = renderWithProviders(
        <ErrorBanner message="Error" className="custom-error" />
      );

      // Fluent MessageBar receives className
      const banner = container.querySelector('.custom-error');
      expect(banner).toBeInTheDocument();
    });

    it('renders with Fluent error intent', () => {
      const { container } = renderWithProviders(<ErrorBanner message="Error" />);

      // Fluent MessageBar with error intent
      const messageBar = container.querySelector('.fui-MessageBar');
      expect(messageBar).toBeInTheDocument();
    });
  });

  describe('Content Display', () => {
    it('displays long error messages correctly', () => {
      const longMessage =
        'This is a very long error message that should be displayed in full without truncation to ensure the user gets all the information they need';

      renderWithProviders(<ErrorBanner message={longMessage} />);

      expect(screen.getByText(longMessage)).toBeInTheDocument();
    });

    it('displays error messages with special characters', () => {
      const specialMessage = 'Error: <script>alert("test")</script> & "quotes"';

      renderWithProviders(<ErrorBanner message={specialMessage} />);

      expect(screen.getByText(specialMessage)).toBeInTheDocument();
    });

    it('handles empty error message', () => {
      const { container } = renderWithProviders(<ErrorBanner message="" />);

      // Should render without crashing, MessageBar should exist
      const banner = container.querySelector('.fui-MessageBar');
      expect(banner).toBeInTheDocument();
    });
  });

  describe('Layout', () => {
    it('displays components in correct order', () => {
      const handleRetry = vi.fn();
      const handleDismiss = vi.fn();

      renderWithProviders(
        <ErrorBanner message="Error message" onRetry={handleRetry} onDismiss={handleDismiss} />
      );

      // Check that message, title, and buttons are all present
      expect(screen.getByText('Error occurred')).toBeInTheDocument();
      expect(screen.getByText('Error message')).toBeInTheDocument();
      expect(screen.getByText(/retry/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/^dismiss$/i)).toBeInTheDocument();
    });
  });
});
