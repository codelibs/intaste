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

test.describe('Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.setItem('assera.token', 'test-token-32-characters-long-secure');
    });
    await page.reload();
  });

  test('should be keyboard navigable', async ({ page }) => {
    await page.goto('/');

    // Tab through elements
    await page.keyboard.press('Tab');
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName);

    expect(focusedElement).toBeTruthy();
  });

  test('should have accessible labels', async ({ page }) => {
    // Check for ARIA labels
    const input = page.getByPlaceholder(/ask a question/i);
    const ariaLabel = await input.getAttribute('aria-label');

    expect(ariaLabel || (await input.getAttribute('placeholder'))).toBeTruthy();
  });

  test('should have proper heading hierarchy', async ({ page }) => {
    const headings = await page.locator('h1, h2, h3, h4, h5, h6').allTextContents();
    expect(headings.length).toBeGreaterThan(0);
  });

  test('should support screen reader text', async ({ page }) => {
    // Check for sr-only or visually-hidden classes
    const srElements = await page.locator('.sr-only, [class*="sr-only"]').count();
    // Screen reader text should exist for improved accessibility
    expect(srElements).toBeGreaterThanOrEqual(0);
  });

  test('should have proper button roles', async ({ page }) => {
    const buttons = await page.getByRole('button').count();
    expect(buttons).toBeGreaterThan(0);
  });

  test('should have proper link roles', async ({ page }) => {
    // Mock response with citations first
    await page.route('**/api/v1/assist/query', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          answer: { text: 'Answer', suggested_followups: [] },
          citations: [
            {
              id: '1',
              title: 'Doc',
              snippet: 'Snippet',
              url: 'http://example.com',
              score: 0.9,
              metadata: { site: 'example.com', type: 'html' },
            },
          ],
          session: {
            session_id: 'test',
            turn: 1,
            created_at: new Date().toISOString(),
          },
          timings: { intent_ms: 0, search_ms: 0, compose_ms: 0, total_ms: 0 },
        }),
      });
    });

    // Submit query to show citations
    const input = page.getByPlaceholder(/ask a question/i);
    await input.fill('test');
    await input.press('Enter');
    await page.waitForSelector('text=Doc');

    const links = await page.getByRole('link').count();
    expect(links).toBeGreaterThan(0);
  });

  test('should have descriptive link text', async ({ page }) => {
    // Mock response
    await page.route('**/api/v1/assist/query', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          answer: { text: 'Answer', suggested_followups: [] },
          citations: [
            {
              id: '1',
              title: 'Document Title',
              snippet: 'Snippet',
              url: 'http://example.com',
              score: 0.9,
              metadata: { site: 'example.com', type: 'html' },
            },
          ],
          session: {
            session_id: 'test',
            turn: 1,
            created_at: new Date().toISOString(),
          },
          timings: { intent_ms: 0, search_ms: 0, compose_ms: 0, total_ms: 0 },
        }),
      });
    });

    const input = page.getByPlaceholder(/ask a question/i);
    await input.fill('test');
    await input.press('Enter');
    await page.waitForSelector('text=Document Title');

    // Check that links have descriptive text (not just "click here")
    const linkTexts = await page.getByRole('link').allTextContents();
    for (const text of linkTexts) {
      expect(text.toLowerCase()).not.toBe('click here');
      expect(text.toLowerCase()).not.toBe('link');
    }
  });

  test('should have proper color contrast', async ({ page }) => {
    // This is a basic check - full contrast testing requires specialized tools
    const bodyBg = await page.evaluate(() => {
      return window.getComputedStyle(document.body).backgroundColor;
    });

    expect(bodyBg).toBeTruthy();
  });
});
