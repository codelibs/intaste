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
 * Tests for streaming client
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { queryAssistStream } from '@/libs/streamingClient';
import { APIError } from '@/libs/apiClient';
import { useUIStore } from '@/store/ui.store';

// Mock the store
vi.mock('@/store/ui.store', () => ({
  useUIStore: {
    getState: vi.fn(() => ({
      apiToken: 'test-token',
    })),
  },
}));

describe('streamingClient', () => {
  beforeEach(() => {
    // Reset the mock implementation
    vi.mocked(useUIStore.getState).mockReturnValue({
      apiToken: 'test-token',
    } as any);

    // Mock fetch
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('should call fetch with correct parameters', async () => {
    const mockReadableStream = {
      getReader: () => ({
        read: vi.fn()
          .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode('event: start\ndata: {}\n\n') })
          .mockResolvedValueOnce({ done: true }),
        releaseLock: vi.fn(),
      }),
    };

    (global.fetch as any).mockResolvedValue({
      ok: true,
      body: mockReadableStream,
    });

    await queryAssistStream('test query', {}, undefined, {});

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/assist/query/stream'),
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
          'X-Assera-Token': 'test-token',
          'Accept': 'text/event-stream',
        }),
      })
    );
  });

  it('should throw error if no API token', async () => {
    // Mock store to return null token
    vi.mocked(useUIStore.getState).mockReturnValue({
      apiToken: null,
    } as any);

    await expect(queryAssistStream('test', {}, undefined, {}))
      .rejects.toThrow('API token not configured');
  });

  it('should throw APIError on HTTP error response with structured error data', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({
        code: 'INTERNAL_SERVER_ERROR',
        message: 'Server error',
        details: { reason: 'Database connection failed' }
      }),
    });

    await expect(queryAssistStream('test', {}, undefined, {}))
      .rejects.toThrow(APIError);

    try {
      await queryAssistStream('test', {}, undefined, {});
    } catch (error) {
      expect(error).toBeInstanceOf(APIError);
      expect((error as APIError).status).toBe(500);
      expect((error as APIError).code).toBe('INTERNAL_SERVER_ERROR');
      expect((error as APIError).message).toBe('Server error');
      expect((error as APIError).details).toEqual({ reason: 'Database connection failed' });
    }
  });

  it('should throw APIError with fallback data when response is not JSON', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: false,
      status: 503,
      json: async () => {
        throw new Error('Invalid JSON');
      },
    });

    try {
      await queryAssistStream('test', {}, undefined, {});
    } catch (error) {
      expect(error).toBeInstanceOf(APIError);
      expect((error as APIError).status).toBe(503);
      expect((error as APIError).code).toBe('HTTP_ERROR');
      expect((error as APIError).message).toBe('HTTP 503');
      expect((error as APIError).details).toBeUndefined();
    }
  });

  it('should call onStart callback on start event', async () => {
    const onStart = vi.fn();
    const sseData = 'event: start\ndata: {"message":"Starting"}\n\n';

    const mockReadableStream = {
      getReader: () => ({
        read: vi.fn()
          .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode(sseData) })
          .mockResolvedValueOnce({ done: true }),
        releaseLock: vi.fn(),
      }),
    };

    (global.fetch as any).mockResolvedValue({
      ok: true,
      body: mockReadableStream,
    });

    await queryAssistStream('test', {}, undefined, { onStart });

    expect(onStart).toHaveBeenCalledWith({ message: 'Starting' });
  });

  it('should call onIntent callback on intent event', async () => {
    const onIntent = vi.fn();
    const sseData = 'event: intent\ndata: {"optimized_query":"test query"}\n\n';

    const mockReadableStream = {
      getReader: () => ({
        read: vi.fn()
          .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode(sseData) })
          .mockResolvedValueOnce({ done: true }),
        releaseLock: vi.fn(),
      }),
    };

    (global.fetch as any).mockResolvedValue({
      ok: true,
      body: mockReadableStream,
    });

    await queryAssistStream('test', {}, undefined, { onIntent });

    expect(onIntent).toHaveBeenCalledWith({ optimized_query: 'test query' });
  });

  it('should call onCitations callback on citations event', async () => {
    const onCitations = vi.fn();
    const sseData = 'event: citations\ndata: {"citations":[{"id":1,"title":"Test"}]}\n\n';

    const mockReadableStream = {
      getReader: () => ({
        read: vi.fn()
          .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode(sseData) })
          .mockResolvedValueOnce({ done: true }),
        releaseLock: vi.fn(),
      }),
    };

    (global.fetch as any).mockResolvedValue({
      ok: true,
      body: mockReadableStream,
    });

    await queryAssistStream('test', {}, undefined, { onCitations });

    expect(onCitations).toHaveBeenCalledWith({ citations: [{ id: 1, title: 'Test' }] });
  });

  it('should call onChunk callback for each chunk event', async () => {
    const onChunk = vi.fn();
    const sseData =
      'event: chunk\ndata: {"text":"Hello "}\n\n' +
      'event: chunk\ndata: {"text":"world"}\n\n';

    const mockReadableStream = {
      getReader: () => ({
        read: vi.fn()
          .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode(sseData) })
          .mockResolvedValueOnce({ done: true }),
        releaseLock: vi.fn(),
      }),
    };

    (global.fetch as any).mockResolvedValue({
      ok: true,
      body: mockReadableStream,
    });

    await queryAssistStream('test', {}, undefined, { onChunk });

    expect(onChunk).toHaveBeenCalledTimes(2);
    expect(onChunk).toHaveBeenNthCalledWith(1, { text: 'Hello ' });
    expect(onChunk).toHaveBeenNthCalledWith(2, { text: 'world' });
  });

  it('should call onComplete callback on complete event', async () => {
    const onComplete = vi.fn();
    const sseData = 'event: complete\ndata: {"answer":{"text":"Done"},"session":{"id":"123"}}\n\n';

    const mockReadableStream = {
      getReader: () => ({
        read: vi.fn()
          .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode(sseData) })
          .mockResolvedValueOnce({ done: true }),
        releaseLock: vi.fn(),
      }),
    };

    (global.fetch as any).mockResolvedValue({
      ok: true,
      body: mockReadableStream,
    });

    await queryAssistStream('test', {}, undefined, { onComplete });

    expect(onComplete).toHaveBeenCalledWith({
      answer: { text: 'Done' },
      session: { id: '123' },
    });
  });

  it('should call onError callback on error event', async () => {
    const onError = vi.fn();
    const sseData = 'event: error\ndata: {"message":"Error occurred"}\n\n';

    const mockReadableStream = {
      getReader: () => ({
        read: vi.fn()
          .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode(sseData) })
          .mockResolvedValueOnce({ done: true }),
        releaseLock: vi.fn(),
      }),
    };

    (global.fetch as any).mockResolvedValue({
      ok: true,
      body: mockReadableStream,
    });

    await queryAssistStream('test', {}, undefined, { onError });

    expect(onError).toHaveBeenCalledWith({ message: 'Error occurred' });
  });

  it('should handle partial SSE messages across chunks', async () => {
    const onChunk = vi.fn();

    // Split an SSE message across multiple chunks
    const chunk1 = 'event: chunk\n';
    const chunk2 = 'data: {"text":"split"}\n\n';

    const mockReadableStream = {
      getReader: () => ({
        read: vi.fn()
          .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode(chunk1) })
          .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode(chunk2) })
          .mockResolvedValueOnce({ done: true }),
        releaseLock: vi.fn(),
      }),
    };

    (global.fetch as any).mockResolvedValue({
      ok: true,
      body: mockReadableStream,
    });

    await queryAssistStream('test', {}, undefined, { onChunk });

    expect(onChunk).toHaveBeenCalledWith({ text: 'split' });
  });

  it('should handle multiple events in single chunk', async () => {
    const onChunk = vi.fn();
    const sseData =
      'event: chunk\ndata: {"text":"First"}\n\n' +
      'event: chunk\ndata: {"text":"Second"}\n\n';

    const mockReadableStream = {
      getReader: () => ({
        read: vi.fn()
          .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode(sseData) })
          .mockResolvedValueOnce({ done: true }),
        releaseLock: vi.fn(),
      }),
    };

    (global.fetch as any).mockResolvedValue({
      ok: true,
      body: mockReadableStream,
    });

    await queryAssistStream('test', {}, undefined, { onChunk });

    expect(onChunk).toHaveBeenCalledTimes(2);
    expect(onChunk).toHaveBeenNthCalledWith(1, { text: 'First' });
    expect(onChunk).toHaveBeenNthCalledWith(2, { text: 'Second' });
  });

  it('should include session_id in request if provided', async () => {
    const mockReadableStream = {
      getReader: () => ({
        read: vi.fn()
          .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode('event: start\ndata: {}\n\n') })
          .mockResolvedValueOnce({ done: true }),
        releaseLock: vi.fn(),
      }),
    };

    (global.fetch as any).mockResolvedValue({
      ok: true,
      body: mockReadableStream,
    });

    await queryAssistStream('test', {}, 'session-123', {});

    const fetchCall = (global.fetch as any).mock.calls[0];
    const body = JSON.parse(fetchCall[1].body);
    expect(body.session_id).toBe('session-123');
  });

  it('should handle Unicode characters in streaming', async () => {
    const onChunk = vi.fn();
    const sseData = 'event: chunk\ndata: {"text":"日本語 🚀"}\n\n';

    const mockReadableStream = {
      getReader: () => ({
        read: vi.fn()
          .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode(sseData) })
          .mockResolvedValueOnce({ done: true }),
        releaseLock: vi.fn(),
      }),
    };

    (global.fetch as any).mockResolvedValue({
      ok: true,
      body: mockReadableStream,
    });

    await queryAssistStream('test', {}, undefined, { onChunk });

    expect(onChunk).toHaveBeenCalledWith({ text: '日本語 🚀' });
  });
});
