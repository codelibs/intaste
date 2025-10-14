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
 * Session store for managing conversation state.
 */

import { create } from 'zustand';

interface SessionState {
  id: string | null;
  turn: number;
  set: (patch: Partial<Omit<SessionState, 'set' | 'reset'>>) => void;
  reset: () => void;
}

export const useSessionStore = create<SessionState>((set) => ({
  id: null,
  turn: 0,

  set: (patch) => set(patch),

  reset: () => set({ id: null, turn: 0 }),
}));
