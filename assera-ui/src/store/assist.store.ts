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
import type { Answer, Citation, Timings } from '@/types/api';
import { queryAssist } from '@/libs/apiClient';
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

  send: (query: string, options?: Record<string, any>) => Promise<void>;
  sendStream: (query: string, options?: Record<string, any>) => Promise<void>;
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

  send: async (query: string, options?: Record<string, any>) => {
    set({ loading: true, error: null, fallbackNotice: null });

    try {
      const sessionId = useSessionStore.getState().id || undefined;
      const queryHistory = get().queryHistory;
      const response = await queryAssist({
        query,
        session_id: sessionId,
        query_history: queryHistory.length > 0 ? queryHistory : undefined,
        options,
      });

      // Update session
      useSessionStore.getState().set({
        id: response.session.id,
        turn: response.session.turn,
      });

      // Set results
      set({
        answer: response.answer,
        citations: response.citations,
        selectedCitationId: response.citations[0]?.id ?? null,
        timings: response.timings,
        fallbackNotice: response.notice?.fallback
          ? `LLM fallback: ${response.notice.reason}`
          : null,
        loading: false,
      });
    } catch (error: any) {
      set({
        error: error.message || 'Request failed',
        loading: false,
      });
    }
  },

  sendStream: async (query: string, options?: Record<string, any>) => {
    set({
      loading: true,
      streaming: true,
      error: null,
      fallbackNotice: null,
      answer: { text: '', suggested_questions: [] },
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
          onIntent: (data) => {
            console.log('Intent extracted:', data);
          },
          onCitations: (data) => {
            set({
              citations: data.citations,
              selectedCitationId: data.citations[0]?.id ?? null,
            });
          },
          onChunk: (data) => {
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
            });
          },
          onError: (data) => {
            set({
              error: data.message || 'Streaming failed',
              loading: false,
              streaming: false,
            });
          },
        }
      );
    } catch (error: any) {
      set({
        error: error.message || 'Streaming failed',
        loading: false,
        streaming: false,
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
    }),
}));
