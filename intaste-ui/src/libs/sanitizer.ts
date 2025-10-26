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
 * HTML sanitizer using DOMPurify for XSS prevention.
 *
 * This module provides secure HTML sanitization for user-generated and external content,
 * particularly search result snippets from Fess that may contain arbitrary HTML.
 *
 * @module sanitizer
 */

import DOMPurify from 'dompurify';

/**
 * Sanitize HTML content from search snippets to prevent XSS attacks.
 *
 * This function uses DOMPurify to remove potentially malicious HTML while preserving
 * safe formatting tags commonly used in search result snippets. This is critical for
 * security as Fess search results may contain HTML snippets with highlighted search terms.
 *
 * **Security measures:**
 * - Removes all script tags and inline event handlers (onclick, onerror, etc.)
 * - Blocks dangerous URL schemes (javascript:, data:, vbscript:)
 * - Strips all unsafe HTML tags (iframe, object, embed, form, etc.)
 * - Allows only safe formatting tags: em, strong, mark, a
 * - Restricts anchor attributes to href and title only
 * - Only allows HTTP/HTTPS URLs in href attributes
 *
 * **Allowed tags and attributes:**
 * - `<em>`, `<strong>`, `<mark>`: Formatting tags (no attributes)
 * - `<a href="..." title="...">`: Links with href (http/https only) and title
 *
 * **Server-side rendering:**
 * When running on the server (window undefined), falls back to iteratively
 * stripping all HTML tags until no tags remain. This prevents bypass attacks
 * from malformed or overlapping tags (e.g., <<script>script>).
 *
 * @param dirty - The potentially unsafe HTML string to sanitize
 * @returns Sanitized HTML string safe for rendering with dangerouslySetInnerHTML
 *
 * @example
 * ```typescript
 * // Safe content is preserved
 * sanitizeHtml('Text with <em>emphasis</em>')
 * // => 'Text with <em>emphasis</em>'
 *
 * // Malicious scripts are removed
 * sanitizeHtml('<script>alert("xss")</script>Safe text')
 * // => 'Safe text'
 *
 * // Inline handlers are removed
 * sanitizeHtml('<div onclick="alert()">Click</div>')
 * // => '<div>Click</div>' (div removed as it's not in allowed tags, only text remains)
 *
 * // Safe links are preserved
 * sanitizeHtml('<a href="https://example.com">Link</a>')
 * // => '<a href="https://example.com">Link</a>'
 * ```
 *
 * @see {@link https://github.com/cure53/DOMPurify DOMPurify Documentation}
 */
export function sanitizeHtml(dirty: string): string {
  if (typeof window === 'undefined') {
    // Server-side: iteratively remove all HTML tags to prevent bypass attacks
    // from malformed or overlapping tags (e.g., <<script>script>)
    let sanitized = dirty;
    let previous;
    let iterations = 0;
    const MAX_ITERATIONS = 10; // Safety limit to prevent DoS

    do {
      previous = sanitized;
      // Remove both complete tags (<...>) and orphaned < or > characters
      sanitized = sanitized.replace(/<[^>]*>|[<>]/g, '');
      iterations++;
    } while (sanitized !== previous && iterations < MAX_ITERATIONS);

    return sanitized;
  }

  return DOMPurify.sanitize(dirty, {
    ALLOWED_TAGS: ['em', 'strong', 'mark', 'a'],
    ALLOWED_ATTR: ['href', 'title'],
    ALLOWED_URI_REGEXP: /^https?:\/\//,
  });
}
