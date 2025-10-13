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

import { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';

/**
 * Custom render function for testing with providers
 */
export function renderWithProviders(ui: ReactElement, options?: Omit<RenderOptions, 'wrapper'>) {
  return render(ui, { ...options });
}

/**
 * Mock API response helper
 */
export function mockApiResponse(data: any, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => data,
    headers: new Headers(),
  };
}

/**
 * Mock Citation data
 */
export function createMockCitation(id: string = '1') {
  return {
    id: parseInt(id, 10),
    title: `Test Document ${id}`,
    snippet: 'This is a test document snippet',
    url: `http://example.com/doc${id}`,
    score: 0.9,
    meta: {
      site: 'example.com',
      content_type: 'html',
    },
  };
}

/**
 * Mock Answer data
 */
export function createMockAnswer() {
  return {
    text: 'This is a test answer [1][2]',
    suggested_questions: ['What else?', 'Tell me more'],
  };
}

/**
 * Mock AssistQueryResponse
 */
export function createMockQueryResponse() {
  return {
    answer: createMockAnswer(),
    citations: [createMockCitation('1'), createMockCitation('2')],
    session: {
      id: 'test-session-id',
      turn: 1,
    },
    timings: {
      llm_ms: 100,
      search_ms: 150,
      total_ms: 330,
    },
  };
}

// Re-export everything from testing-library
export * from '@testing-library/react';
