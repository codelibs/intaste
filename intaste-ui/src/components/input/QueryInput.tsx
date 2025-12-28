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

'use client';

import { useRef, KeyboardEvent } from 'react';
import { Textarea, Text, makeStyles } from '@fluentui/react-components';
import { useTranslation } from '@/libs/i18n/client';

const useStyles = makeStyles({
  root: {
    width: '100%',
    transitionProperty: 'all',
    transitionDuration: '200ms',
    transitionTimingFunction: 'cubic-bezier(0.4, 0, 0.2, 1)',
  },
  footer: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: '8px',
  },
  helperText: {
    opacity: '0.7',
    transitionProperty: 'opacity',
    transitionDuration: '200ms',
  },
  charCount: {
    fontVariantNumeric: 'tabular-nums',
  },
});

interface QueryInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
}

export function QueryInput({
  value,
  onChange,
  onSubmit,
  disabled = false,
  placeholder,
  className,
}: QueryInputProps) {
  const { t } = useTranslation();
  const styles = useStyles();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Skip if IME composition is in progress (e.g., Japanese input)
    // keyCode === 229: fallback for older browsers during IME input
    // nativeEvent.isComposing: standard way to detect IME composition
    if (e.nativeEvent.isComposing || e.keyCode === 229) {
      return;
    }

    // Submit on Enter (without Shift)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (value.trim() && !disabled) {
        onSubmit();
      }
    }
  };

  return (
    <div className={className}>
      <Textarea
        ref={textareaRef}
        value={value}
        onChange={(_e, data) => onChange(data.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder={placeholder || t('input.placeholder')}
        rows={3}
        resize="none"
        appearance="outline"
        size="large"
        aria-label="Search query input"
        className={styles.root}
      />
      <div className={styles.footer}>
        <Text size={200} className={styles.helperText}>
          {t('input.helper')}
        </Text>
        <Text size={200} className={styles.charCount}>
          {t('input.characterCount', { count: value.length })}
        </Text>
      </div>
    </div>
  );
}
