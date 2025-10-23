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

import type { Citation } from '@/types/api';
import { sanitizeHtml } from '@/libs/sanitizer';
import { cn } from '@/libs/utils';
import { useTranslation } from '@/libs/i18n/client';

interface EvidenceItemProps {
  citation: Citation;
  active: boolean;
  onSelect: () => void;
  showFull?: boolean;
}

export function EvidenceItem({ citation, active, onSelect, showFull = false }: EvidenceItemProps) {
  const { t } = useTranslation();

  return (
    <div
      onClick={onSelect}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onSelect();
        }
      }}
      role="button"
      tabIndex={0}
      aria-selected={active}
      className={cn(
        'rounded-lg border p-3 cursor-pointer transition-all',
        'hover:border-primary/50',
        active ? 'border-primary bg-primary/5' : 'border-border bg-card'
      )}
    >
      {/* Citation Number */}
      <div className="flex items-start gap-2 mb-2">
        <span
          className={cn(
            'flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium',
            active ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
          )}
        >
          {citation.id}
        </span>
        <h4 className="flex-1 text-sm font-medium text-foreground line-clamp-2">
          {citation.title}
        </h4>
      </div>

      {/* Snippet - SECURITY: Must sanitize HTML from Fess search results */}
      {citation.snippet && (
        <div
          className="text-xs text-muted-foreground mt-2 leading-relaxed"
          // SECURITY: citation.snippet may contain HTML from Fess with search term highlighting.
          // We use sanitizeHtml() to prevent XSS attacks while preserving safe formatting tags.
          // This is the ONLY location in the codebase where dangerouslySetInnerHTML is used.
          dangerouslySetInnerHTML={{
            __html: sanitizeHtml(citation.snippet),
          }}
          style={{
            display: showFull ? 'block' : '-webkit-box',
            WebkitLineClamp: showFull ? 'unset' : 3,
            WebkitBoxOrient: 'vertical',
            overflow: showFull ? 'visible' : 'hidden',
          }}
        />
      )}

      {/* Metadata */}
      {showFull && citation.meta && (
        <div className="mt-3 pt-3 border-t space-y-1 text-xs">
          {citation.meta.site && (
            <div>
              <span className="font-medium">{t('citation.site')}:</span>{' '}
              <span className="text-muted-foreground">{citation.meta.site}</span>
            </div>
          )}
          {citation.meta.content_type && (
            <div>
              <span className="font-medium">{t('citation.type')}:</span>{' '}
              <span className="text-muted-foreground">{citation.meta.content_type}</span>
            </div>
          )}
          {citation.score !== undefined && (
            <div>
              <span className="font-medium">{t('citation.searchScore')}:</span>{' '}
              <span className="text-muted-foreground">{citation.score.toFixed(2)}</span>
            </div>
          )}
          {citation.relevance_score !== undefined && (
            <div>
              <span className="font-medium">{t('citation.relevanceScore')}:</span>{' '}
              <span className="text-muted-foreground">
                {(citation.relevance_score * 100).toFixed(0)}%
              </span>
            </div>
          )}
        </div>
      )}

      {/* Open in Fess Link */}
      {showFull && (
        <a
          href={citation.url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-3 inline-flex items-center text-xs text-primary hover:underline"
          onClick={(e) => e.stopPropagation()}
        >
          Open in Fess
          <svg className="ml-1 w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
            />
          </svg>
        </a>
      )}
    </div>
  );
}
