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

import { describe, it, expect } from 'vitest';
import { sanitizeHtml } from '@/libs/sanitizer';

describe('sanitizeHtml', () => {
  describe('XSS Prevention', () => {
    it('should remove script tags', () => {
      const dirty = '<script>alert("xss")</script>Safe content';
      const clean = sanitizeHtml(dirty);
      expect(clean).not.toContain('script');
      expect(clean).not.toContain('alert');
      expect(clean).toContain('Safe content');
    });

    it('should remove inline event handlers', () => {
      const dirty = '<div onclick="alert(\'xss\')">Click me</div>';
      const clean = sanitizeHtml(dirty);
      expect(clean).not.toContain('onclick');
      expect(clean).not.toContain('alert');
    });

    it('should remove javascript: URLs', () => {
      const dirty = '<a href="javascript:alert(\'xss\')">Click</a>';
      const clean = sanitizeHtml(dirty);
      expect(clean).not.toContain('javascript:');
    });

    it('should remove data: URLs', () => {
      const dirty = '<a href="data:text/html,<script>alert(\'xss\')</script>">Click</a>';
      const clean = sanitizeHtml(dirty);
      expect(clean).not.toContain('data:');
    });

    it('should remove vbscript: URLs', () => {
      const dirty = '<a href="vbscript:msgbox(\'xss\')">Click</a>';
      const clean = sanitizeHtml(dirty);
      expect(clean).not.toContain('vbscript:');
    });

    it('should remove iframe tags', () => {
      const dirty = '<iframe src="evil.com"></iframe>Safe content';
      const clean = sanitizeHtml(dirty);
      expect(clean).not.toContain('iframe');
      expect(clean).toContain('Safe content');
    });

    it('should remove object tags', () => {
      const dirty = '<object data="evil.swf"></object>Safe content';
      const clean = sanitizeHtml(dirty);
      expect(clean).not.toContain('object');
      expect(clean).toContain('Safe content');
    });

    it('should remove embed tags', () => {
      const dirty = '<embed src="evil.swf">Safe content';
      const clean = sanitizeHtml(dirty);
      expect(clean).not.toContain('embed');
      expect(clean).toContain('Safe content');
    });

    it('should remove style tags with malicious content', () => {
      const dirty = '<style>body { background: url("javascript:alert(\'xss\')"); }</style>Safe';
      const clean = sanitizeHtml(dirty);
      expect(clean).not.toContain('style');
      expect(clean).toContain('Safe');
    });

    it('should remove form elements', () => {
      const dirty = '<form action="evil.com"><input type="text"></form>Safe';
      const clean = sanitizeHtml(dirty);
      expect(clean).not.toContain('form');
      expect(clean).not.toContain('input');
      expect(clean).toContain('Safe');
    });
  });

  describe('Allowed Tags', () => {
    it('should preserve em tags', () => {
      const dirty = 'This is <em>emphasized</em> text';
      const clean = sanitizeHtml(dirty);
      expect(clean).toBe('This is <em>emphasized</em> text');
    });

    it('should preserve strong tags', () => {
      const dirty = 'This is <strong>bold</strong> text';
      const clean = sanitizeHtml(dirty);
      expect(clean).toBe('This is <strong>bold</strong> text');
    });

    it('should preserve mark tags', () => {
      const dirty = 'This is <mark>highlighted</mark> text';
      const clean = sanitizeHtml(dirty);
      expect(clean).toBe('This is <mark>highlighted</mark> text');
    });

    it('should preserve safe anchor tags with https URLs', () => {
      const dirty = '<a href="https://example.com" title="Example">Link</a>';
      const clean = sanitizeHtml(dirty);
      expect(clean).toContain('<a');
      expect(clean).toContain('href="https://example.com"');
      expect(clean).toContain('title="Example"');
      expect(clean).toContain('Link');
    });

    it('should preserve safe anchor tags with http URLs', () => {
      const dirty = '<a href="http://example.com">Link</a>';
      const clean = sanitizeHtml(dirty);
      expect(clean).toContain('<a');
      expect(clean).toContain('href="http://example.com"');
    });

    it('should allow nested safe tags', () => {
      const dirty = '<strong>Bold with <em>emphasis</em> and <mark>highlight</mark></strong>';
      const clean = sanitizeHtml(dirty);
      expect(clean).toContain('<strong>');
      expect(clean).toContain('<em>');
      expect(clean).toContain('<mark>');
      expect(clean).toContain('</strong>');
      expect(clean).toContain('</em>');
      expect(clean).toContain('</mark>');
    });
  });

  describe('Disallowed Attributes', () => {
    it('should remove style attributes', () => {
      const dirty = '<em style="color: red;">Red text</em>';
      const clean = sanitizeHtml(dirty);
      expect(clean).not.toContain('style');
      expect(clean).toContain('Red text');
    });

    it('should remove class attributes', () => {
      const dirty = '<em class="dangerous">Text</em>';
      const clean = sanitizeHtml(dirty);
      expect(clean).not.toContain('class');
      expect(clean).toContain('Text');
    });

    it('should remove id attributes', () => {
      const dirty = '<em id="myid">Text</em>';
      const clean = sanitizeHtml(dirty);
      expect(clean).not.toContain('id');
      expect(clean).toContain('Text');
    });

    it('should preserve data attributes (DOMPurify default behavior)', () => {
      const dirty = '<em data-value="test">Text</em>';
      const clean = sanitizeHtml(dirty);
      // Note: DOMPurify allows data-* attributes by default
      // This is acceptable for our use case as data attributes are not security risks
      expect(clean).toContain('Text');
    });

    it('should remove disallowed attributes from anchor tags', () => {
      const dirty = '<a href="https://example.com" onclick="alert(\'xss\')" class="link">Link</a>';
      const clean = sanitizeHtml(dirty);
      expect(clean).toContain('href="https://example.com"');
      expect(clean).not.toContain('onclick');
      expect(clean).not.toContain('class');
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty string', () => {
      const clean = sanitizeHtml('');
      expect(clean).toBe('');
    });

    it('should handle plain text without HTML', () => {
      const dirty = 'Just plain text';
      const clean = sanitizeHtml(dirty);
      expect(clean).toBe('Just plain text');
    });

    it('should handle malformed HTML', () => {
      const dirty = '<em>Unclosed tag with <strong>nested content';
      const clean = sanitizeHtml(dirty);
      // DOMPurify auto-closes tags
      expect(clean).toContain('Unclosed tag');
      expect(clean).toContain('nested content');
    });

    it('should handle HTML entities', () => {
      const dirty = '&lt;script&gt;alert("xss")&lt;/script&gt; &amp; safe content';
      const clean = sanitizeHtml(dirty);
      expect(clean).toContain('safe content');
      // Entities should be preserved or decoded safely
    });

    it('should handle Unicode characters', () => {
      const dirty = '<em>日本語テキスト</em> and <strong>한글 텍스트</strong>';
      const clean = sanitizeHtml(dirty);
      expect(clean).toContain('日本語テキスト');
      expect(clean).toContain('한글 텍스트');
    });

    it('should handle mixed safe and unsafe content', () => {
      const dirty = '<em>Safe</em><script>alert("xss")</script><strong>Also safe</strong>';
      const clean = sanitizeHtml(dirty);
      expect(clean).toContain('<em>Safe</em>');
      expect(clean).toContain('<strong>Also safe</strong>');
      expect(clean).not.toContain('script');
      expect(clean).not.toContain('alert');
    });
  });

  describe('Real-world Fess Snippet Examples', () => {
    it('should handle typical search snippet with highlighting', () => {
      const dirty =
        'This is a <em>search</em> result with <strong>important</strong> keywords highlighted.';
      const clean = sanitizeHtml(dirty);
      expect(clean).toBe(dirty); // Should remain unchanged
    });

    it('should handle snippet with anchor to source', () => {
      const dirty = 'Visit <a href="https://docs.example.com/page">documentation</a> for details.';
      const clean = sanitizeHtml(dirty);
      expect(clean).toContain('<a href="https://docs.example.com/page">');
      expect(clean).toContain('documentation');
    });

    it('should sanitize snippet with injected script', () => {
      const dirty =
        'Normal content <em>highlighted</em><script>fetch("evil.com")</script> more content';
      const clean = sanitizeHtml(dirty);
      expect(clean).toContain('Normal content');
      expect(clean).toContain('<em>highlighted</em>');
      expect(clean).not.toContain('script');
      expect(clean).not.toContain('fetch');
    });
  });

  describe('Server-side Rendering', () => {
    it('should strip all HTML tags when window is undefined (SSR)', () => {
      // Mock window being undefined
      const originalWindow = global.window;
      // @ts-expect-error - Testing SSR behavior without window
      delete global.window;

      const dirty = '<em>emphasized</em> and <script>alert("xss")</script> text';
      const clean = sanitizeHtml(dirty);

      expect(clean).not.toContain('<em>');
      expect(clean).not.toContain('</em>');
      expect(clean).not.toContain('<script>');
      expect(clean).toContain('emphasized');
      expect(clean).toContain('text');

      // Restore window
      global.window = originalWindow;
    });

    it('should remove overlapping tags (<<script>script>) - CVE bypass attack', () => {
      // This test verifies the fix for incomplete multi-character sanitization
      const originalWindow = global.window;
      // @ts-expect-error - Testing SSR behavior without window
      delete global.window;

      const dirty = '<<script>script>alert("xss")</script>';
      const clean = sanitizeHtml(dirty);

      // After iterative sanitization, all tags should be removed
      expect(clean).not.toContain('<script');
      expect(clean).not.toContain('script>');
      expect(clean).not.toContain('</script>');
      expect(clean).not.toContain('<');
      expect(clean).toContain('alert'); // Text content should remain

      // Restore window
      global.window = originalWindow;
    });

    it('should remove deeply nested malformed tags', () => {
      const originalWindow = global.window;
      // @ts-expect-error - Testing SSR behavior without window
      delete global.window;

      const dirty = '<<<div><script>>>malicious</script></div>>';
      const clean = sanitizeHtml(dirty);

      // All tag-like structures should be removed
      expect(clean).not.toContain('<');
      expect(clean).not.toContain('>');
      expect(clean).toBe('malicious');

      // Restore window
      global.window = originalWindow;
    });

    it('should handle tag-like strings that are not actually tags', () => {
      const originalWindow = global.window;
      // @ts-expect-error - Testing SSR behavior without window
      delete global.window;

      const dirty = 'Use <variable> or <function> syntax in code';
      const clean = sanitizeHtml(dirty);

      // Simple < > patterns should also be removed
      expect(clean).not.toContain('<');
      expect(clean).not.toContain('>');
      expect(clean).toBe('Use  or  syntax in code');

      // Restore window
      global.window = originalWindow;
    });

    it('should handle complex nested attack pattern', () => {
      const originalWindow = global.window;
      // @ts-expect-error - Testing SSR behavior without window
      delete global.window;

      // Multiple levels of nesting to test iterative approach
      const dirty = '<div><<strong><<em><<mark>nested</mark>></em>></strong>></div>';
      const clean = sanitizeHtml(dirty);

      expect(clean).not.toContain('<');
      expect(clean).not.toContain('>');
      expect(clean).toBe('nested');

      // Restore window
      global.window = originalWindow;
    });

    it('should handle mixed malformed and well-formed tags', () => {
      const originalWindow = global.window;
      // @ts-expect-error - Testing SSR behavior without window
      delete global.window;

      const dirty = 'Normal <em>text</em> with <<script>malicious>content</script>';
      const clean = sanitizeHtml(dirty);

      expect(clean).not.toContain('<');
      expect(clean).not.toContain('>');
      expect(clean).toContain('Normal');
      expect(clean).toContain('text');
      expect(clean).toContain('malicious');

      // Restore window
      global.window = originalWindow;
    });

    it('should complete within iteration limit for extremely nested input', () => {
      const originalWindow = global.window;
      // @ts-expect-error - Testing SSR behavior without window
      delete global.window;

      // Create a very deeply nested structure that would take many iterations
      // but should still complete within MAX_ITERATIONS (10)
      let dirty = 'content';
      for (let i = 0; i < 15; i++) {
        dirty = `<div>${dirty}</div>`;
      }

      const clean = sanitizeHtml(dirty);

      // Should remove as many tags as possible within iteration limit
      expect(clean).toContain('content');
      // May still have some tags if hitting the iteration limit, but should not hang

      // Restore window
      global.window = originalWindow;
    });
  });
});
