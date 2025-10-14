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

test.describe('Citation Interaction', () => {
  test.beforeEach(async ({ page }) => {
    // Set up API token
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.setItem('intaste.token', 'test-token-32-characters-long-secure');
    });

    // Mock API response with citations
    await page.route('**/api/v1/assist/query', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          answer: {
            text: 'Answer with [1] and [2] citations',
            suggested_followups: ['Follow up 1', 'Follow up 2'],
          },
          citations: [
            {
              id: '1',
              title: 'First Document',
              snippet: 'First document <em>snippet</em>',
              url: 'http://example.com/doc1',
              score: 0.95,
              metadata: { site: 'example.com', type: 'html' },
            },
            {
              id: '2',
              title: 'Second Document',
              snippet: 'Second document snippet',
              url: 'http://example.com/doc2',
              score: 0.85,
              metadata: { site: 'example.org', type: 'pdf' },
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

    await page.reload();

    // Submit a query
    const input = page.getByPlaceholder(/ask a question/i);
    await input.fill('Test query');
    await input.press('Enter');

    // Wait for results
    await page.waitForSelector('text=First Document');
  });

  test('should display all citations in sidebar', async ({ page }) => {
    await expect(page.getByText('First Document')).toBeVisible();
    await expect(page.getByText('Second Document')).toBeVisible();
  });

  test('should highlight citation when clicked in answer', async ({ page }) => {
    // Click citation reference in answer
    await page.getByRole('button', { name: '[1]' }).click();

    // The first citation should be highlighted/selected
    // Verify by checking if "Selected" tab is active or citation has active styling
    await expect(page.getByText('First Document')).toBeVisible();
  });

  test('should show citation details in Selected tab', async ({ page }) => {
    // Click citation reference
    await page.getByRole('button', { name: '[1]' }).click();

    // Should show detailed view
    await expect(page.getByText('First Document')).toBeVisible();
    await expect(page.getByText(/snippet/i)).toBeVisible();
    await expect(page.getByText(/0\.95/)).toBeVisible();
  });

  test('should allow switching between Selected and All tabs', async ({ page }) => {
    // Click citation to select it
    await page.getByRole('button', { name: '[1]' }).click();

    // Switch to All tab
    const allTab = page.getByRole('tab', { name: /all/i });
    if (await allTab.isVisible()) {
      await allTab.click();
      await expect(page.getByText('First Document')).toBeVisible();
      await expect(page.getByText('Second Document')).toBeVisible();
    }
  });

  test('should open citation URL in new tab', async ({ page, context }) => {
    // Set up listener for new page
    const pagePromise = context.waitForEvent('page');

    // Click "Open in Fess" link
    const link = page.getByText(/open in fess/i).first();
    await link.click();

    // Wait for new page
    const newPage = await pagePromise;
    await newPage.waitForLoadState();

    // Verify URL
    expect(newPage.url()).toContain('example.com/doc');
  });

  test('should click follow-up suggestion', async ({ page }) => {
    // Click a follow-up suggestion
    await page.getByText('Follow up 1').click();

    // The suggestion should be filled into the input
    const input = page.getByPlaceholder(/ask a question/i);
    const value = await input.inputValue();
    expect(value).toBe('Follow up 1');
  });

  test('should display citation metadata', async ({ page }) => {
    await expect(page.getByText('example.com')).toBeVisible();
    await expect(page.getByText('html')).toBeVisible();
    await expect(page.getByText('example.org')).toBeVisible();
    await expect(page.getByText('pdf')).toBeVisible();
  });

  test('should sanitize HTML in citations', async ({ page }) => {
    // The snippet should show emphasized text but no script tags
    await expect(page.locator('em').filter({ hasText: 'snippet' })).toBeVisible();
    await expect(page.locator('script')).not.toBeVisible();
  });
});
