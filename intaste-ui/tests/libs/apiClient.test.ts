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

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { submitFeedback, getModels, selectModel, checkHealth, APIError } from '@/libs/apiClient';
import { useUIStore } from '@/store/ui.store';
import type { FeedbackRequest, ModelSelectRequest } from '@/types/api';

describe('APIClient', () => {
  beforeEach(() => {
    // Set up API token
    useUIStore.setState({ apiToken: 'test-token' });

    // Reset fetch mock
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('API Error', () => {
    it('creates APIError with all properties', () => {
      const error = new APIError(404, 'NOT_FOUND', 'Resource not found', { resource: 'user' });

      expect(error.status).toBe(404);
      expect(error.code).toBe('NOT_FOUND');
      expect(error.message).toBe('Resource not found');
      expect(error.details).toEqual({ resource: 'user' });
      expect(error.name).toBe('APIError');
    });

    it('extends Error class', () => {
      const error = new APIError(500, 'SERVER_ERROR', 'Internal error');

      expect(error).toBeInstanceOf(Error);
      expect(error).toBeInstanceOf(APIError);
    });
  });

  describe('submitFeedback', () => {
    it('sends POST request to /assist/feedback', async () => {
      const mockResponse = { status: 'ok' };
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      });

      const request: FeedbackRequest = {
        session_id: 'session-123',
        turn: 1,
        rating: 'up',
        comment: 'Great answer!',
      };

      const result = await submitFeedback(request);

      expect(result).toEqual(mockResponse);
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/v1/assist/feedback',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(request),
        })
      );
    });

    it('includes authentication token in headers', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ status: 'ok' }),
      });

      await submitFeedback({
        session_id: 'test',
        turn: 1,
        rating: 'up',
      });

      const fetchCall = vi.mocked(global.fetch).mock.calls[0]!;
      const headers = fetchCall[1]!.headers as Headers;

      expect(headers.get('X-Intaste-Token')).toBe('test-token');
    });

    it('includes request ID in headers', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ status: 'ok' }),
      });

      await submitFeedback({
        session_id: 'test',
        turn: 1,
        rating: 'up',
      });

      const fetchCall = vi.mocked(global.fetch).mock.calls[0]!;
      const headers = fetchCall[1]!.headers as Headers;

      expect(headers.get('X-Request-ID')).toBeTruthy();
    });

    it('throws APIError on HTTP error', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 400,
        json: async () => ({
          code: 'INVALID_REQUEST',
          message: 'Invalid feedback data',
        }),
      });

      await expect(
        submitFeedback({
          session_id: 'test',
          turn: 1,
          rating: 'up',
        })
      ).rejects.toThrow(APIError);
    });
  });

  describe('getModels', () => {
    it('sends GET request to /models', async () => {
      const mockResponse = {
        models: [
          { name: 'gpt-oss', selected: true },
          { name: 'llama3', selected: false },
        ],
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await getModels();

      expect(result).toEqual(mockResponse);
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/v1/models',
        expect.objectContaining({
          headers: expect.any(Headers),
        })
      );
    });

    it('includes authentication token', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ models: [] }),
      });

      await getModels();

      const fetchCall = vi.mocked(global.fetch).mock.calls[0]!;
      const headers = fetchCall[1]!.headers as Headers;

      expect(headers.get('X-Intaste-Token')).toBe('test-token');
    });

    it('throws APIError on failure', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => ({
          code: 'INTERNAL_ERROR',
          message: 'Server error',
        }),
      });

      await expect(getModels()).rejects.toThrow(APIError);
    });
  });

  describe('selectModel', () => {
    it('sends POST request to /models/select', async () => {
      const mockResponse = { status: 'ok' };
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      });

      const request: ModelSelectRequest = {
        model: 'llama3',
        scope: 'default',
      };

      const result = await selectModel(request);

      expect(result).toEqual(mockResponse);
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/v1/models/select',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(request),
        })
      );
    });

    it('includes authentication token', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ status: 'ok' }),
      });

      await selectModel({ model: 'gpt-oss', scope: 'default' });

      const fetchCall = vi.mocked(global.fetch).mock.calls[0]!;
      const headers = fetchCall[1]!.headers as Headers;

      expect(headers.get('X-Intaste-Token')).toBe('test-token');
    });

    it('throws APIError on failure', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        json: async () => ({
          code: 'MODEL_NOT_FOUND',
          message: 'Model not found',
        }),
      });

      await expect(selectModel({ model: 'invalid', scope: 'default' })).rejects.toThrow(APIError);
    });
  });

  describe('checkHealth', () => {
    it('sends GET request to /health', async () => {
      const mockResponse = { status: 'healthy' };
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await checkHealth();

      expect(result).toEqual(mockResponse);
      expect(global.fetch).toHaveBeenCalledWith('/api/v1/health', expect.any(Object));
    });

    it('includes authentication token', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ status: 'healthy' }),
      });

      await checkHealth();

      const fetchCall = vi.mocked(global.fetch).mock.calls[0]!;
      const headers = fetchCall[1]!.headers as Headers;

      expect(headers.get('X-Intaste-Token')).toBe('test-token');
    });

    it('throws APIError on unhealthy status', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
        json: async () => ({
          code: 'SERVICE_UNAVAILABLE',
          message: 'Service is down',
        }),
      });

      await expect(checkHealth()).rejects.toThrow(APIError);
    });
  });

  describe('Error Handling', () => {
    it('handles network errors', async () => {
      global.fetch = vi.fn().mockRejectedValue(new Error('Network failure'));

      await expect(getModels()).rejects.toThrow(APIError);
      await expect(getModels()).rejects.toThrow('Network failure');
    });

    it('handles JSON parsing errors', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => {
          throw new Error('Invalid JSON');
        },
      });

      const error = await getModels().catch((e) => e);

      expect(error).toBeInstanceOf(APIError);
      expect(error.code).toBe('UNKNOWN_ERROR');
      expect(error.message).toContain('HTTP 500');
    });

    it('includes error details when available', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 400,
        json: async () => ({
          code: 'VALIDATION_ERROR',
          message: 'Invalid input',
          details: { field: 'rating', error: 'required' },
        }),
      });

      const error = await submitFeedback({
        session_id: 'test',
        turn: 1,
        rating: 'up',
      }).catch((e) => e);

      expect(error.details).toEqual({ field: 'rating', error: 'required' });
    });
  });

  describe('Request Configuration', () => {
    it('sets Content-Type header to application/json', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ status: 'ok' }),
      });

      await getModels();

      const fetchCall = vi.mocked(global.fetch).mock.calls[0]!;
      const headers = fetchCall[1]!.headers as Headers;

      expect(headers.get('Content-Type')).toBe('application/json');
    });

    it('uses no-store cache policy', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ status: 'ok' }),
      });

      await getModels();

      const fetchCall = vi.mocked(global.fetch).mock.calls[0]!;
      expect(fetchCall[1]!.cache).toBe('no-store');
    });

    it('constructs correct API URLs', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ status: 'ok' }),
      });

      await checkHealth();
      expect(vi.mocked(global.fetch).mock.calls[0]![0]).toBe('/api/v1/health');

      await getModels();
      expect(vi.mocked(global.fetch).mock.calls[1]![0]).toBe('/api/v1/models');

      await selectModel({ model: 'test', scope: 'default' });
      expect(vi.mocked(global.fetch).mock.calls[2]![0]).toBe('/api/v1/models/select');

      await submitFeedback({ session_id: 'test', turn: 1, rating: 'up' });
      expect(vi.mocked(global.fetch).mock.calls[3]![0]).toBe('/api/v1/assist/feedback');
    });
  });

  describe('Token Handling', () => {
    it('works without token when not set', async () => {
      useUIStore.setState({ apiToken: null });

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ status: 'ok' }),
      });

      await checkHealth();

      const fetchCall = vi.mocked(global.fetch).mock.calls[0]!;
      const headers = fetchCall[1]!.headers as Headers;

      expect(headers.get('X-Intaste-Token')).toBeNull();
    });

    it('updates token when UI store changes', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ status: 'ok' }),
      });

      await getModels();
      let fetchCall = vi.mocked(global.fetch).mock.calls[0]!;
      expect((fetchCall[1]!.headers as Headers).get('X-Intaste-Token')).toBe('test-token');

      // Update token
      useUIStore.setState({ apiToken: 'new-token' });

      await getModels();
      fetchCall = vi.mocked(global.fetch).mock.calls[1]!;
      expect((fetchCall[1]!.headers as Headers).get('X-Intaste-Token')).toBe('new-token');
    });
  });
});
