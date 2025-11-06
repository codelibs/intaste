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
import { renderWithProviders, screen } from '../utils/test-utils';
import userEvent from '@testing-library/user-event';
import { QueryInput } from '@/components/input/QueryInput';

describe('QueryInput', () => {
  it('renders textarea with placeholder', () => {
    renderWithProviders(<QueryInput value="" onChange={() => {}} onSubmit={() => {}} />);

    const textarea = screen.getByPlaceholderText(/enter your question/i);
    expect(textarea).toBeInTheDocument();
  });

  it('calls onChange when text is entered', async () => {
    const handleChange = vi.fn();
    const user = userEvent.setup();

    renderWithProviders(<QueryInput value="" onChange={handleChange} onSubmit={() => {}} />);

    const textarea = screen.getByPlaceholderText(/enter your question/i);
    await user.type(textarea, 'test query');

    expect(handleChange).toHaveBeenCalled();
  });

  it('calls onSubmit when Enter is pressed', async () => {
    const handleSubmit = vi.fn();
    const user = userEvent.setup();

    renderWithProviders(
      <QueryInput value="test query" onChange={() => {}} onSubmit={handleSubmit} />
    );

    const textarea = screen.getByPlaceholderText(/enter your question/i);
    await user.click(textarea);
    await user.keyboard('{Enter}');

    expect(handleSubmit).toHaveBeenCalled();
  });

  it('does not submit when Shift+Enter is pressed', async () => {
    const handleSubmit = vi.fn();
    const user = userEvent.setup();

    renderWithProviders(
      <QueryInput value="test query" onChange={() => {}} onSubmit={handleSubmit} />
    );

    const textarea = screen.getByPlaceholderText(/enter your question/i);
    await user.click(textarea);
    await user.keyboard('{Shift>}{Enter}{/Shift}');

    expect(handleSubmit).not.toHaveBeenCalled();
  });

  it('disables input when disabled', () => {
    renderWithProviders(
      <QueryInput value="" onChange={() => {}} onSubmit={() => {}} disabled={true} />
    );

    const textarea = screen.getByPlaceholderText(/enter your question/i);
    expect(textarea).toBeDisabled();
  });

  it('shows character counter', () => {
    renderWithProviders(<QueryInput value="test" onChange={() => {}} onSubmit={() => {}} />);

    expect(screen.getByText(/4.*4096/)).toBeInTheDocument();
  });

  it('prevents submission when empty', async () => {
    const handleSubmit = vi.fn();
    const user = userEvent.setup();

    renderWithProviders(<QueryInput value="" onChange={() => {}} onSubmit={handleSubmit} />);

    const textarea = screen.getByPlaceholderText(/enter your question/i);
    await user.click(textarea);
    await user.keyboard('{Enter}');

    expect(handleSubmit).not.toHaveBeenCalled();
  });

  it('renders Fluent UI Textarea component', async () => {
    const handleChange = vi.fn();

    renderWithProviders(<QueryInput value="" onChange={handleChange} onSubmit={() => {}} />);

    const textarea = screen.getByPlaceholderText(/enter your question/i);
    // Fluent UI Textarea is rendered
    expect(textarea).toBeInTheDocument();
    expect(textarea.tagName).toBe('TEXTAREA');
  });
});
