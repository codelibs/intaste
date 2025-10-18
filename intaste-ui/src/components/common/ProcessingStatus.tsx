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

interface ProcessingStatusProps {
  phase: 'intent' | 'search' | 'compose';
  intentData?: {
    normalized_query: string;
    filters?: Record<string, any>;
    followups: string[];
  };
  citationsData?: {
    total: number;
    topResults: string[];
  };
  lang?: 'ja' | 'en';
}

export function ProcessingStatus({
  phase,
  intentData,
  citationsData,
  lang = 'ja',
}: ProcessingStatusProps) {
  return (
    <div className="space-y-3 text-sm">
      {/* Intent data */}
      {intentData && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-primary">
            <span>🔍</span>
            <span className="font-medium">
              {lang === 'ja' ? '検索キーワード' : 'Search Keywords'}:
            </span>
          </div>
          <div className="pl-6 text-foreground font-mono bg-muted/50 rounded p-2">
            &quot;{intentData.normalized_query}&quot;
          </div>

          {intentData.filters && Object.keys(intentData.filters).length > 0 && (
            <div className="pl-6 text-xs text-muted-foreground">
              📌 {lang === 'ja' ? '検索条件' : 'Filters'}: {JSON.stringify(intentData.filters)}
            </div>
          )}

          {intentData.followups.length > 0 && (
            <div className="space-y-1">
              <div className="pl-6 text-muted-foreground">
                💡 {lang === 'ja' ? '関連する質問' : 'Related Questions'}:
              </div>
              <ul className="pl-8 space-y-0.5 text-muted-foreground text-xs">
                {intentData.followups.map((q, i) => (
                  <li key={i}>• {q}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Search in progress indicator */}
      {phase === 'search' && (
        <div className="flex items-center gap-2 text-primary animate-pulse">
          <span className="inline-block animate-spin h-4 w-4 border-2 border-primary border-t-transparent rounded-full"></span>
          <span>🔎 {lang === 'ja' ? '関連情報を検索中...' : 'Searching...'}</span>
        </div>
      )}

      {/* Citations data */}
      {citationsData && citationsData.total > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
            <span>✅</span>
            <span className="font-medium">
              {citationsData.total}
              {lang === 'ja' ? '件の関連情報が見つかりました' : ' results found'}
            </span>
          </div>

          {citationsData.topResults.length > 0 && (
            <div className="space-y-1">
              <div className="pl-6 text-muted-foreground">
                📄 {lang === 'ja' ? '検索結果' : 'Top Results'}:
              </div>
              <ol className="pl-8 space-y-1 text-sm">
                {citationsData.topResults.map((title, i) => (
                  <li key={i} className="text-foreground">
                    {i + 1}. {title}
                  </li>
                ))}
              </ol>
            </div>
          )}
        </div>
      )}

      {/* Answer generation in progress indicator */}
      {phase === 'compose' && (
        <div className="flex items-center gap-2 text-primary animate-pulse">
          <span className="inline-block animate-spin h-4 w-4 border-2 border-primary border-t-transparent rounded-full"></span>
          <span>💬 {lang === 'ja' ? '回答を生成中...' : 'Generating answer...'}</span>
        </div>
      )}

      {/* Intent analysis in progress (when intentData is not yet available) */}
      {!intentData && phase === 'intent' && (
        <div className="flex items-center gap-2 text-primary animate-pulse">
          <span className="inline-block animate-spin h-4 w-4 border-2 border-primary border-t-transparent rounded-full"></span>
          <span>🔍 {lang === 'ja' ? '質問を分析中...' : 'Analyzing query...'}</span>
        </div>
      )}
    </div>
  );
}
