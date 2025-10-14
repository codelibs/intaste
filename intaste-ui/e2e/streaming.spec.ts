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

/**
 * E2E tests for streaming functionality
 */

import { test, expect } from '@playwright/test';

test.describe('Streaming Functionality', () => {
  test.beforeEach(async ({ page }) => {
    // Set API token in localStorage
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.setItem('intaste.token', 'test-token');
    });
  });

  test('should display streaming toggle in header', async ({ page }) => {
    await page.goto('/');

    // Check for streaming toggle
    const streamingToggle = page.locator('input[type="checkbox"]');
    await expect(streamingToggle).toBeVisible();
    await expect(streamingToggle).toBeChecked(); // Should be enabled by default

    // Check label text
    const label = page.locator('label:has(input[type="checkbox"])');
    await expect(label).toContainText('Stream');
  });

  test('should toggle streaming mode on/off', async ({ page }) => {
    await page.goto('/');

    const streamingToggle = page.locator('input[type="checkbox"]');

    // Initially enabled
    await expect(streamingToggle).toBeChecked();

    // Toggle off
    await streamingToggle.click();
    await expect(streamingToggle).not.toBeChecked();

    // Check label changes
    const label = page.locator('label:has(input[type="checkbox"])');
    await expect(label).toContainText('Standard');

    // Toggle back on
    await streamingToggle.click();
    await expect(streamingToggle).toBeChecked();
  });

  test('should show streaming indicator during streaming', async ({ page }) => {
    await page.goto('/');

    // Mock streaming SSE endpoint
    await page.route('**/api/v1/assist/query/stream', async (route) => {
      // Simulate SSE response
      const sseResponse = [
        'event: start',
        'data: {"message":"Starting"}',
        '',
        'event: chunk',
        'data: {"text":"Hello "}',
        '',
        'event: chunk',
        'data: {"text":"world"}',
        '',
        'event: complete',
        'data: {"answer":{"text":"Hello world","suggested_followups":[]},"session":{"id":"123","turn":1},"timings":{}}',
        '',
      ].join('\n');

      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseResponse,
      });
    });

    // Enable streaming
    const streamingToggle = page.locator('input[type="checkbox"]');
    await expect(streamingToggle).toBeChecked();

    // Enter query
    const input = page.locator('textarea[placeholder*="question"]');
    await input.fill('test question');
    await input.press('Enter');

    // Check streaming indicator appears
    const label = page.locator('label:has(input[type="checkbox"])');
    await expect(label).toContainText('Streaming...', { timeout: 2000 });

    // Wait for streaming to complete
    await expect(label).toContainText('Stream', { timeout: 5000 });
  });

  test('should display text incrementally during streaming', async ({ page }) => {
    await page.goto('/');

    // Mock streaming endpoint with delayed chunks
    await page.route('**/api/v1/assist/query/stream', async (route) => {
      const chunks = [
        'event: start\ndata: {"message":"Starting"}\n\n',
        'event: chunk\ndata: {"text":"First "}\n\n',
        'event: chunk\ndata: {"text":"second "}\n\n',
        'event: chunk\ndata: {"text":"third"}\n\n',
        'event: complete\ndata: {"answer":{"text":"First second third","suggested_followups":[]},"session":{"id":"123"},"timings":{}}\n\n',
      ];

      // Send chunks with delay
      const stream = chunks.join('');
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: stream,
      });
    });

    // Enter query
    const input = page.locator('textarea[placeholder*="question"]');
    await input.fill('test question');
    await input.press('Enter');

    // Wait for answer to appear
    const answerContainer = page.locator('[data-testid="answer-bubble"]').first();
    await expect(answerContainer).toBeVisible({ timeout: 5000 });

    // Final text should be complete
    await expect(answerContainer).toContainText('First second third', { timeout: 5000 });
  });

  test('should display citations during streaming', async ({ page }) => {
    await page.goto('/');

    // Mock streaming endpoint with citations
    await page.route('**/api/v1/assist/query/stream', async (route) => {
      const sseResponse = [
        'event: start',
        'data: {"message":"Starting"}',
        '',
        'event: citations',
        'data: {"citations":[{"id":1,"title":"Test Document","url":"https://example.com","content":"Test content","score":0.95}]}',
        '',
        'event: chunk',
        'data: {"text":"Based on the document..."}',
        '',
        'event: complete',
        'data: {"answer":{"text":"Based on the document...","suggested_followups":[]},"session":{"id":"123"},"timings":{}}',
        '',
      ].join('\n');

      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseResponse,
      });
    });

    // Enter query
    const input = page.locator('textarea[placeholder*="question"]');
    await input.fill('test question');
    await input.press('Enter');

    // Check citations panel appears
    const citationsPanel = page.locator('aside');
    await expect(citationsPanel).toBeVisible({ timeout: 5000 });

    // Check citation content
    await expect(citationsPanel).toContainText('Test Document');
  });

  test('should use standard mode when streaming is disabled', async ({ page }) => {
    await page.goto('/');

    // Disable streaming
    const streamingToggle = page.locator('input[type="checkbox"]');
    await streamingToggle.click();
    await expect(streamingToggle).not.toBeChecked();

    // Mock standard (non-streaming) endpoint
    let standardEndpointCalled = false;
    await page.route('**/api/v1/assist/query', async (route) => {
      standardEndpointCalled = true;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          answer: { text: 'Standard response', suggested_followups: [] },
          citations: [],
          session: { id: '123', turn: 1 },
          timings: {},
        }),
      });
    });

    // Enter query
    const input = page.locator('textarea[placeholder*="question"]');
    await input.fill('test question');
    await input.press('Enter');

    // Wait for response
    await page.waitForTimeout(1000);

    // Verify standard endpoint was called
    expect(standardEndpointCalled).toBe(true);
  });

  test('should handle streaming errors gracefully', async ({ page }) => {
    await page.goto('/');

    // Mock streaming endpoint with error
    await page.route('**/api/v1/assist/query/stream', async (route) => {
      const sseResponse = [
        'event: start',
        'data: {"message":"Starting"}',
        '',
        'event: error',
        'data: {"message":"Streaming failed"}',
        '',
      ].join('\n');

      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseResponse,
      });
    });

    // Enter query
    const input = page.locator('textarea[placeholder*="question"]');
    await input.fill('test question');
    await input.press('Enter');

    // Check error message appears
    const errorBanner = page.locator('[role="alert"]').first();
    await expect(errorBanner).toBeVisible({ timeout: 5000 });
    await expect(errorBanner).toContainText('Streaming failed');
  });

  test('should persist streaming preference', async ({ page }) => {
    await page.goto('/');

    // Disable streaming
    const streamingToggle = page.locator('input[type="checkbox"]');
    await streamingToggle.click();
    await expect(streamingToggle).not.toBeChecked();

    // Reload page
    await page.reload();

    // Check preference is persisted
    await expect(streamingToggle).not.toBeChecked();

    // Enable streaming again
    await streamingToggle.click();
    await expect(streamingToggle).toBeChecked();

    // Reload and verify
    await page.reload();
    await expect(streamingToggle).toBeChecked();
  });

  test('should handle network errors during streaming', async ({ page }) => {
    await page.goto('/');

    // Mock streaming endpoint to fail
    await page.route('**/api/v1/assist/query/stream', async (route) => {
      await route.abort('failed');
    });

    // Enter query
    const input = page.locator('textarea[placeholder*="question"]');
    await input.fill('test question');
    await input.press('Enter');

    // Check error message appears
    const errorBanner = page.locator('[role="alert"]').first();
    await expect(errorBanner).toBeVisible({ timeout: 5000 });
  });

  test('should support Unicode characters in streaming', async ({ page }) => {
    await page.goto('/');

    // Mock streaming endpoint with Unicode
    await page.route('**/api/v1/assist/query/stream', async (route) => {
      const sseResponse = [
        'event: chunk',
        'data: {"text":"日本語 "}',
        '',
        'event: chunk',
        'data: {"text":"テスト "}',
        '',
        'event: chunk',
        'data: {"text":"🚀"}',
        '',
        'event: complete',
        'data: {"answer":{"text":"日本語 テスト 🚀","suggested_followups":[]},"session":{"id":"123"},"timings":{}}',
        '',
      ].join('\n');

      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream; charset=utf-8',
        body: sseResponse,
      });
    });

    // Enter query
    const input = page.locator('textarea[placeholder*="question"]');
    await input.fill('test question');
    await input.press('Enter');

    // Check Unicode text appears correctly
    const answerContainer = page.locator('[data-testid="answer-bubble"]').first();
    await expect(answerContainer).toContainText('日本語 テスト 🚀', { timeout: 5000 });
  });
});
