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
  type MessageBarIntent,
} from '@fluentui/react-components';
import {
  DismissRegular,
  CheckmarkCircleRegular,
  InfoRegular,
  WarningRegular,
  ErrorCircleRegular,
} from '@fluentui/react-icons';

const useStyles = makeStyles({
  actionButton: {
    minWidth: 'auto',
  },
});

export type BannerIntent = 'info' | 'warning' | 'success' | 'error';

interface BannerProps {
  intent: BannerIntent;
  title?: string;
  message: string;
  onAction?: () => void;
  actionLabel?: string;
  onDismiss?: () => void;
  className?: string;
}

const iconMap: Record<BannerIntent, React.ReactElement> = {
  success: <CheckmarkCircleRegular />,
  info: <InfoRegular />,
  warning: <WarningRegular />,
  error: <ErrorCircleRegular />,
};

/**
 * Banner component inspired by Atlassian Design System
 * Displays important messages with various intent levels
 */
export function Banner({
  intent,
  title,
  message,
  onAction,
  actionLabel,
  onDismiss,
  className,
}: BannerProps) {
  const styles = useStyles();

  // Map our intent to Fluent UI's MessageBarIntent
  const fluentIntent: MessageBarIntent = intent;

  return (
    <MessageBar intent={fluentIntent} icon={iconMap[intent]} className={className}>
      <MessageBarBody>
        {title && <MessageBarTitle>{title}</MessageBarTitle>}
        {message}
      </MessageBarBody>
      <MessageBarActions
        containerAction={
          onDismiss ? (
            <Button
              appearance="transparent"
              icon={<DismissRegular />}
              onClick={onDismiss}
              aria-label="Dismiss"
              size="small"
            />
          ) : undefined
        }
      >
        {onAction && actionLabel && (
          <Button
            appearance="transparent"
            onClick={onAction}
            className={styles.actionButton}
            size="small"
          >
            {actionLabel}
          </Button>
        )}
      </MessageBarActions>
    </MessageBar>
  );
}
