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
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryHistory } from '@/components/history/QueryHistory';

describe('QueryHistory', () => {
  it('renders null when history is empty', () => {
    const { container } = render(<QueryHistory history={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders history items', () => {
    const history = ['query 1', 'query 2', 'query 3'];
    render(<QueryHistory history={history} />);

    expect(screen.getByText(/query 1/)).toBeInTheDocument();
    expect(screen.getByText(/query 2/)).toBeInTheDocument();
    expect(screen.getByText(/query 3/)).toBeInTheDocument();
  });

  it('displays Search History title', () => {
    const history = ['test query'];
    render(<QueryHistory history={history} />);

    expect(screen.getByText('Search History')).toBeInTheDocument();
  });

  it('numbers history items starting from 1', () => {
    const history = ['first', 'second', 'third'];
    render(<QueryHistory history={history} />);

    expect(screen.getByText('1.')).toBeInTheDocument();
    expect(screen.getByText('2.')).toBeInTheDocument();
    expect(screen.getByText('3.')).toBeInTheDocument();
  });

  it('calls onQueryClick when history item is clicked', () => {
    const onQueryClick = vi.fn();
    const history = ['clickable query'];

    render(<QueryHistory history={history} onQueryClick={onQueryClick} />);

    const item = screen.getByText(/clickable query/);
    fireEvent.click(item);

    expect(onQueryClick).toHaveBeenCalledWith('clickable query');
    expect(onQueryClick).toHaveBeenCalledTimes(1);
  });

  it('renders Clear button when onClear is provided', () => {
    const onClear = vi.fn();
    const history = ['test query'];

    render(<QueryHistory history={history} onClear={onClear} />);

    expect(screen.getByText('Clear')).toBeInTheDocument();
  });

  it('calls onClear when Clear button is clicked', () => {
    const onClear = vi.fn();
    const history = ['test query'];

    render(<QueryHistory history={history} onClear={onClear} />);

    const clearButton = screen.getByText('Clear');
    fireEvent.click(clearButton);

    expect(onClear).toHaveBeenCalledTimes(1);
  });

  it('does not render Clear button when onClear is not provided', () => {
    const history = ['test query'];

    render(<QueryHistory history={history} />);

    expect(screen.queryByText('Clear')).not.toBeInTheDocument();
  });

  it('applies custom className', () => {
    const history = ['test query'];
    const { container } = render(<QueryHistory history={history} className="custom-class" />);

    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper.className).toContain('custom-class');
  });

  it('renders long queries with line-clamp', () => {
    const longQuery = 'This is a very long query that should be clamped to two lines maximum';
    const history = [longQuery];

    render(<QueryHistory history={history} />);

    const queryElement = screen.getByText(longQuery);
    expect(queryElement.className).toContain('line-clamp-2');
  });

  it('handles multiple history items with different lengths', () => {
    const history = [
      'short',
      'medium length query',
      'this is a very long query that goes on and on and should be truncated',
    ];

    render(<QueryHistory history={history} />);

    history.forEach((query) => {
      expect(screen.getByText(new RegExp(query.slice(0, 10)))).toBeInTheDocument();
    });
  });

  it('shows cursor pointer when onQueryClick is provided', () => {
    const onQueryClick = vi.fn();
    const history = ['clickable'];

    const { container } = render(<QueryHistory history={history} onQueryClick={onQueryClick} />);

    const items = container.querySelectorAll('.group');
    expect(items[0].className).toContain('cursor-pointer');
  });

  it('does not show cursor pointer when onQueryClick is not provided', () => {
    const history = ['not clickable'];

    const { container } = render(<QueryHistory history={history} />);

    const items = container.querySelectorAll('.group');
    expect(items[0].className).not.toContain('cursor-pointer');
  });

  it('renders exactly the number of items in history', () => {
    const history = ['q1', 'q2', 'q3', 'q4', 'q5'];

    const { container } = render(<QueryHistory history={history} />);

    const items = container.querySelectorAll('.group');
    expect(items.length).toBe(5);
  });

  it('maintains scroll container for long histories', () => {
    const history = Array.from({ length: 20 }, (_, i) => `query ${i + 1}`);

    const { container } = render(<QueryHistory history={history} />);

    const scrollContainer = container.querySelector('.overflow-y-auto');
    expect(scrollContainer).toBeInTheDocument();
    expect(scrollContainer?.className).toContain('max-h-48');
  });
});
