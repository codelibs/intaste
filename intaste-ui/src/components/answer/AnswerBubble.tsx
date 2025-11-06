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

import React from 'react';
import type { Answer } from '@/types/api';
import { Card, Text, Button, makeStyles, mergeClasses, tokens } from '@fluentui/react-components';
import { LightbulbRegular } from '@fluentui/react-icons';
import { ProcessingStatus } from '@/components/common/ProcessingStatus';
import { useTranslation } from '@/libs/i18n/client';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const useStyles = makeStyles({
  card: {
    padding: tokens.spacingVerticalXXL,
  },
  fallbackNotice: {
    marginBottom: tokens.spacingVerticalL,
    padding: tokens.spacingVerticalM,
    backgroundColor: tokens.colorPaletteYellowBackground2,
    borderRadius: tokens.borderRadiusMedium,
  },
  markdownContainer: {
    lineHeight: '1.6',
  },
  streamingCursor: {
    display: 'inline-block',
    width: '2px',
    height: '1rem',
    marginLeft: tokens.spacingHorizontalXS,
    backgroundColor: tokens.colorBrandBackground,
    animationName: {
      '0%, 100%': { opacity: 1 },
      '50%': { opacity: 0 },
    },
    animationDuration: '1s',
    animationIterationCount: 'infinite',
  },
  suggestedQuestionsSection: {
    marginTop: tokens.spacingVerticalXXL,
    paddingTop: tokens.spacingVerticalL,
    borderTopWidth: '1px',
    borderTopStyle: 'solid',
    borderTopColor: tokens.colorNeutralStroke2,
  },
  suggestedQuestionsHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: tokens.spacingHorizontalS,
    marginBottom: tokens.spacingVerticalM,
  },
  questionsList: {
    display: 'flex',
    flexDirection: 'column',
    gap: tokens.spacingVerticalS,
  },
  citationButton: {
    padding: '0',
    minWidth: 'auto',
    height: 'auto',
  },
  // Markdown styling
  markdownParagraph: {
    marginBottom: tokens.spacingVerticalL,
    '&:last-child': {
      marginBottom: '0',
    },
  },
  markdownHeading3: {
    fontSize: tokens.fontSizeBase400,
    fontWeight: tokens.fontWeightSemibold,
    marginTop: tokens.spacingVerticalL,
    marginBottom: tokens.spacingVerticalS,
  },
  markdownHeading4: {
    fontSize: tokens.fontSizeBase300,
    fontWeight: tokens.fontWeightSemibold,
    marginTop: tokens.spacingVerticalM,
    marginBottom: tokens.spacingVerticalS,
  },
  markdownList: {
    marginBottom: tokens.spacingVerticalL,
    marginLeft: tokens.spacingHorizontalXL,
  },
  markdownListItem: {
    marginLeft: tokens.spacingHorizontalL,
  },
  markdownCode: {
    backgroundColor: tokens.colorNeutralBackground2,
    paddingLeft: tokens.spacingHorizontalXXS,
    paddingRight: tokens.spacingHorizontalXXS,
    paddingTop: '2px',
    paddingBottom: '2px',
    borderRadius: tokens.borderRadiusSmall,
    fontSize: tokens.fontSizeBase200,
  },
});

interface AnswerBubbleProps {
  answer: Answer;
  streaming?: boolean;
  processingPhase?: 'intent' | 'search' | 'relevance' | 'compose' | null;
  intentData?: {
    normalized_query: string;
    filters?: Record<string, string | number | boolean | null>;
    followups: string[];
  } | null;
  citationsData?: {
    total: number;
    topResults: string[];
  } | null;
  relevanceData?: {
    evaluated_count: number;
    max_score: number;
  } | null;
  fallbackNotice?: string | null;
  onCitationClick?: (id: number) => void;
  className?: string;
}

export function AnswerBubble({
  answer,
  streaming = false,
  processingPhase,
  intentData,
  citationsData,
  relevanceData,
  fallbackNotice,
  onCitationClick,
  className,
}: AnswerBubbleProps) {
  const { t } = useTranslation();
  const styles = useStyles();

  // Render Markdown with clickable citation markers
  const renderMarkdownWithCitations = (text: string) => {
    return (
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Custom renderer for text to make citation markers clickable
          p: ({ children }) => {
            const processChildren = (child: React.ReactNode): React.ReactNode => {
              if (typeof child === 'string') {
                const parts = child.split(/(\[\d+\])/g);
                return parts.map((part, idx) => {
                  const match = part.match(/\[(\d+)\]/);
                  if (match) {
                    const citationId = parseInt(match[1], 10);
                    return (
                      <Button
                        key={`cite-${idx}`}
                        appearance="transparent"
                        onClick={() => onCitationClick?.(citationId)}
                        className={styles.citationButton}
                        aria-label={t('answer.viewCitation', { id: citationId })}
                      >
                        <Text style={{ color: tokens.colorBrandForeground1 }}>{part}</Text>
                      </Button>
                    );
                  }
                  return <span key={`text-${idx}`}>{part}</span>;
                });
              }
              return child;
            };

            return (
              <p className={styles.markdownParagraph}>
                {Array.isArray(children)
                  ? children.map((child, idx) => (
                      <React.Fragment key={idx}>{processChildren(child)}</React.Fragment>
                    ))
                  : processChildren(children)}
              </p>
            );
          },
          // Style headings
          h3: ({ children }) => <h3 className={styles.markdownHeading3}>{children}</h3>,
          h4: ({ children }) => <h4 className={styles.markdownHeading4}>{children}</h4>,
          // Style lists
          ul: ({ children }) => (
            <ul className={styles.markdownList} style={{ listStyleType: 'disc' }}>
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className={styles.markdownList} style={{ listStyleType: 'decimal' }}>
              {children}
            </ol>
          ),
          li: ({ children }) => <li className={styles.markdownListItem}>{children}</li>,
          // Style inline code and emphasis
          strong: ({ children }) => (
            <strong style={{ fontWeight: tokens.fontWeightSemibold }}>{children}</strong>
          ),
          em: ({ children }) => <em style={{ fontStyle: 'italic' }}>{children}</em>,
          code: ({ children }) => <code className={styles.markdownCode}>{children}</code>,
        }}
      >
        {text}
      </ReactMarkdown>
    );
  };

  return (
    <Card appearance="filled" className={mergeClasses(styles.card, className)}>
      {fallbackNotice && (
        <Card appearance="filled" className={styles.fallbackNotice}>
          <Text size={300} weight="semibold">
            {t('answer.fallbackNotice')}
          </Text>
          <Text size={200}>{fallbackNotice}</Text>
        </Card>
      )}

      <div className={styles.markdownContainer}>
        {processingPhase ? (
          // Display detailed processing status
          <ProcessingStatus
            phase={processingPhase}
            intentData={intentData ?? undefined}
            citationsData={citationsData ?? undefined}
            relevanceData={relevanceData ?? undefined}
          />
        ) : (
          // Display answer text with Markdown rendering
          <div>
            {renderMarkdownWithCitations(answer.text)}
            {streaming && (
              <span className={styles.streamingCursor} aria-label="Streaming">
                |
              </span>
            )}
          </div>
        )}
      </div>

      {answer.suggested_questions && answer.suggested_questions.length > 0 && (
        <div className={styles.suggestedQuestionsSection}>
          <div className={styles.suggestedQuestionsHeader}>
            <LightbulbRegular />
            <Text size={300} weight="semibold">
              {t('answer.relatedQuestions')}
            </Text>
          </div>
          <div className={styles.questionsList}>
            {answer.suggested_questions.map((question, idx) => (
              <Button
                key={idx}
                appearance="subtle"
                style={{ height: 'auto', padding: tokens.spacingVerticalM }}
              >
                <Text size={300}>{question}</Text>
              </Button>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}
