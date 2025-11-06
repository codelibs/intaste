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

import {
  MessageBar,
  MessageBarBody,
  MessageBarTitle,
  MessageBarActions,
  Button,
  makeStyles,
} from '@fluentui/react-components';
import { DismissRegular } from '@fluentui/react-icons';
import { useTranslation } from '@/libs/i18n/client';

const useStyles = makeStyles({
  retryButton: {
    minWidth: 'auto',
  },
});

interface ErrorBannerProps {
  message: string;
  onRetry?: () => void;
  onDismiss?: () => void;
  className?: string;
}

export function ErrorBanner({ message, onRetry, onDismiss, className }: ErrorBannerProps) {
  const { t } = useTranslation();
  const styles = useStyles();

  return (
    <MessageBar intent="error" className={className}>
      <MessageBarBody>
        <MessageBarTitle>{t('error.title')}</MessageBarTitle>
        {message}
      </MessageBarBody>
      <MessageBarActions
        containerAction={
          onDismiss ? (
            <Button
              appearance="transparent"
              icon={<DismissRegular />}
              onClick={onDismiss}
              aria-label="Dismiss error"
              size="small"
            />
          ) : undefined
        }
      >
        {onRetry && (
          <Button
            appearance="transparent"
            onClick={onRetry}
            className={styles.retryButton}
            size="small"
          >
            {t('error.retry')}
          </Button>
        )}
      </MessageBarActions>
    </MessageBar>
  );
}
