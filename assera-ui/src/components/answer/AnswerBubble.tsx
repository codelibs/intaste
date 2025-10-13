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

import type { Answer } from '@/types/api';
import { cn } from '@/libs/utils';

interface AnswerBubbleProps {
  answer: Answer;
  fallbackNotice?: string | null;
  onCitationClick?: (id: number) => void;
  className?: string;
}

export function AnswerBubble({
  answer,
  fallbackNotice,
  onCitationClick,
  className,
}: AnswerBubbleProps) {
  // Parse citation markers [1], [2], etc. and make them clickable
  const renderTextWithCitations = (text: string) => {
    const parts = text.split(/(\[\d+\])/g);
    return parts.map((part, idx) => {
      const match = part.match(/\[(\d+)\]/);
      if (match) {
        const citationId = parseInt(match[1], 10);
        return (
          <button
            key={idx}
            onClick={() => onCitationClick?.(citationId)}
            className="text-primary hover:underline focus:outline-none focus:ring-1 focus:ring-ring rounded"
            aria-label={`View citation ${citationId}`}
          >
            {part}
          </button>
        );
      }
      return <span key={idx}>{part}</span>;
    });
  };

  return (
    <div className={cn('rounded-lg border bg-card p-4 shadow-sm', className)}>
      {fallbackNotice && (
        <div className="mb-3 flex items-start gap-2 rounded-md bg-yellow-50 dark:bg-yellow-900/20 p-2 text-xs text-yellow-800 dark:text-yellow-200">
          <span className="text-base">⚠️</span>
          <span>{fallbackNotice}</span>
        </div>
      )}

      <div className="prose prose-sm dark:prose-invert max-w-none">
        <p className="text-foreground leading-relaxed">{renderTextWithCitations(answer.text)}</p>
      </div>

      {answer.suggested_questions && answer.suggested_questions.length > 0 && (
        <div className="mt-4 pt-4 border-t">
          <p className="text-xs font-medium text-muted-foreground mb-2">Related questions:</p>
          <div className="flex flex-wrap gap-2">
            {answer.suggested_questions.map((question, idx) => (
              <span key={idx} className="text-xs text-muted-foreground">
                • {question}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
