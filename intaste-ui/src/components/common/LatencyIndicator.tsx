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

import type { Timings } from '@/types/api';
import { getLatencyLevel } from '@/libs/utils';
import { cn } from '@/libs/utils';

interface LatencyIndicatorProps {
  timings: Timings;
  className?: string;
}

export function LatencyIndicator({ timings, className }: LatencyIndicatorProps) {
  const level = getLatencyLevel(timings.total_ms);

  const levelConfig = {
    good: {
      icon: '⚡',
      text: 'Fast',
      color: 'text-green-600 dark:text-green-400',
    },
    ok: {
      icon: '⏱️',
      text: 'Normal',
      color: 'text-yellow-600 dark:text-yellow-400',
    },
    slow: {
      icon: '🐌',
      text: 'Slow',
      color: 'text-red-600 dark:text-red-400',
    },
  };

  const config = levelConfig[level];

  return (
    <div className={cn('flex items-center gap-2 text-xs', className)}>
      <span className={cn('font-medium', config.color)}>
        {config.icon} {config.text}
      </span>
      <span className="text-muted-foreground">{timings.total_ms}ms</span>
      <span className="text-muted-foreground text-[10px]">
        (LLM: {timings.llm_ms}ms, Search: {timings.search_ms}ms)
      </span>
    </div>
  );
}
