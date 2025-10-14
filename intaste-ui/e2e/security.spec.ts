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

test.describe('Security - XSS Prevention', () => {
  test.beforeEach(async ({ page }) => {
    // Set API token in localStorage
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.setItem(
        'intaste-ui-storage',
        JSON.stringify({
          state: { apiToken: 'test-token-123' },
          version: 0,
        })
      );
    });
  });

  test('should sanitize malicious scripts in search snippets', async ({ page }) => {
    // Mock API response with malicious snippet
    await page.route('**/api/v1/assist/query', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          answer: {
            text: 'Here are the search results [1]',
            suggested_questions: [],
          },
          citations: [
            {
              id: 1,
              title: 'Test Document',
              snippet: '<script>alert("xss")</script>Safe content with <em>emphasis</em>',
              url: 'https://example.com/doc1',
              score: 0.95,
            },
          ],
          session: {
            id: 'test-session',
            turn: 1,
          },
          timings: {
            llm_ms: 100,
            search_ms: 50,
            total_ms: 150,
          },
        }),
      });
    });

    await page.goto('/');

    // Submit search query
    const input = page.getByPlaceholder(/type your question/i);
    await input.fill('test query');
    await input.press('Enter');

    // Wait for results
    await page.waitForSelector('text=Test Document');

    // Verify script tag was removed but safe content remains
    const snippetContent = await page.textContent('[data-testid="evidence-panel"]');
    expect(snippetContent).not.toContain('alert');
    expect(snippetContent).not.toContain('<script>');
    expect(snippetContent).toContain('Safe content');

    // Verify em tag was preserved
    const emElements = page.locator('em:has-text("emphasis")');
    await expect(emElements).toHaveCount(1);
  });

  test('should remove inline event handlers from snippets', async ({ page }) => {
    await page.route('**/api/v1/assist/query', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          answer: {
            text: 'Results found [1]',
            suggested_questions: [],
          },
          citations: [
            {
              id: 1,
              title: 'Document with Events',
              snippet: '<div onclick="alert(\'xss\')">Click me</div>',
              url: 'https://example.com/doc2',
              score: 0.9,
            },
          ],
          session: {
            id: 'test-session-2',
            turn: 1,
          },
          timings: {
            llm_ms: 100,
            search_ms: 50,
            total_ms: 150,
          },
        }),
      });
    });

    await page.goto('/');
    const input = page.getByPlaceholder(/type your question/i);
    await input.fill('test query');
    await input.press('Enter');

    await page.waitForSelector('text=Document with Events');

    // Verify no onclick attributes exist in the DOM
    const elementsWithOnclick = await page.locator('[onclick]').count();
    expect(elementsWithOnclick).toBe(0);

    // Verify content is still displayed
    await expect(page.locator('text=Click me')).toBeVisible();
  });

  test('should block javascript: URLs in snippets', async ({ page }) => {
    await page.route('**/api/v1/assist/query', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          answer: {
            text: 'Link found [1]',
            suggested_questions: [],
          },
          citations: [
            {
              id: 1,
              title: 'Malicious Link Document',
              snippet: '<a href="javascript:alert(\'xss\')">Malicious Link</a>',
              url: 'https://example.com/doc3',
              score: 0.85,
            },
          ],
          session: {
            id: 'test-session-3',
            turn: 1,
          },
          timings: {
            llm_ms: 100,
            search_ms: 50,
            total_ms: 150,
          },
        }),
      });
    });

    await page.goto('/');
    const input = page.getByPlaceholder(/type your question/i);
    await input.fill('test query');
    await input.press('Enter');

    await page.waitForSelector('text=Malicious Link Document');

    // Verify no javascript: URLs exist
    const javascriptLinks = await page.locator('a[href^="javascript:"]').count();
    expect(javascriptLinks).toBe(0);

    // Verify link text is still displayed
    await expect(page.locator('text=Malicious Link')).toBeVisible();
  });

  test('should preserve safe HTTPS links in snippets', async ({ page }) => {
    await page.route('**/api/v1/assist/query', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          answer: {
            text: 'Safe link found [1]',
            suggested_questions: [],
          },
          citations: [
            {
              id: 1,
              title: 'Safe Link Document',
              snippet:
                'Visit <a href="https://docs.example.com/guide">our documentation</a> for details',
              url: 'https://example.com/doc4',
              score: 0.88,
            },
          ],
          session: {
            id: 'test-session-4',
            turn: 1,
          },
          timings: {
            llm_ms: 100,
            search_ms: 50,
            total_ms: 150,
          },
        }),
      });
    });

    await page.goto('/');
    const input = page.getByPlaceholder(/type your question/i);
    await input.fill('test query');
    await input.press('Enter');

    await page.waitForSelector('text=Safe Link Document');

    // Verify safe HTTPS link is preserved
    const safeLink = page.locator('a[href="https://docs.example.com/guide"]');
    await expect(safeLink).toBeVisible();
    await expect(safeLink).toHaveText('our documentation');
  });

  test('should handle mixed safe and unsafe content in snippets', async ({ page }) => {
    await page.route('**/api/v1/assist/query', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          answer: {
            text: 'Mixed content found [1]',
            suggested_questions: [],
          },
          citations: [
            {
              id: 1,
              title: 'Mixed Content Document',
              snippet:
                '<strong>Important</strong><script>alert("xss")</script> text with <em>emphasis</em>',
              url: 'https://example.com/doc5',
              score: 0.92,
            },
          ],
          session: {
            id: 'test-session-5',
            turn: 1,
          },
          timings: {
            llm_ms: 100,
            search_ms: 50,
            total_ms: 150,
          },
        }),
      });
    });

    await page.goto('/');
    const input = page.getByPlaceholder(/type your question/i);
    await input.fill('test query');
    await input.press('Enter');

    await page.waitForSelector('text=Mixed Content Document');

    // Verify script was removed
    const content = await page.textContent('[data-testid="evidence-panel"]');
    expect(content).not.toContain('alert');
    expect(content).not.toContain('<script>');

    // Verify safe tags were preserved
    await expect(page.locator('strong:has-text("Important")')).toBeVisible();
    await expect(page.locator('em:has-text("emphasis")')).toBeVisible();
  });

  test('should verify CSP headers are set', async ({ page }) => {
    const response = await page.goto('/');

    // Check for security headers
    const headers = response?.headers();

    expect(headers).toBeDefined();
    if (headers) {
      expect(headers['x-content-type-options']).toBe('nosniff');
      expect(headers['x-frame-options']).toBe('DENY');
      expect(headers['content-security-policy']).toBeDefined();
      expect(headers['content-security-policy']).toContain("default-src 'self'");
    }
  });
});
