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
import {
  TabList,
  Tab,
  Card,
  Text,
  makeStyles,
  mergeClasses,
  tokens,
  type SelectTabData,
  type SelectTabEvent,
} from '@fluentui/react-components';
import { useTranslation } from '@/libs/i18n/client';

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
  },
  tabsContainer: {
    borderBottomWidth: '1px',
    borderBottomStyle: 'solid',
    borderBottomColor: tokens.colorNeutralStroke2,
  },
  tabContent: {
    flex: 1,
    overflowY: 'auto',
    padding: tokens.spacingVerticalL,
  },
  citationsList: {
    display: 'flex',
    flexDirection: 'column',
    gap: tokens.spacingVerticalM,
  },
  emptyState: {
    textAlign: 'center',
    paddingTop: tokens.spacingVerticalXXXL,
    paddingBottom: tokens.spacingVerticalXXXL,
  },
});

interface EvidencePanelProps {
  citations: Citation[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  className?: string;
}

export function EvidencePanel({ citations, selectedId, onSelect, className }: EvidencePanelProps) {
  const { t } = useTranslation();
  const styles = useStyles();
  const [tab, setTab] = useState<'selected' | 'all'>('selected');

  const selectedCitation = citations.find((c) => c.id === selectedId);

  const handleTabSelect = (_event: SelectTabEvent, data: SelectTabData) => {
    setTab(data.value as 'selected' | 'all');
  };

  return (
    <Card appearance="filled" className={mergeClasses(styles.container, className)}>
      {/* Tab Header */}
      <div className={styles.tabsContainer}>
        <TabList selectedValue={tab} onTabSelect={handleTabSelect}>
          <Tab value="selected">{t('evidence.selected')}</Tab>
          <Tab value="all">{t('evidence.all', { count: citations.length })}</Tab>
        </TabList>
      </div>

      {/* Tab Content */}
      <div className={styles.tabContent}>
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
                <div className={styles.citationsList}>
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
                <div className={styles.emptyState}>
                  <Text size={300}>{t('evidence.noSelection')}</Text>
                </div>
              );
            }
          })()
        ) : (
          <div className={styles.citationsList}>
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
    </Card>
  );
}
