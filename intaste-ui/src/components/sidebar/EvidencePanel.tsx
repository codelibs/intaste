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
import type { Citation } from '@/types/api';
import { EvidenceItem } from './EvidenceItem';
import { cn } from '@/libs/utils';
import { useTranslation } from '@/libs/i18n/client';

interface EvidencePanelProps {
  citations: Citation[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  className?: string;
}

export function EvidencePanel({ citations, selectedId, onSelect, className }: EvidencePanelProps) {
  const { t } = useTranslation();
  const [tab, setTab] = useState<'selected' | 'all'>('selected');

  const selectedCitation = citations.find((c) => c.id === selectedId);

  return (
    <div className={cn('flex flex-col h-full', className)}>
      {/* Tab Header */}
      <div className="border-b" role="tablist">
        <div className="flex">
          <button
            role="tab"
            aria-selected={tab === 'selected'}
            onClick={() => setTab('selected')}
            className={cn(
              'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
              tab === 'selected'
                ? 'border-primary text-foreground'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            )}
          >
            {t('evidence.selected')}
          </button>
          <button
            role="tab"
            aria-selected={tab === 'all'}
            onClick={() => setTab('all')}
            className={cn(
              'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
              tab === 'all'
                ? 'border-primary text-foreground'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            )}
          >
            {t('evidence.all', { count: citations.length })}
          </button>
        </div>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto p-4" role="tabpanel">
        {tab === 'selected' ? (
          (() => {
            // Filter citations by relevance threshold (default 0.8 = 80%)
            const RELEVANCE_THRESHOLD = 0.8;
            const highRelevanceCitations = citations.filter(
              (c) => (c.relevance_score ?? 0) >= RELEVANCE_THRESHOLD
            );

            // Show high relevance citations if any exist, otherwise show selected citation
            if (highRelevanceCitations.length > 0) {
              return (
                <div className="space-y-3">
                  {highRelevanceCitations.map((citation) => (
                    <EvidenceItem
                      key={citation.id}
                      citation={citation}
                      active={citation.id === selectedId}
                      onSelect={() => onSelect(citation.id)}
                      showFull
                    />
                  ))}
                </div>
              );
            } else if (selectedCitation) {
              return (
                <EvidenceItem
                  citation={selectedCitation}
                  active={true}
                  onSelect={() => {}}
                  showFull
                />
              );
            } else {
              return (
                <div className="text-center text-sm text-muted-foreground py-8">
                  {t('evidence.noSelection')}
                </div>
              );
            }
          })()
        ) : (
          <div className="space-y-3">
            {citations.map((citation) => (
              <EvidenceItem
                key={citation.id}
                citation={citation}
                active={citation.id === selectedId}
                onSelect={() => onSelect(citation.id)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
