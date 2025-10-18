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

interface ErrorBannerProps {
  message: string;
  onRetry?: () => void;
  onDismiss?: () => void;
  className?: string;
}

export function ErrorBanner({ message, onRetry, onDismiss, className }: ErrorBannerProps) {
  const { t } = useTranslation();

  return (
    <div
      className={cn('rounded-lg border border-destructive/50 bg-destructive/10 p-4', className)}
      role="alert"
    >
      <div className="flex items-start gap-3">
        <span className="text-xl">❌</span>
        <div className="flex-1">
          <p className="text-sm font-medium text-destructive mb-1">{t('error.title')}</p>
          <p className="text-sm text-destructive/90">{message}</p>
        </div>
        <div className="flex gap-2">
          {onRetry && (
            <button
              onClick={onRetry}
              className="text-xs font-medium text-destructive hover:underline"
            >
              {t('error.retry')}
            </button>
          )}
          {onDismiss && (
            <button
              onClick={onDismiss}
              className="text-xs font-medium text-muted-foreground hover:text-foreground"
              aria-label="Dismiss error"
            >
              {t('error.dismiss')}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
