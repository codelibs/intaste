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
 * UUID generation utility with fallback for non-secure contexts.
 *
 * crypto.randomUUID() requires a secure context (HTTPS or localhost).
 * This utility provides a fallback implementation for HTTP environments.
 */

/**
 * Generate a RFC 4122 version 4 compliant UUID.
 *
 * Prefers crypto.randomUUID() when available in secure contexts.
 * Falls back to Math.random() based implementation in non-secure contexts.
 *
 * @returns A UUID string in the format xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
 */
export function generateUUID(): string {
  // Try to use native crypto.randomUUID() if available
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    try {
      return crypto.randomUUID();
    } catch {
      // Fall through to fallback implementation
      // This can happen in non-secure contexts (HTTP, not localhost)
    }
  }

  // Fallback: RFC 4122 version 4 UUID implementation
  // Using Math.random() - not cryptographically secure but sufficient for request IDs
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}
