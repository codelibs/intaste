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

interface EmptyStateProps {
  title?: string;
  message?: string;
  suggestions?: string[];
  type?: 'welcome' | 'noResults';
  className?: string;
}

export function EmptyState({
  title,
  message,
  suggestions,
  type = 'noResults',
  className,
}: EmptyStateProps) {
  const { t } = useTranslation();

  const defaultTitle = type === 'welcome' ? t('empty.welcome.title') : t('empty.noResults.title');
  const defaultMessage =
    type === 'welcome' ? t('empty.welcome.message') : t('empty.noResults.message');
  const defaultSuggestions =
    type === 'welcome'
      ? (t('empty.welcome.suggestions', { returnObjects: true }) as string[])
      : (t('empty.noResults.suggestions', { returnObjects: true }) as string[]);

  return (
    <div className={cn('text-center py-12', className)}>
      <div className="text-6xl mb-4">🔍</div>
      <h3 className="text-lg font-medium text-foreground mb-2">{title || defaultTitle}</h3>
      <p className="text-sm text-muted-foreground mb-6 max-w-md mx-auto">
        {message || defaultMessage}
      </p>
      {(suggestions || defaultSuggestions).length > 0 && (
        <div className="max-w-md mx-auto">
          <ul className="space-y-2 text-sm text-muted-foreground">
            {(suggestions || defaultSuggestions).map((suggestion, idx) => (
              <li key={idx}>• {suggestion}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
