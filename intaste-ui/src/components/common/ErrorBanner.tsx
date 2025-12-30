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

import { useTranslation } from '@/libs/i18n/client';
import { Banner } from './Banner';

interface ErrorBannerProps {
  message: string;
  onRetry?: () => void;
  onDismiss?: () => void;
  className?: string;
}

/**
 * ErrorBanner component - now using the unified Banner component
 * Displays error messages with optional retry and dismiss actions
 */
export function ErrorBanner({ message, onRetry, onDismiss, className }: ErrorBannerProps) {
  const { t } = useTranslation();

  return (
    <Banner
      intent="error"
      title={t('error.title')}
      message={message}
      onAction={onRetry}
      actionLabel={onRetry ? t('error.retry') : undefined}
      onDismiss={onDismiss}
      className={className}
    />
  );
}
