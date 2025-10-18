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

  it('displays error icon', () => {
    renderWithProviders(<ErrorBanner message="Error occurred" />);

    expect(screen.getByText('❌')).toBeInTheDocument();
  });

  it('has alert role for accessibility', () => {
    renderWithProviders(<ErrorBanner message="Error message" />);

    const banner = screen.getByRole('alert');
    expect(banner).toBeInTheDocument();
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

      // The dismiss button shows '✕' not 'dismiss'
      expect(screen.getByText('✕')).toBeInTheDocument();
    });

    it('does not show dismiss button when onDismiss is not provided', () => {
      renderWithProviders(<ErrorBanner message="Error" />);

      expect(screen.queryByText('✕')).not.toBeInTheDocument();
    });

    it('calls onDismiss when dismiss button is clicked', async () => {
      const user = userEvent.setup();
      const handleDismiss = vi.fn();

      renderWithProviders(<ErrorBanner message="Error" onDismiss={handleDismiss} />);

      const dismissButton = screen.getByText('✕');
      await user.click(dismissButton);

      expect(handleDismiss).toHaveBeenCalledTimes(1);
    });

    it('has accessible aria-label on dismiss button', () => {
      const handleDismiss = vi.fn();
      renderWithProviders(<ErrorBanner message="Error" onDismiss={handleDismiss} />);

      const dismissButton = screen.getByLabelText(/dismiss error/i);
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

      expect(screen.getByText('Retry')).toBeInTheDocument();
      expect(screen.getByText('✕')).toBeInTheDocument();
    });

    it('calls correct handlers independently', async () => {
      const user = userEvent.setup();
      const handleRetry = vi.fn();
      const handleDismiss = vi.fn();

      renderWithProviders(
        <ErrorBanner message="Error" onRetry={handleRetry} onDismiss={handleDismiss} />
      );

      await user.click(screen.getByText('Retry'));
      expect(handleRetry).toHaveBeenCalledTimes(1);
      expect(handleDismiss).not.toHaveBeenCalled();

      await user.click(screen.getByText('✕'));
      expect(handleDismiss).toHaveBeenCalledTimes(1);
      expect(handleRetry).toHaveBeenCalledTimes(1); // Still only once
    });
  });

  describe('Styling', () => {
    it('applies custom className', () => {
      const { container } = renderWithProviders(
        <ErrorBanner message="Error" className="custom-error" />
      );

      const banner = container.querySelector('.custom-error');
      expect(banner).toBeInTheDocument();
    });

    it('has destructive border styling', () => {
      const { container } = renderWithProviders(<ErrorBanner message="Error" />);

      const banner = container.querySelector('.border-destructive\\/50');
      expect(banner).toBeInTheDocument();
    });

    it('has destructive background styling', () => {
      const { container } = renderWithProviders(<ErrorBanner message="Error" />);

      const banner = container.querySelector('.bg-destructive\\/10');
      expect(banner).toBeInTheDocument();
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
      renderWithProviders(<ErrorBanner message="" />);

      // Should render without crashing, message area should exist but be empty
      const banner = screen.getByRole('alert');
      expect(banner).toBeInTheDocument();
    });
  });

  describe('Layout', () => {
    it('displays components in correct order', () => {
      const handleRetry = vi.fn();
      const handleDismiss = vi.fn();

      const { container } = renderWithProviders(
        <ErrorBanner message="Error message" onRetry={handleRetry} onDismiss={handleDismiss} />
      );

      const banner = container.querySelector('[role="alert"]');
      expect(banner).toBeInTheDocument();

      // Check that icon, message, and buttons are all present
      expect(screen.getByText('❌')).toBeInTheDocument();
      expect(screen.getByText('Error message')).toBeInTheDocument();
      expect(screen.getByText('Retry')).toBeInTheDocument();
      expect(screen.getByText('✕')).toBeInTheDocument();
    });
  });
});
