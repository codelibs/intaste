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
 * API client for Intaste backend.
 */

import type {
  AssistQueryRequest,
  AssistQueryResponse,
  ErrorResponse,
  FeedbackRequest,
  ModelSelectRequest,
  ModelsResponse,
} from '@/types/api';
import { useUIStore } from '@/store/ui.store';
import { generateUUID } from '@/libs/uuid';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || '/api/v1';

class APIError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details?: Record<string, any>
  ) {
    super(message);
    this.name = 'APIError';
  }
}

/**
 * Generic API fetch wrapper with authentication and error handling.
 */
async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = typeof window !== 'undefined' ? useUIStore.getState().apiToken : null;

  const headers = new Headers(init.headers);
  headers.set('Content-Type', 'application/json');

  if (token) {
    headers.set('X-Intaste-Token', token);
  }

  // Add request ID for tracing
  headers.set('X-Request-ID', generateUUID());

  const url = `${API_BASE}${path}`;

  try {
    const response = await fetch(url, {
      ...init,
      headers,
      cache: 'no-store',
    });

    if (!response.ok) {
      const error: ErrorResponse = await response.json().catch(() => ({
        code: 'UNKNOWN_ERROR',
        message: `HTTP ${response.status}`,
      }));

      throw new APIError(response.status, error.code, error.message, error.details);
    }

    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }

    // Network or parsing error
    throw new APIError(
      0,
      'NETWORK_ERROR',
      error instanceof Error ? error.message : 'Network error occurred'
    );
  }
}

/**
 * Execute assisted search query.
 */
export async function queryAssist(request: AssistQueryRequest): Promise<AssistQueryResponse> {
  return apiFetch<AssistQueryResponse>('/assist/query', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * Submit feedback on a response.
 */
export async function submitFeedback(request: FeedbackRequest): Promise<{ status: string }> {
  return apiFetch<{ status: string }>('/assist/feedback', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * Get available models.
 */
export async function getModels(): Promise<ModelsResponse> {
  return apiFetch<ModelsResponse>('/models');
}

/**
 * Select a model.
 */
export async function selectModel(request: ModelSelectRequest): Promise<{ status: string }> {
  return apiFetch<{ status: string }>('/models/select', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * Check API health.
 */
export async function checkHealth(): Promise<{ status: string }> {
  return apiFetch<{ status: string }>('/health');
}

export { APIError };
