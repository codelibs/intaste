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

import { describe, it, expect, beforeEach } from 'vitest';
import { useSessionStore } from '@/store/session.store';

describe('SessionStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    useSessionStore.setState({
      id: null,
      turn: 0,
    });
  });

  it('initializes with default state', () => {
    const state = useSessionStore.getState();

    expect(state.id).toBe(null);
    expect(state.turn).toBe(0);
  });

  it('sets session ID', () => {
    const id = 'test-session-123';
    useSessionStore.getState().set({ id });

    expect(useSessionStore.getState().id).toBe(id);
  });

  it('increments turn number', () => {
    useSessionStore.getState().set({ turn: 1 });

    expect(useSessionStore.getState().turn).toBe(1);

    useSessionStore.getState().set({ turn: 2 });

    expect(useSessionStore.getState().turn).toBe(2);
  });

  it('resets session to initial state', () => {
    useSessionStore.setState({
      id: 'existing-session',
      turn: 5,
    });

    useSessionStore.getState().reset();

    const state = useSessionStore.getState();
    expect(state.id).toBe(null);
    expect(state.turn).toBe(0);
  });

  it('handles multiple session changes', () => {
    useSessionStore.getState().set({ id: 'session-1' });
    useSessionStore.getState().set({ turn: 1 });
    useSessionStore.getState().set({ turn: 2 });

    expect(useSessionStore.getState().turn).toBe(2);

    useSessionStore.getState().set({ id: 'session-2' });

    // Turn should still be 2 after changing session
    // (unless explicitly reset)
    expect(useSessionStore.getState().turn).toBe(2);
  });

  it('allows setting session ID to null', () => {
    useSessionStore.setState({ id: 'existing-session' });
    useSessionStore.getState().set({ id: null });

    expect(useSessionStore.getState().id).toBe(null);
  });
});
