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
import { cn } from '@/libs/utils';

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
  placeholder = 'Enter your question here...',
  className,
}: QueryInputProps) {
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
    <div className={cn('relative w-full', className)}>
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder={placeholder}
        rows={3}
        maxLength={4096}
        className={cn(
          'w-full rounded-lg border border-input bg-background px-4 py-3',
          'text-sm resize-none',
          'placeholder:text-muted-foreground',
          'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
          'disabled:cursor-not-allowed disabled:opacity-50',
          'transition-colors'
        )}
        aria-label="Search query input"
      />
      <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
        <span>Enter to send • Shift+Enter for new line</span>
        <span>{value.length} / 4096</span>
      </div>
    </div>
  );
}
