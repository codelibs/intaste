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

import { cn } from '@/libs/utils';
import { useTranslation } from '@/libs/i18n/client';

interface QueryHistoryProps {
  history: string[];
  onQueryClick?: (query: string) => void;
  onClear?: () => void;
  className?: string;
}

export function QueryHistory({ history, onQueryClick, onClear, className }: QueryHistoryProps) {
  const { t } = useTranslation();

  if (history.length === 0) {
    return null;
  }

  return (
    <div className={cn('w-full', className)}>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-muted-foreground">{t('history.title')}</h3>
        {onClear && (
          <button
            onClick={onClear}
            className="text-xs text-muted-foreground hover:text-foreground transition-colors px-2 py-1 rounded hover:bg-muted"
            aria-label="Clear history"
          >
            {t('history.clear')}
          </button>
        )}
      </div>
      <div className="space-y-2 max-h-48 overflow-y-auto">
        {history.map((query, index) => (
          <div
            key={`${query}-${index}`}
            onClick={() => onQueryClick?.(query)}
            className={cn(
              'group px-3 py-2 rounded-lg bg-muted/50 border border-border',
              'text-sm text-foreground',
              'transition-colors',
              onQueryClick && 'cursor-pointer hover:bg-muted hover:border-primary/50'
            )}
          >
            <div className="flex items-start gap-2">
              <span className="text-xs text-muted-foreground mt-0.5 flex-shrink-0">
                {index + 1}.
              </span>
              <p className="flex-1 line-clamp-2 break-words">{query}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
