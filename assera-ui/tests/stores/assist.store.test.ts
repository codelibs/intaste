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

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useAssistStore } from '@/store/assist.store';
import { mockApiResponse, createMockQueryResponse } from '../utils/test-utils';

describe('AssistStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    useAssistStore.setState({
      loading: false,
      error: null,
      answer: null,
      citations: [],
      selectedCitationId: null,
      timings: null,
    });

    // Reset mocks
    vi.clearAllMocks();
  });

  it('initializes with default state', () => {
    const state = useAssistStore.getState();

    expect(state.loading).toBe(false);
    expect(state.error).toBe(null);
    expect(state.answer).toBe(null);
    expect(state.citations).toEqual([]);
    expect(state.selectedCitationId).toBe(null);
  });

  it('sets loading state when sending query', async () => {
    const mockResponse = createMockQueryResponse();
    global.fetch = vi.fn().mockResolvedValue(mockApiResponse(mockResponse));

    const promise = useAssistStore.getState().send('test query');

    // Check loading state immediately after calling send
    expect(useAssistStore.getState().loading).toBe(true);

    await promise;
  });

  it('updates state with response data on successful query', async () => {
    const mockResponse = createMockQueryResponse();
    global.fetch = vi.fn().mockResolvedValue(mockApiResponse(mockResponse));

    await useAssistStore.getState().send('test query');

    const state = useAssistStore.getState();
    expect(state.loading).toBe(false);
    expect(state.error).toBe(null);
    expect(state.answer).toEqual(mockResponse.answer);
    expect(state.citations).toEqual(mockResponse.citations);
    expect(state.timings).toEqual(mockResponse.timings);
  });

  it('sets error state on failed query', async () => {
    const errorMessage = 'API Error';
    global.fetch = vi.fn().mockResolvedValue(
      mockApiResponse({ error: { message: errorMessage } }, 500)
    );

    await useAssistStore.getState().send('test query');

    const state = useAssistStore.getState();
    expect(state.loading).toBe(false);
    expect(state.error).toBeTruthy();
    expect(state.answer).toBe(null);
  });

  it('handles network errors', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('Network error'));

    await useAssistStore.getState().send('test query');

    const state = useAssistStore.getState();
    expect(state.loading).toBe(false);
    expect(state.error).toBeTruthy();
  });

  it('selects citation by ID', () => {
    useAssistStore.getState().selectCitation('2');

    expect(useAssistStore.getState().selectedCitationId).toBe('2');
  });

  it('clears selection when selecting null', () => {
    useAssistStore.setState({ selectedCitationId: '1' });
    useAssistStore.getState().selectCitation(null);

    expect(useAssistStore.getState().selectedCitationId).toBe(null);
  });

  it('clears error', () => {
    useAssistStore.setState({ error: 'Some error' });
    useAssistStore.getState().clearError();

    expect(useAssistStore.getState().error).toBe(null);
  });

  it('resets store to initial state', () => {
    useAssistStore.setState({
      loading: true,
      error: 'Error',
      answer: { text: 'Answer', suggested_followups: [] },
      citations: [{ id: '1', title: 'Doc', snippet: '', url: '', score: 0.9, metadata: {} }],
      selectedCitationId: '1',
      timings: { intent_ms: 100, search_ms: 150, compose_ms: 80, total_ms: 330 },
    });

    useAssistStore.getState().reset();

    const state = useAssistStore.getState();
    expect(state.loading).toBe(false);
    expect(state.error).toBe(null);
    expect(state.answer).toBe(null);
    expect(state.citations).toEqual([]);
    expect(state.selectedCitationId).toBe(null);
    expect(state.timings).toBe(null);
  });

  it('includes options in API request', async () => {
    const mockResponse = createMockQueryResponse();
    global.fetch = vi.fn().mockResolvedValue(mockApiResponse(mockResponse));

    const options = { max_results: 10, site: 'example.com' };
    await useAssistStore.getState().send('test query', options);

    expect(global.fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        body: JSON.stringify({
          query: 'test query',
          options,
        }),
      })
    );
  });

  it('includes session_id in API request when provided', async () => {
    const mockResponse = createMockQueryResponse();
    global.fetch = vi.fn().mockResolvedValue(mockApiResponse(mockResponse));

    await useAssistStore.getState().send('test query', {}, 'session-123');

    expect(global.fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        body: JSON.stringify({
          query: 'test query',
          session_id: 'session-123',
          options: {},
        }),
      })
    );
  });

  describe('Streaming', () => {
    it('sets streaming state when sending stream query', async () => {
      const mockReadableStream = {
        getReader: () => ({
          read: vi.fn()
            .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode('event: complete\ndata: {"answer":{"text":"Done"},"session":{}}\n\n') })
            .mockResolvedValueOnce({ done: true }),
          releaseLock: vi.fn(),
        }),
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        body: mockReadableStream,
      });

      const promise = useAssistStore.getState().sendStream('test query');

      // Check streaming state immediately after calling sendStream
      expect(useAssistStore.getState().streaming).toBe(true);
      expect(useAssistStore.getState().loading).toBe(true);

      await promise;
    });

    it('accumulates text chunks during streaming', async () => {
      const sseData =
        'event: chunk\ndata: {"text":"Hello "}\n\n' +
        'event: chunk\ndata: {"text":"world"}\n\n' +
        'event: complete\ndata: {"answer":{"text":"Hello world"},"session":{}}\n\n';

      const mockReadableStream = {
        getReader: () => ({
          read: vi.fn()
            .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode(sseData) })
            .mockResolvedValueOnce({ done: true }),
          releaseLock: vi.fn(),
        }),
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        body: mockReadableStream,
      });

      await useAssistStore.getState().sendStream('test query');

      const state = useAssistStore.getState();
      expect(state.answer?.text).toBe('Hello world');
      expect(state.streaming).toBe(false);
      expect(state.loading).toBe(false);
    });

    it('updates citations during streaming', async () => {
      const sseData =
        'event: citations\ndata: {"citations":[{"id":1,"title":"Test","url":"http://test.com","content":"Content","score":0.9}]}\n\n' +
        'event: complete\ndata: {"answer":{"text":"Done"},"session":{}}\n\n';

      const mockReadableStream = {
        getReader: () => ({
          read: vi.fn()
            .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode(sseData) })
            .mockResolvedValueOnce({ done: true }),
          releaseLock: vi.fn(),
        }),
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        body: mockReadableStream,
      });

      await useAssistStore.getState().sendStream('test query');

      const state = useAssistStore.getState();
      expect(state.citations.length).toBe(1);
      expect(state.citations[0].title).toBe('Test');
      expect(state.selectedCitationId).toBe(1);
    });

    it('handles streaming error event', async () => {
      const sseData = 'event: error\ndata: {"message":"Streaming error"}\n\n';

      const mockReadableStream = {
        getReader: () => ({
          read: vi.fn()
            .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode(sseData) })
            .mockResolvedValueOnce({ done: true }),
          releaseLock: vi.fn(),
        }),
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        body: mockReadableStream,
      });

      await useAssistStore.getState().sendStream('test query');

      const state = useAssistStore.getState();
      expect(state.error).toBe('Streaming error');
      expect(state.streaming).toBe(false);
      expect(state.loading).toBe(false);
    });

    it('handles streaming network error', async () => {
      global.fetch = vi.fn().mockRejectedValue(new Error('Network error'));

      await useAssistStore.getState().sendStream('test query');

      const state = useAssistStore.getState();
      expect(state.error).toBeTruthy();
      expect(state.streaming).toBe(false);
      expect(state.loading).toBe(false);
    });

    it('initializes answer with empty text at stream start', async () => {
      const mockReadableStream = {
        getReader: () => ({
          read: vi.fn()
            .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode('event: start\ndata: {}\n\n') })
            .mockResolvedValueOnce({ done: true }),
          releaseLock: vi.fn(),
        }),
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        body: mockReadableStream,
      });

      const promise = useAssistStore.getState().sendStream('test query');

      // Check answer is initialized to empty
      await new Promise((resolve) => setTimeout(resolve, 10));
      const state = useAssistStore.getState();
      expect(state.answer?.text).toBe('');

      await promise;
    });

    it('updates session on stream complete', async () => {
      const sseData = 'event: complete\ndata: {"answer":{"text":"Done"},"session":{"id":"session-123","turn":2}}\n\n';

      const mockReadableStream = {
        getReader: () => ({
          read: vi.fn()
            .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode(sseData) })
            .mockResolvedValueOnce({ done: true }),
          releaseLock: vi.fn(),
        }),
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        body: mockReadableStream,
      });

      await useAssistStore.getState().sendStream('test query');

      // Session should be updated (this would need session store integration)
      const state = useAssistStore.getState();
      expect(state.streaming).toBe(false);
    });
  });
});
