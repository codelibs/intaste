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
 * Type definitions matching Intaste API schemas.
 */

/**
 * Citation from search results with document metadata.
 *
 * Citations represent individual search results returned by Fess,
 * displayed in the evidence panel with snippets showing search context.
 */
export interface Citation {
  /** Unique identifier for this citation (1-indexed) */
  id: number;

  /** Document title */
  title: string;

  /**
   * HTML snippet excerpt from the document showing search context.
   *
   * **SECURITY WARNING:** This field contains HTML from Fess search results,
   * including highlighted search terms wrapped in `<em>` tags. The content
   * originates from indexed documents and may contain arbitrary HTML.
   *
   * **MUST be sanitized** before rendering to prevent XSS attacks.
   * Use `sanitizeHtml()` from `@/libs/sanitizer` when rendering with
   * `dangerouslySetInnerHTML`.
   *
   * @example
   * "This is a <em>search result</em> with highlighted terms"
   */
  snippet?: string;

  /** URL to the original document in Fess */
  url: string;

  /** Relevance score (0.0 - 1.0), higher is more relevant */
  score?: number;

  /** Additional metadata about the document (e.g., content_type, site) */
  meta?: Record<string, any>;
}

export interface Answer {
  text: string;
  suggested_questions?: string[];
}

export interface Session {
  id: string;
  turn: number;
}

export interface Timings {
  llm_ms: number;
  search_ms: number;
  total_ms: number;
}

export interface Notice {
  fallback?: boolean;
  reason?: string;
}

export interface AssistQueryRequest {
  query: string;
  session_id?: string;
  query_history?: string[];
  options?: {
    max_results?: number;
    language?: string;
    filters?: Record<string, any>;
    timeout_ms?: number;
  };
}

export interface AssistQueryResponse {
  answer: Answer;
  citations: Citation[];
  session: Session;
  timings: Timings;
  notice?: Notice;
}

export interface FeedbackRequest {
  session_id: string;
  turn: number;
  rating: 'up' | 'down';
  comment?: string;
}

export interface ModelsResponse {
  default: string;
  available: string[];
  selected_per_session: Record<string, string>;
}

export interface ModelSelectRequest {
  model: string;
  scope: 'default' | 'session';
  session_id?: string;
}

export interface ErrorResponse {
  code: string;
  message: string;
  details?: Record<string, any>;
  request_id?: string;
}
