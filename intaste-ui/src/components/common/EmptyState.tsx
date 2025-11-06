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

import { Text, makeStyles, mergeClasses, tokens } from '@fluentui/react-components';
import { Search48Regular } from '@fluentui/react-icons';
import { useTranslation } from '@/libs/i18n/client';

const useStyles = makeStyles({
  container: {
    textAlign: 'center',
    paddingTop: tokens.spacingVerticalXXXL,
    paddingBottom: tokens.spacingVerticalXXXL,
  },
  welcomeContainer: {
    textAlign: 'center',
    paddingTop: tokens.spacingVerticalXXXL,
    paddingBottom: tokens.spacingVerticalM,
  },
  welcomeMessage: {
    color: tokens.colorNeutralForeground2,
  },
  icon: {
    marginBottom: tokens.spacingVerticalXL,
    fontSize: '64px',
    color: tokens.colorNeutralForeground3,
  },
  title: {
    marginBottom: tokens.spacingVerticalM,
  },
  message: {
    marginBottom: tokens.spacingVerticalXXXL,
    maxWidth: '600px',
    marginLeft: 'auto',
    marginRight: 'auto',
    color: tokens.colorNeutralForeground2,
  },
  suggestionsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
    gap: tokens.spacingHorizontalL,
    maxWidth: '900px',
    marginLeft: 'auto',
    marginRight: 'auto',
    paddingLeft: tokens.spacingHorizontalL,
    paddingRight: tokens.spacingHorizontalL,
  },
  suggestionCard: {
    backgroundColor: tokens.colorNeutralBackground2,
    borderRadius: tokens.borderRadiusMedium,
    borderTopWidth: '1px',
    borderBottomWidth: '1px',
    borderLeftWidth: '1px',
    borderRightWidth: '1px',
    borderTopStyle: 'solid',
    borderBottomStyle: 'solid',
    borderLeftStyle: 'solid',
    borderRightStyle: 'solid',
    borderTopColor: tokens.colorNeutralStroke2,
    borderBottomColor: tokens.colorNeutralStroke2,
    borderLeftColor: tokens.colorNeutralStroke2,
    borderRightColor: tokens.colorNeutralStroke2,
    paddingTop: tokens.spacingVerticalL,
    paddingBottom: tokens.spacingVerticalL,
    paddingLeft: tokens.spacingHorizontalL,
    paddingRight: tokens.spacingHorizontalL,
    boxShadow: tokens.shadow4,
    textAlign: 'left',
    transitionProperty: 'box-shadow, border-color',
    transitionDuration: tokens.durationNormal,
    transitionTimingFunction: tokens.curveEasyEase,
    ':hover': {
      boxShadow: tokens.shadow8,
      borderTopColor: tokens.colorNeutralStroke1,
      borderBottomColor: tokens.colorNeutralStroke1,
      borderLeftColor: tokens.colorNeutralStroke1,
      borderRightColor: tokens.colorNeutralStroke1,
    },
  },
  suggestionText: {
    color: tokens.colorNeutralForeground2,
    lineHeight: '1.5',
  },
});

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
  const styles = useStyles();

  const defaultTitle = type === 'welcome' ? t('empty.welcome.title') : t('empty.noResults.title');
  const defaultMessage =
    type === 'welcome' ? t('empty.welcome.message') : t('empty.noResults.message');
  const defaultSuggestions =
    type === 'welcome'
      ? (t('empty.welcome.suggestions', { returnObjects: true }) as string[])
      : (t('empty.noResults.suggestions', { returnObjects: true }) as string[]);

  // Welcome state: show only a simple message
  if (type === 'welcome') {
    return (
      <div className={mergeClasses(styles.welcomeContainer, className)}>
        <Text size={500} block className={styles.welcomeMessage}>
          {title || defaultTitle}
        </Text>
      </div>
    );
  }

  // NoResults state: show full layout with suggestions
  return (
    <div className={mergeClasses(styles.container, className)}>
      <div className={styles.icon}>
        <Search48Regular />
      </div>
      <Text size={600} weight="semibold" block className={styles.title}>
        {title || defaultTitle}
      </Text>
      <Text size={400} block className={styles.message}>
        {message || defaultMessage}
      </Text>
      {(suggestions || defaultSuggestions).length > 0 && (
        <div className={styles.suggestionsGrid}>
          {(suggestions || defaultSuggestions).map((suggestion, idx) => (
            <div key={idx} className={styles.suggestionCard}>
              <Text size={300} className={styles.suggestionText}>
                {suggestion}
              </Text>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
