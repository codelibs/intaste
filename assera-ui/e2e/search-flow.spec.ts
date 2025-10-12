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

import { test, expect } from '@playwright/test';

test.describe('Search Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Set up API token
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.setItem('assera.token', 'test-token-32-characters-long-secure');
    });
    await page.reload();
  });

  test('should display the search interface', async ({ page }) => {
    await page.goto('/');

    // Check main elements are present
    await expect(page.getByPlaceholder(/ask a question/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /send/i })).toBeVisible();
  });

  test('should submit a query and display results', async ({ page }) => {
    // Mock API response
    await page.route('**/api/v1/assist/query', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          answer: {
            text: 'Test answer with [1] citation',
            suggested_followups: ['What else?'],
          },
          citations: [
            {
              id: '1',
              title: 'Test Document',
              snippet: 'Test snippet',
              url: 'http://example.com/doc1',
              score: 0.9,
              metadata: { site: 'example.com', type: 'html' },
            },
          ],
          session: {
            session_id: 'test-session',
            turn: 1,
            created_at: new Date().toISOString(),
          },
          timings: {
            intent_ms: 100,
            search_ms: 150,
            compose_ms: 80,
            total_ms: 330,
          },
        }),
      });
    });

    await page.goto('/');

    // Enter query
    const input = page.getByPlaceholder(/ask a question/i);
    await input.fill('What is the security policy?');
    await input.press('Enter');

    // Wait for results
    await expect(page.getByText(/test answer/i)).toBeVisible();
    await expect(page.getByText(/test document/i)).toBeVisible();
  });

  test('should handle empty query', async ({ page }) => {
    await page.goto('/');

    const input = page.getByPlaceholder(/ask a question/i);
    await input.press('Enter');

    // Should not submit empty query
    await expect(page.getByText(/test answer/i)).not.toBeVisible();
  });

  test('should allow multi-line input with Shift+Enter', async ({ page }) => {
    await page.goto('/');

    const input = page.getByPlaceholder(/ask a question/i);
    await input.fill('Line 1');
    await input.press('Shift+Enter');
    await input.type('Line 2');

    const value = await input.inputValue();
    expect(value).toContain('\n');
  });

  test('should display error on API failure', async ({ page }) => {
    // Mock API error
    await page.route('**/api/v1/assist/query', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          error: { message: 'Internal server error' },
        }),
      });
    });

    await page.goto('/');

    const input = page.getByPlaceholder(/ask a question/i);
    await input.fill('Test query');
    await input.press('Enter');

    // Should display error message
    await expect(page.getByText(/error/i)).toBeVisible();
  });

  test('should show loading state during query', async ({ page }) => {
    // Mock slow API response
    await page.route('**/api/v1/assist/query', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          answer: { text: 'Answer', suggested_followups: [] },
          citations: [],
          session: {
            session_id: 'test-session',
            turn: 1,
            created_at: new Date().toISOString(),
          },
          timings: { intent_ms: 0, search_ms: 0, compose_ms: 0, total_ms: 0 },
        }),
      });
    });

    await page.goto('/');

    const input = page.getByPlaceholder(/ask a question/i);
    await input.fill('Test query');
    await input.press('Enter');

    // Check loading state
    await expect(input).toBeDisabled();
  });
});
