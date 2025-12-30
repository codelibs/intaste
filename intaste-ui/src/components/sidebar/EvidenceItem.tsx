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
import { truncateSnippet, isValidHttpUrl } from '@/libs/sanitizer';
import {
  Card,
  Badge,
  Text,
  Link,
  makeStyles,
  mergeClasses,
  tokens,
} from '@fluentui/react-components';
import { ArrowUpRight16Regular } from '@fluentui/react-icons';
import { useTranslation } from '@/libs/i18n/client';

// Maximum character length for snippet display (configurable via environment variable)
const SNIPPET_MAX_LENGTH = parseInt(process.env.NEXT_PUBLIC_SNIPPET_MAX_LENGTH || '100', 10);

const useStyles = makeStyles({
  card: {
    padding: tokens.spacingVerticalL,
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    ':hover': {
      transform: 'scale(1.02)',
    },
  },
  cardActive: {
    outline: `2px solid ${tokens.colorBrandBackground}`,
    outlineOffset: '0',
  },
  header: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: tokens.spacingHorizontalM,
    marginBottom: tokens.spacingVerticalS,
  },
  badgeActive: {
    backgroundColor: tokens.colorBrandBackground,
    color: tokens.colorNeutralForegroundOnBrand,
  },
  badgeInactive: {
    backgroundColor: tokens.colorNeutralBackground3,
    color: tokens.colorNeutralForeground3,
  },
  title: {
    flex: 1,
    display: '-webkit-box',
    WebkitLineClamp: 2,
    WebkitBoxOrient: 'vertical',
    overflow: 'hidden',
  },
  snippet: {
    marginTop: tokens.spacingVerticalS,
    lineHeight: '1.6',
  },
  snippetClamped: {
    display: '-webkit-box',
    WebkitLineClamp: 3,
    WebkitBoxOrient: 'vertical',
    overflow: 'hidden',
  },
  metadata: {
    marginTop: tokens.spacingVerticalM,
    paddingTop: tokens.spacingVerticalM,
    borderTopWidth: '1px',
    borderTopStyle: 'solid',
    borderTopColor: tokens.colorNeutralStroke2,
  },
  metadataRow: {
    display: 'flex',
    gap: tokens.spacingHorizontalXS,
    marginBottom: tokens.spacingVerticalXS,
  },
  linkContainer: {
    marginTop: tokens.spacingVerticalM,
  },
});

interface EvidenceItemProps {
  citation: Citation;
  active: boolean;
  onSelect: () => void;
  showFull?: boolean;
}

export function EvidenceItem({ citation, active, onSelect, showFull = false }: EvidenceItemProps) {
  const { t } = useTranslation();
  const styles = useStyles();

  return (
    <Card
      appearance="filled-alternative"
      onClick={onSelect}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onSelect();
        }
      }}
      role="button"
      tabIndex={0}
      aria-pressed={active}
      className={mergeClasses(styles.card, active && styles.cardActive)}
    >
      {/* Citation Number and Title */}
      <div className={styles.header}>
        <Badge
          appearance="filled"
          shape="circular"
          size="large"
          className={active ? styles.badgeActive : styles.badgeInactive}
        >
          {citation.id}
        </Badge>
        <Text size={300} weight="semibold" className={styles.title}>
          {citation.title}
        </Text>
      </div>

      {/* Snippet - SECURITY: Must sanitize HTML from Fess search results */}
      {citation.snippet && (
        <div
          className={styles.snippet}
          // SECURITY: citation.snippet may contain HTML from Fess with search term highlighting.
          // We use truncateSnippet() to sanitize (prevent XSS) and truncate to configured length.
          // This is the ONLY location in the codebase where dangerouslySetInnerHTML is used.
          dangerouslySetInnerHTML={{
            __html: truncateSnippet(citation.snippet, SNIPPET_MAX_LENGTH),
          }}
        />
      )}

      {/* Metadata */}
      {showFull && citation.meta && (
        <div className={styles.metadata}>
          {citation.meta.site && (
            <div className={styles.metadataRow}>
              <Text size={200} weight="semibold">
                {t('citation.site')}:
              </Text>
              <Text size={200}>{citation.meta.site}</Text>
            </div>
          )}
          {citation.meta.content_type && (
            <div className={styles.metadataRow}>
              <Text size={200} weight="semibold">
                {t('citation.type')}:
              </Text>
              <Text size={200}>{citation.meta.content_type}</Text>
            </div>
          )}
          {citation.score !== undefined && (
            <div className={styles.metadataRow}>
              <Text size={200} weight="semibold">
                {t('citation.searchScore')}:
              </Text>
              <Text size={200}>{citation.score.toFixed(2)}</Text>
            </div>
          )}
          {citation.relevance_score !== undefined && (
            <div className={styles.metadataRow}>
              <Text size={200} weight="semibold">
                {t('citation.relevanceScore')}:
              </Text>
              <Text size={200}>{(citation.relevance_score * 100).toFixed(0)}%</Text>
            </div>
          )}
        </div>
      )}

      {/* Open in Fess Link - SECURITY: Only render link if URL is valid HTTP/HTTPS */}
      {showFull && isValidHttpUrl(citation.url) && (
        <div className={styles.linkContainer}>
          <Link
            href={citation.url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
          >
            <Text size={200} weight="medium">
              Open in Fess
            </Text>
            <ArrowUpRight16Regular style={{ marginLeft: tokens.spacingHorizontalXXS }} />
          </Link>
        </div>
      )}
    </Card>
  );
}
