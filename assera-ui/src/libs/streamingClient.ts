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
 * Streaming API client using Server-Sent Events (SSE)
 */

import { useUIStore } from '@/store/ui.store';
import { APIError } from '@/libs/apiClient';
import { generateUUID } from '@/libs/uuid';
import type { ErrorResponse } from '@/types/api';

export interface StreamEvent {
  event: string;
  data: any;
}

export interface StreamCallbacks {
  onStart?: (data: any) => void;
  onIntent?: (data: any) => void;
  onCitations?: (data: any) => void;
  onChunk?: (data: { text: string }) => void;
  onComplete?: (data: any) => void;
  onError?: (data: any) => void;
}

/**
 * Query assist API with streaming response
 */
export async function queryAssistStream(
  query: string,
  options: Record<string, any> = {},
  sessionId?: string,
  callbacks?: StreamCallbacks
): Promise<void> {
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || '/api/v1';
  const url = `${API_BASE}/assist/query/stream`;

  // Get API token from store
  const token = useUIStore.getState().apiToken;
  if (!token) {
    throw new Error('API token not configured');
  }

  // Prepare request body
  const body = {
    query,
    options,
    ...(sessionId && { session_id: sessionId }),
  };

  // Make POST request with SSE
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Assera-Token': token,
      'X-Request-ID': generateUUID(),
      'Accept': 'text/event-stream',
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const error: ErrorResponse = await response.json().catch(() => ({
      code: 'HTTP_ERROR',
      message: `HTTP ${response.status}`,
    }));

    throw new APIError(
      response.status,
      error.code,
      error.message,
      error.details
    );
  }

  if (!response.body) {
    throw new Error('Response body is null');
  }

  // Process SSE stream
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) break;

      // Decode chunk and add to buffer
      buffer += decoder.decode(value, { stream: true });

      // Process complete messages
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || ''; // Keep incomplete message in buffer

      for (const line of lines) {
        if (!line.trim()) continue;

        // Parse SSE message
        const eventMatch = line.match(/^event: (.+)$/m);
        const dataMatch = line.match(/^data: (.+)$/m);

        if (eventMatch && dataMatch) {
          const event = eventMatch[1];
          const data = JSON.parse(dataMatch[1]);

          // Call appropriate callback
          switch (event) {
            case 'start':
              callbacks?.onStart?.(data);
              break;
            case 'intent':
              callbacks?.onIntent?.(data);
              break;
            case 'citations':
              callbacks?.onCitations?.(data);
              break;
            case 'chunk':
              callbacks?.onChunk?.(data);
              break;
            case 'complete':
              callbacks?.onComplete?.(data);
              break;
            case 'error':
              callbacks?.onError?.(data);
              break;
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

/**
 * Create an AbortController for canceling streaming requests
 */
export function createStreamAbortController(): AbortController {
  return new AbortController();
}
