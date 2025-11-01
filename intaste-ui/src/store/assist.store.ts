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

/**
 * Assist store for managing search state and results.
 */

import { create } from 'zustand';
import type { Answer, Citation, Timings, AssistQueryRequest } from '@/types/api';
import { queryAssistStream } from '@/libs/streamingClient';
import { useSessionStore } from './session.store';

interface AssistState {
  loading: boolean;
  streaming: boolean;
  error: string | null;
  answer: Answer | null;
  citations: Citation[];
  selectedCitationId: number | null;
  timings: Timings | null;
  fallbackNotice: string | null;
  queryHistory: string[];
  processingPhase: 'intent' | 'search' | 'relevance' | 'compose' | null;
  searchStartTime: number | null;
  intentData: {
    normalized_query: string;
    filters?: Record<string, string | number | boolean | null>;
    followups: string[];
  } | null;
  citationsData: {
    total: number;
    topResults: string[];
  } | null;
  relevanceData: {
    evaluated_count: number;
    max_score: number;
  } | null;
  retryData: {
    attempt: number;
    reason: string;
    previous_max_score: number;
  } | null;

  send: (query: string, options?: AssistQueryRequest['options']) => Promise<void>;
  selectCitation: (id: number | null) => void;
  addQueryToHistory: (query: string) => void;
  clearQueryHistory: () => void;
  clear: () => void;
}

export const useAssistStore = create<AssistState>((set, get) => ({
  loading: false,
  streaming: false,
  error: null,
  answer: null,
  citations: [],
  selectedCitationId: null,
  timings: null,
  fallbackNotice: null,
  queryHistory: [],
  processingPhase: null,
  searchStartTime: null,
  intentData: null,
  citationsData: null,
  relevanceData: null,
  retryData: null,

  send: async (query: string, options?: AssistQueryRequest['options']) => {
    set({
      loading: true,
      streaming: true,
      error: null,
      fallbackNotice: null,
      answer: { text: '', suggested_questions: [] },
      processingPhase: null,
      searchStartTime: Date.now(),
      intentData: null,
      citationsData: null,
      relevanceData: null,
      retryData: null,
    });

    try {
      const sessionId = useSessionStore.getState().id || undefined;
      const queryHistory = get().queryHistory;
      let accumulatedText = '';

      await queryAssistStream(
        query,
        options,
        sessionId,
        queryHistory.length > 0 ? queryHistory : undefined,
        {
          onStart: (data) => {
            console.log('Stream started:', data);
          },
          onStatus: (data) => {
            set({ processingPhase: data.phase });
          },
          onIntent: (data) => {
            console.log('Intent extracted:', data);
            set({
              intentData: {
                normalized_query: data.normalized_query,
                filters: data.filters,
                followups: data.followups || [],
              },
            });
          },
          onCitations: (data) => {
            const topResults = data.citations.slice(0, 3).map((c: Citation) => c.title);

            set({
              citations: data.citations,
              selectedCitationId: data.citations[0]?.id ?? null,
              citationsData: {
                total: data.citations.length,
                topResults,
              },
            });
          },
          onRelevance: (data) => {
            console.log('Relevance evaluated:', data);
            set({
              relevanceData: {
                evaluated_count: data.evaluated_count,
                max_score: data.max_score,
              },
            });
          },
          onRetry: (data) => {
            console.log('Retry search:', data);
            set({
              retryData: {
                attempt: data.attempt,
                reason: data.reason,
                previous_max_score: data.previous_max_score,
              },
            });
          },
          onChunk: (data) => {
            // Clear processing info on first chunk
            if (accumulatedText === '') {
              set({
                processingPhase: null,
                intentData: null,
                citationsData: null,
                relevanceData: null,
                retryData: null,
              });
            }
            accumulatedText += data.text;
            set({
              answer: {
                text: accumulatedText,
                suggested_questions: [],
              },
            });
          },
          onComplete: (data) => {
            // Update session
            useSessionStore.getState().set({
              id: data.session?.id || sessionId,
              turn: data.session?.turn || 1,
            });

            set({
              answer: data.answer,
              timings: data.timings,
              loading: false,
              streaming: false,
              searchStartTime: null,
            });
          },
          onError: (data) => {
            set({
              error: data.message || 'Streaming failed',
              loading: false,
              streaming: false,
              searchStartTime: null,
            });
          },
        }
      );
    } catch (error: unknown) {
      set({
        error: error instanceof Error ? error.message : 'Streaming failed',
        loading: false,
        streaming: false,
        searchStartTime: null,
      });
    }
  },

  selectCitation: (id: number | null) => {
    set({ selectedCitationId: id });
  },

  addQueryToHistory: (query: string) => {
    const trimmedQuery = query.trim();
    if (!trimmedQuery) return;

    set((state) => {
      // Add to beginning (most recent first), limit to 10 items
      const newHistory = [
        trimmedQuery,
        ...state.queryHistory.filter((q) => q !== trimmedQuery),
      ].slice(0, 10);
      return { queryHistory: newHistory };
    });
  },

  clearQueryHistory: () => {
    set({ queryHistory: [] });
  },

  clear: () =>
    set({
      loading: false,
      streaming: false,
      error: null,
      answer: null,
      citations: [],
      selectedCitationId: null,
      timings: null,
      fallbackNotice: null,
      queryHistory: [],
      searchStartTime: null,
    }),
}));
