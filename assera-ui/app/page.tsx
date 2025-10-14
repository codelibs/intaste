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
import { useAssistStore } from '@/store/assist.store';
import { useUIStore } from '@/store/ui.store';
import { QueryInput } from '@/components/input/QueryInput';
import { QueryHistory } from '@/components/history/QueryHistory';
import { AnswerBubble } from '@/components/answer/AnswerBubble';
import { EvidencePanel } from '@/components/sidebar/EvidencePanel';
import { LatencyIndicator } from '@/components/common/LatencyIndicator';
import { ErrorBanner } from '@/components/common/ErrorBanner';
import { EmptyState } from '@/components/common/EmptyState';

export default function HomePage() {
  const [query, setQuery] = useState('');
  const apiToken = useUIStore((state) => state.apiToken);
  const setApiToken = useUIStore((state) => state.setApiToken);
  const streamingEnabled = useUIStore((state) => state.streamingEnabled);
  const setStreamingEnabled = useUIStore((state) => state.setStreamingEnabled);

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
    send,
    sendStream,
    selectCitation,
    addQueryToHistory,
    clearQueryHistory,
  } = useAssistStore();

  const handleSubmit = async () => {
    if (!query.trim() || loading) return;

    // Check for API token
    if (!apiToken) {
      alert('Please set your API token first. Check the settings.');
      return;
    }

    // Add query to history before sending
    addQueryToHistory(query);

    // Use streaming or standard query based on setting
    if (streamingEnabled) {
      await sendStream(query);
    } else {
      await send(query);
    }
    // Optionally clear query after send
    // setQuery('');
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
          <h1 className="text-xl font-bold text-foreground">Assera</h1>
          <div className="flex items-center gap-4">
            {/* Streaming Toggle */}
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={streamingEnabled}
                onChange={(e) => setStreamingEnabled(e.target.checked)}
                className="w-4 h-4"
              />
              <span className="text-muted-foreground">
                {streaming ? '⚡ Streaming...' : streamingEnabled ? '⚡ Stream' : 'Standard'}
              </span>
            </label>

            {!apiToken && (
              <button
                onClick={() => {
                  const token = prompt('Enter your API token:');
                  if (token) {
                    setApiToken(token);
                  }
                }}
                className="text-sm px-3 py-1 rounded bg-primary text-primary-foreground hover:bg-primary/90"
              >
                Set API Token
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
                onClear={clearQueryHistory}
              />
            )}

            {/* Query Input */}
            <QueryInput
              value={query}
              onChange={setQuery}
              onSubmit={handleSubmit}
              disabled={loading}
              placeholder="Enter your question here..."
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
                fallbackNotice={fallbackNotice}
                onCitationClick={handleCitationClick}
              />
            )}

            {/* Empty State */}
            {!loading && !error && !answer && citations.length === 0 && (
              <EmptyState
                title="Welcome to Assera"
                message="Enter your question above to get started with AI-assisted search."
                suggestions={[
                  'Ask questions in natural language',
                  'Results will include citations and sources',
                  'Click citation numbers to view details',
                ]}
              />
            )}

            {/* Loading State */}
            {loading && (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent"></div>
                <p className="mt-4 text-sm text-muted-foreground">Searching...</p>
              </div>
            )}

            {/* No Results */}
            {!loading && answer && citations.length === 0 && (
              <EmptyState
                title="No sources found"
                message="Try different keywords or check your search criteria."
                suggestions={['Use broader search terms', 'Check spelling', 'Try related keywords']}
              />
            )}
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
            Assera v0.1.0 • Apache License 2.0 •{' '}
            <a
              href="https://github.com/codelibs/assera"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline"
            >
              GitHub
            </a>
          </p>
        </div>
      </footer>
    </div>
  );
}
