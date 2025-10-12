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

import { describe, it, expect, vi } from 'vitest';
import { renderWithProviders, screen, createMockAnswer } from '../utils/test-utils';
import userEvent from '@testing-library/user-event';
import AnswerBubble from '@/components/answer/AnswerBubble';

describe('AnswerBubble', () => {
  it('renders answer text', () => {
    const answer = createMockAnswer();
    renderWithProviders(<AnswerBubble answer={answer} />);

    expect(screen.getByText(/this is a test answer/i)).toBeInTheDocument();
  });

  it('renders citation references as clickable buttons', () => {
    const answer = {
      text: 'This is an answer with [1] and [2] citations',
      suggested_followups: [],
    };
    renderWithProviders(<AnswerBubble answer={answer} />);

    const citation1 = screen.getByRole('button', { name: '[1]' });
    const citation2 = screen.getByRole('button', { name: '[2]' });

    expect(citation1).toBeInTheDocument();
    expect(citation2).toBeInTheDocument();
  });

  it('calls onCitationClick when citation is clicked', async () => {
    const handleCitationClick = vi.fn();
    const user = userEvent.setup();
    const answer = {
      text: 'Answer with [1] citation',
      suggested_followups: [],
    };

    renderWithProviders(
      <AnswerBubble answer={answer} onCitationClick={handleCitationClick} />
    );

    const citation = screen.getByRole('button', { name: '[1]' });
    await user.click(citation);

    expect(handleCitationClick).toHaveBeenCalledWith('1');
  });

  it('renders suggested follow-up questions', () => {
    const answer = {
      text: 'Test answer',
      suggested_followups: ['What else?', 'Tell me more'],
    };
    renderWithProviders(<AnswerBubble answer={answer} />);

    expect(screen.getByText('What else?')).toBeInTheDocument();
    expect(screen.getByText('Tell me more')).toBeInTheDocument();
  });

  it('calls onFollowupClick when follow-up is clicked', async () => {
    const handleFollowupClick = vi.fn();
    const user = userEvent.setup();
    const answer = {
      text: 'Test answer',
      suggested_followups: ['What else?'],
    };

    renderWithProviders(
      <AnswerBubble answer={answer} onFollowupClick={handleFollowupClick} />
    );

    const followup = screen.getByText('What else?');
    await user.click(followup);

    expect(handleFollowupClick).toHaveBeenCalledWith('What else?');
  });

  it('does not render follow-ups section when empty', () => {
    const answer = {
      text: 'Test answer',
      suggested_followups: [],
    };
    renderWithProviders(<AnswerBubble answer={answer} />);

    expect(screen.queryByText(/follow-up/i)).not.toBeInTheDocument();
  });

  it('handles answer text without citations', () => {
    const answer = {
      text: 'Simple answer without citations',
      suggested_followups: [],
    };
    renderWithProviders(<AnswerBubble answer={answer} />);

    expect(screen.getByText(/simple answer/i)).toBeInTheDocument();
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
});
