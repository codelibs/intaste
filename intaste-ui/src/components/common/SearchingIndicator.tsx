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
 * SearchingIndicator component
 * Displays searching status with elapsed time in glassmorphism design
 */

'use client';

import { useEffect, useState } from 'react';
import { useTranslation } from '@/libs/i18n/client';
import { useAssistStore } from '@/store/assist.store';
import { cn } from '@/libs/utils';

export function SearchingIndicator() {
  const { t } = useTranslation();
  const { streaming, searchStartTime } = useAssistStore();
  const [elapsedTime, setElapsedTime] = useState(0);

  useEffect(() => {
    if (!streaming || !searchStartTime) {
      setElapsedTime(0);
      return;
    }

    // Update elapsed time every second
    const interval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - searchStartTime) / 1000);
      setElapsedTime(elapsed);
    }, 1000);

    // Initial update
    const elapsed = Math.floor((Date.now() - searchStartTime) / 1000);
    setElapsedTime(elapsed);

    return () => clearInterval(interval);
  }, [streaming, searchStartTime]);

  if (!streaming) {
    return null;
  }

  // Format time as MM:SS
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div
      className={cn(
        'glass-panel',
        'px-4 py-2',
        'flex items-center gap-3',
        'transition-all duration-300',
        'animate-pulse'
      )}
    >
      {/* Searching icon with spin animation */}
      <div className="relative flex items-center justify-center w-5 h-5">
        <div className="absolute inset-0 rounded-full border-2 border-primary/30" />
        <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-primary animate-spin" />
      </div>

      {/* Status text */}
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium text-foreground">{t('header.streaming')}</span>
        <span
          className="text-xs font-mono text-muted-foreground tabular-nums"
          aria-live="polite"
          aria-atomic="true"
          aria-label={t('header.elapsedTime', { time: formatTime(elapsedTime) })}
        >
          {formatTime(elapsedTime)}
        </span>
      </div>
    </div>
  );
}
