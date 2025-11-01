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
import { cn } from '@/libs/utils';

interface ProcessingStatusProps {
  phase: 'intent' | 'search' | 'relevance' | 'compose';
  intentData?: {
    normalized_query: string;
    filters?: Record<string, string | number | boolean | null>;
    followups: string[];
  };
  citationsData?: {
    total: number;
    topResults: string[];
  };
  relevanceData?: {
    evaluated_count: number;
    max_score: number;
  };
}

export function ProcessingStatus({
  phase,
  intentData,
  citationsData,
  relevanceData,
}: ProcessingStatusProps) {
  const { t } = useTranslation();

  // Phase icon components with enhanced animations
  const PhaseIcon = ({
    phase: iconPhase,
  }: {
    phase: 'intent' | 'search' | 'relevance' | 'compose';
  }) => {
    const isActive = phase === iconPhase;

    const icons = {
      intent: {
        emoji: '🔍',
        animation: 'animate-spin',
        color: 'text-blue-500 dark:text-blue-400',
      },
      search: {
        emoji: '🔎',
        animation: 'animate-pulse',
        color: 'text-purple-500 dark:text-purple-400',
      },
      relevance: {
        emoji: '⚖️',
        animation: 'animate-bounce',
        color: 'text-cyan-500 dark:text-cyan-400',
      },
      compose: {
        emoji: '💬',
        animation: 'animate-pulse',
        color: 'text-green-500 dark:text-green-400',
      },
    };

    const icon = icons[iconPhase];

    return (
      <div
        className={cn(
          'flex items-center justify-center w-10 h-10 rounded-full',
          isActive && 'glass'
        )}
      >
        <span className={cn('text-2xl transition-all duration-300', isActive && icon.animation)}>
          {icon.emoji}
        </span>
      </div>
    );
  };

  return (
    <div className={cn('glass-card p-6 space-y-4 transition-all duration-300')}>
      {/* Intent data */}
      {intentData && (
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <PhaseIcon phase="intent" />
            <div>
              <div className="font-semibold text-foreground">{t('processing.searchKeywords')}</div>
              <div className="text-xs text-muted-foreground">
                {t('processing.queryOptimizationComplete')}
              </div>
            </div>
          </div>
          <div className="ml-13 space-y-2">
            <div className="glass-panel p-3 font-mono text-sm text-foreground">
              &quot;{intentData.normalized_query}&quot;
            </div>

            {intentData.filters && Object.keys(intentData.filters).length > 0 && (
              <div className="flex items-start gap-2 text-xs text-muted-foreground">
                <span>📌</span>
                <div>
                  <span className="font-medium">{t('processing.filters')}:</span>
                  <div className="mt-1 font-mono">
                    {JSON.stringify(intentData.filters, null, 2)}
                  </div>
                </div>
              </div>
            )}

            {intentData.followups.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <span>💡</span>
                  <span className="font-medium">{t('processing.relatedQuestions')}:</span>
                </div>
                <ul className="pl-6 space-y-1">
                  {intentData.followups.map((q, i) => (
                    <li key={i} className="text-xs text-muted-foreground">
                      • {q}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Search in progress indicator */}
      {phase === 'search' && (
        <div className="flex items-center gap-3 animate-pulse">
          <PhaseIcon phase="search" />
          <div>
            <div className="font-semibold text-foreground">{t('processing.searching')}</div>
            <div className="text-xs text-muted-foreground">
              {t('processing.findingRelevantInfo')}
            </div>
          </div>
        </div>
      )}

      {/* Citations data */}
      {citationsData && citationsData.total > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-full glass">
              <span className="text-2xl">✅</span>
            </div>
            <div>
              <div className="font-semibold text-green-600 dark:text-green-400">
                {t('processing.resultsFound', { count: citationsData.total })}
              </div>
              <div className="text-xs text-muted-foreground">
                {t('processing.searchCompletedSuccessfully')}
              </div>
            </div>
          </div>

          {citationsData.topResults.length > 0 && (
            <div className="ml-13 space-y-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <span>📄</span>
                <span className="font-medium">{t('processing.topResults')}:</span>
              </div>
              <ol className="pl-6 space-y-1.5">
                {citationsData.topResults.map((title, i) => (
                  <li key={i} className="text-sm text-foreground">
                    <span className="font-semibold text-primary">{i + 1}.</span> {title}
                  </li>
                ))}
              </ol>
            </div>
          )}
        </div>
      )}

      {/* Relevance evaluation in progress indicator */}
      {phase === 'relevance' && (
        <div className="flex items-center gap-3 animate-pulse">
          <PhaseIcon phase="relevance" />
          <div>
            <div className="font-semibold text-foreground">
              {t('processing.evaluatingRelevance')}
            </div>
            <div className="text-xs text-muted-foreground">
              {t('processing.analyzingSearchQuality')}
            </div>
          </div>
        </div>
      )}

      {/* Relevance data */}
      {relevanceData && (
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <PhaseIcon phase="relevance" />
            <div>
              <div className="font-semibold text-cyan-600 dark:text-cyan-400">
                {t('processing.relevanceEvaluated', { count: relevanceData.evaluated_count })}
              </div>
              <div className="text-xs text-muted-foreground">
                {t('processing.qualityAssessmentComplete')}
              </div>
            </div>
          </div>
          <div className="ml-13">
            <div className="glass-panel p-3 inline-block">
              <span className="text-sm text-muted-foreground">
                {t('processing.maxRelevanceScore')}:
              </span>{' '}
              <span className="font-mono text-lg font-bold text-foreground">
                {(relevanceData.max_score * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Answer generation in progress indicator */}
      {phase === 'compose' && (
        <div className="flex items-center gap-3 animate-pulse">
          <PhaseIcon phase="compose" />
          <div>
            <div className="font-semibold text-foreground">{t('processing.generatingAnswer')}</div>
            <div className="text-xs text-muted-foreground">
              {t('processing.composingResponseWithCitations')}
            </div>
          </div>
        </div>
      )}

      {/* Intent analysis in progress (when intentData is not yet available) */}
      {!intentData && phase === 'intent' && (
        <div className="flex items-center gap-3 animate-pulse">
          <PhaseIcon phase="intent" />
          <div>
            <div className="font-semibold text-foreground">{t('processing.analyzingQuery')}</div>
            <div className="text-xs text-muted-foreground">
              {t('processing.understandingQuestion')}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
