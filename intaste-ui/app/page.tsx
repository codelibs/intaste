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

import { useState } from 'react';
import Image from 'next/image';
import { useAssistStore } from '@/store/assist.store';
import { useUIStore } from '@/store/ui.store';
import { useLanguageStore } from '@/store/language.store';
import { useTranslation } from '@/libs/i18n/client';
import { QueryInput } from '@/components/input/QueryInput';
import { QueryHistory } from '@/components/history/QueryHistory';
import { AnswerBubble } from '@/components/answer/AnswerBubble';
import { EvidencePanel } from '@/components/sidebar/EvidencePanel';
import { LatencyIndicator } from '@/components/common/LatencyIndicator';
import { SearchingIndicator } from '@/components/common/SearchingIndicator';
import { ErrorBanner } from '@/components/common/ErrorBanner';
import { EmptyState } from '@/components/common/EmptyState';
import { LanguageSwitcher } from '@/components/common/LanguageSwitcher';

export default function HomePage() {
  const { t } = useTranslation();
  const [query, setQuery] = useState('');
  const apiToken = useUIStore((state) => state.apiToken);
  const setApiToken = useUIStore((state) => state.setApiToken);
  const currentLanguage = useLanguageStore((state) => state.currentLanguage);

  const {
    loading,
    streaming,
    error,
    answer,
    citations,
    selectedCitationId,
    timings,
    fallbackNotice,
    queryHistory,
    processingPhase,
    intentData,
    citationsData,
    relevanceData,
    send,
    selectCitation,
    addQueryToHistory,
    clear,
  } = useAssistStore();

  const handleSubmit = async () => {
    if (!query.trim() || loading) return;

    // Check for API token
    if (!apiToken) {
      const token = prompt(t('header.apiTokenPrompt'));
      if (token) {
        setApiToken(token);
      }
      return;
    }

    // Add query to history before sending
    addQueryToHistory(query);

    // All queries use streaming (no separate non-streaming endpoint)
    // Pass language option to ensure response is in the selected language
    await send(query, { language: currentLanguage });
    // Clear query input after successful submission
    setQuery('');
  };

  const handleHistoryQueryClick = (historicalQuery: string) => {
    setQuery(historicalQuery);
  };

  const handleCitationClick = (id: number) => {
    selectCitation(id);
  };

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="container mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Image src="/logo.svg" alt="Intaste logo" width={32} height={32} priority />
            <h1 className="text-xl font-bold text-foreground">{t('header.title')}</h1>
          </div>
          <div className="flex items-center gap-4">
            {/* Searching indicator with elapsed time */}
            <SearchingIndicator />

            {/* Language Switcher */}
            <LanguageSwitcher />

            {!apiToken && (
              <button
                onClick={() => {
                  const token = prompt(t('header.apiTokenPrompt'));
                  if (token) {
                    setApiToken(token);
                  }
                }}
                className="text-sm px-3 py-1 rounded bg-primary text-primary-foreground hover:bg-primary/90"
              >
                {t('header.setApiToken')}
              </button>
            )}
            {timings && <LatencyIndicator timings={timings} />}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Main Search */}
        <main className="flex-1 flex flex-col p-6 overflow-y-auto">
          <div className="max-w-3xl mx-auto w-full space-y-6">
            {/* Query History */}
            {queryHistory.length > 0 && (
              <QueryHistory
                history={queryHistory}
                onQueryClick={handleHistoryQueryClick}
                onClear={clear}
              />
            )}

            {/* Empty State - shown above input when no content */}
            {!loading && !error && !answer && citations.length === 0 && (
              <EmptyState type="welcome" />
            )}

            {/* Query Input */}
            <QueryInput
              value={query}
              onChange={setQuery}
              onSubmit={handleSubmit}
              disabled={loading}
            />

            {/* Error Display */}
            {error && (
              <ErrorBanner
                message={error}
                onRetry={handleSubmit}
                onDismiss={() => useAssistStore.setState({ error: null })}
              />
            )}

            {/* Answer Display */}
            {answer && (
              <AnswerBubble
                answer={answer}
                streaming={streaming}
                processingPhase={processingPhase}
                intentData={intentData}
                citationsData={citationsData}
                relevanceData={relevanceData}
                fallbackNotice={fallbackNotice}
                onCitationClick={handleCitationClick}
              />
            )}

            {/* Loading State */}
            {loading && (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent"></div>
                <p className="mt-4 text-sm text-muted-foreground">{t('loading.searching')}</p>
              </div>
            )}

            {/* No Results */}
            {!loading && answer && citations.length === 0 && <EmptyState type="noResults" />}
          </div>
        </main>

        {/* Right Panel - Evidence */}
        {citations.length > 0 && (
          <aside className="w-96 border-l bg-card">
            <EvidencePanel
              citations={citations}
              selectedId={selectedCitationId}
              onSelect={selectCitation}
            />
          </aside>
        )}
      </div>

      {/* Footer */}
      <footer className="border-t bg-card py-2 px-4">
        <div className="container mx-auto text-center text-xs text-muted-foreground">
          <p>
            {t('footer.version', { version: '0.1.0' })} • {t('footer.license')} •{' '}
            <a
              href="https://github.com/codelibs/intaste"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline"
            >
              {t('footer.github')}
            </a>
          </p>
        </div>
      </footer>
    </div>
  );
}
