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
import { useLanguageStore } from '@/store/language.store';
import { DEFAULT_LANGUAGE } from '@/libs/i18n/languages';

// Mock i18n config
vi.mock('@/libs/i18n/config', () => ({
  default: {
    changeLanguage: vi.fn().mockResolvedValue(undefined),
  },
}));

describe('LanguageStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    useLanguageStore.setState({
      currentLanguage: DEFAULT_LANGUAGE,
    });

    // Clear localStorage
    localStorage.clear();

    // Reset document.documentElement.lang
    if (typeof document !== 'undefined') {
      document.documentElement.lang = '';
    }
  });

  it('initializes with default language', () => {
    const state = useLanguageStore.getState();
    expect(state.currentLanguage).toBe(DEFAULT_LANGUAGE);
  });

  it('changes language', async () => {
    const { changeLanguage } = useLanguageStore.getState();

    await changeLanguage('ja');

    const state = useLanguageStore.getState();
    expect(state.currentLanguage).toBe('ja');
  });

  it('updates HTML lang attribute when changing language', async () => {
    const { changeLanguage } = useLanguageStore.getState();

    await changeLanguage('fr');

    expect(document.documentElement.lang).toBe('fr');
  });

  it('persists language to localStorage', async () => {
    const { changeLanguage } = useLanguageStore.getState();

    await changeLanguage('es');

    // Check that localStorage.setItem was called
    expect(localStorage.setItem).toHaveBeenCalled();

    const state = useLanguageStore.getState();
    expect(state.currentLanguage).toBe('es');
  });

  it('calls localStorage.setItem when language changes', () => {
    const { changeLanguage } = useLanguageStore.getState();

    changeLanguage('de');

    // Verify that localStorage.setItem was called
    expect(localStorage.setItem).toHaveBeenCalled();
  });

  it('supports multiple language changes', async () => {
    const { changeLanguage } = useLanguageStore.getState();

    await changeLanguage('ja');
    expect(useLanguageStore.getState().currentLanguage).toBe('ja');

    await changeLanguage('zh');
    expect(useLanguageStore.getState().currentLanguage).toBe('zh');

    await changeLanguage('ko');
    expect(useLanguageStore.getState().currentLanguage).toBe('ko');
  });

  it('handles changing to the same language', async () => {
    const { changeLanguage } = useLanguageStore.getState();

    await changeLanguage('en');
    expect(useLanguageStore.getState().currentLanguage).toBe('en');

    await changeLanguage('en');
    expect(useLanguageStore.getState().currentLanguage).toBe('en');
  });

  it('calls i18n changeLanguage when language changes', async () => {
    const i18n = await import('@/libs/i18n/config');
    const changeLanguageSpy = vi.spyOn(i18n.default, 'changeLanguage');

    const { changeLanguage } = useLanguageStore.getState();
    await changeLanguage('ja');

    expect(changeLanguageSpy).toHaveBeenCalledWith('ja');
  });

  it('returns a promise from changeLanguage', async () => {
    const { changeLanguage } = useLanguageStore.getState();

    const result = changeLanguage('fr');
    expect(result).toBeInstanceOf(Promise);

    await result;
  });

  describe('Persistence', () => {
    it('calls localStorage.setItem with language-storage key', async () => {
      const { changeLanguage } = useLanguageStore.getState();

      await changeLanguage('ja');

      // Verify that localStorage.setItem was called with the correct key
      expect(localStorage.setItem).toHaveBeenCalledWith('language-storage', expect.any(String));
    });

    it('updates state correctly after language change', async () => {
      const { changeLanguage } = useLanguageStore.getState();

      await changeLanguage('es');

      const state = useLanguageStore.getState();
      expect(state.currentLanguage).toBe('es');
      expect(state.changeLanguage).toBeInstanceOf(Function);
    });
  });

  describe('Edge Cases', () => {
    it('handles empty string language code', async () => {
      const { changeLanguage } = useLanguageStore.getState();

      await changeLanguage('');

      const state = useLanguageStore.getState();
      expect(state.currentLanguage).toBe('');
    });

    it('handles invalid language code', async () => {
      const { changeLanguage } = useLanguageStore.getState();

      // Should not throw error
      await changeLanguage('invalid-lang-code');

      const state = useLanguageStore.getState();
      expect(state.currentLanguage).toBe('invalid-lang-code');
    });

    it('handles special characters in language code', async () => {
      const { changeLanguage } = useLanguageStore.getState();

      await changeLanguage('zh-CN');

      const state = useLanguageStore.getState();
      expect(state.currentLanguage).toBe('zh-CN');
    });
  });
});
