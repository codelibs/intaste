# Assera UI Design Specification

**Document Version:** 1.0
**Last Updated:** 2025-10-12
**Target:** Assera UI (Next.js + shadcn/ui + TailwindCSS + Zustand + i18n)

All external integration is **via Assera API**. **No direct access to Fess**.

**License:** Assera provided under **Apache License 2.0**. Include copyright notice in UI source headers and `NOTICE`.

---

## 1. Screen Configuration (1 Screen + Right Side Pane)

```
┌──────────────────────────────────────────────┐
│ Header: Product name/Model badge/Settings(API token)/Theme/Language toggle │
├───────────────┬───────────────────────────┤
│ Main: Conversational search panel           │ Right Side Pane: Evidence preview     │
│  - Input box (multi-line)                   │  - Tabs: Selected doc / All candidates │
│  - Response bubble (brief) + [1][2][3]      │  - Title / Snippet (sanitized)         │
│  - Suggestions (buttons or chips)           │  - Meta: Updated date/site/type        │
│  - Latency indicator (icon/color)           │  - "Open in Fess" (new tab)            │
├───────────────┴───────────────────────────┤
│ Footer: Terms/License/Version                                             │
└──────────────────────────────────────────────┘
```

- Mobile: Right pane displayed as drawer (bottom slide)

---

## 2. Directory Structure

```
assera-ui/
├─ app/
│  ├─ layout.tsx
│  ├─ page.tsx
│  └─ providers.tsx                  # Zustand, i18n, Theme, etc.
├─ src/
│  ├─ components/
│  │   ├─ header/                    # ModelBadge, ApiTokenDialog, LangThemeSwitch
│  │   ├─ input/                     # QueryInput, SendButton
│  │   ├─ answer/                    # AnswerBubble, SuggestChips
│  │   ├─ sidebar/                   # EvidencePanel, EvidenceItem, MetaTable
│  │   ├─ feedback/                  # ThumbButtons
│  │   ├─ common/                    # LatencyIndicator, ErrorBanner, EmptyState
│  ├─ hooks/
│  │   ├─ useAssist.ts               # API calls, retry, request ID
│  │   ├─ useHotkeys.ts
│  │   └─ useDebouncedValue.ts
│  ├─ libs/
│  │   ├─ apiClient.ts               # fetch wrapper (auth/CORS/JSON/error)
│  │   ├─ sanitizer.ts               # DOMPurify wrapper
│  │   ├─ i18n.ts                    # i18next configuration
│  │   └─ metrics.ts                 # measurement (Web Vitals / custom events)
│  ├─ store/                         # Zustand stores
│  │   ├─ session.store.ts
│  │   ├─ assist.store.ts
│  │   └─ ui.store.ts
│  ├─ styles/
│  │   └─ globals.css
│  └─ types/
│      ├─ api.ts                     # API type definitions (compliant with Assist API detailed design)
│      └─ ui.ts
└─ public/
   └─ locales/ja/*, en/*            # i18n resources
```

---

## 3. Type Definitions (API/Screen I/F)

```typescript
// src/types/api.ts
export type Citation = {
  id: number;
  title: string;
  snippet?: string;     // May contain HTML (sanitize in UI)
  url: string;
  score?: number;
  meta?: Record<string, any>;
};

export type Answer = {
  text: string;
  suggested_questions?: string[]; // Max 3 items
};

export type AssistResponse = {
  answer: Answer;
  citations: Citation[];
  session: { id: string; turn: number };
  timings: { llm_ms: number; search_ms: number; total_ms: number };
  notice?: { fallback?: boolean; reason?: string };
};

export type AssistRequest = {
  query: string;
  session_id?: string;
  options?: { max_results?: number; language?: string; filters?: any; timeout_ms?: number };
};
```

---

## 4. Zustand Store Design

### 4.1 Session Store

```typescript
// src/store/session.store.ts
import { create } from 'zustand';

type SessionState = {
  id: string | null;
  turn: number;
  set: (patch: Partial<SessionState>) => void;
  reset: () => void;
};

export const useSessionStore = create<SessionState>((set) => ({
  id: null,
  turn: 0,
  set: (patch) => set(patch),
  reset: () => set({ id: null, turn: 0 }),
}));
```

### 4.2 Assist Store

```typescript
// src/store/assist.store.ts
import { create } from 'zustand';

type AssistState = {
  loading: boolean;
  error: string | null;
  answer: AssistResponse['answer'] | null;
  citations: Citation[];
  selectedCitationId: number | null;
  timings: AssistResponse['timings'] | null;
  send: (query: string) => Promise<void>;
  selectCitation: (id: number) => void;
};

export const useAssistStore = create<AssistState>((set, get) => ({
  loading: false,
  error: null,
  answer: null,
  citations: [],
  selectedCitationId: null,
  timings: null,
  async send(query) {
    set({ loading: true, error: null });
    try {
      const resp = await assistApi(query);
      set({
        answer: resp.answer,
        citations: resp.citations,
        selectedCitationId: resp.citations[0]?.id ?? null,
        timings: resp.timings,
      });
    } catch (e: any) {
      set({ error: e.message ?? 'Request failed' });
    } finally {
      set({ loading: false });
    }
  },
  selectCitation(id) { set({ selectedCitationId: id }); },
}));
```

---

## 5. API Client (via Assera API)

```typescript
// src/libs/apiClient.ts
export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const base = process.env.NEXT_PUBLIC_API_BASE ?? '/api/v1';
  const token = typeof window !== 'undefined' ? localStorage.getItem('assera.token') : null;
  const headers = new Headers(init.headers);
  headers.set('Content-Type', 'application/json');
  if (token) headers.set('X-Assera-Token', token);
  headers.set('X-Request-Id', crypto.randomUUID());
  const res = await fetch(`${base}${path}`, { ...init, headers, cache: 'no-store' });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.message || `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const assistApi = (query: string) =>
  apiFetch<AssistResponse>('/assist/query', { method: 'POST', body: JSON.stringify({ query }) });
```

---

## 6. Key Components

### 6.1 QueryInput
- **Props:** `value`, `onChange`, `onSubmit`, `disabled`
- **Behavior:** Enter submit, Shift+Enter newline, `Cmd/Ctrl+K` focus with `useHotkeys`
- **Validation:** 1–4096 characters. Reject whitespace only

### 6.2 AnswerBubble
- **Input:** `answer.text` (multilingual). Do **not add** evidence references "[1][2]..." to UI (not included in text)
- **Decoration:** Badge indicating LLM-generated (icon display on fallback)

### 6.3 SuggestChips
- **Input:** `answer.suggested_questions[]`
- **Behavior:** Re-execute `send()` on click

### 6.4 EvidencePanel
- **Tabs:** `Selected` / `All` (accessibility: `role="tablist"`)
- **Selected:** Display details of `selectedCitationId` (display meta with `MetaTable`)
- **All:** `EvidenceItem` list (click to toggle selection)
- **Open in Fess:** `ExternalLink` with `rel="noopener" target="_blank"`. Only allowed hosts

### 6.5 LatencyIndicator
- **Input:** `timings.total_ms`
- **Thresholds:** `NEXT_PUBLIC_LATENCY_THRESHOLDS` (e.g., `<=500ms` good, `<=1500ms` normal, over slow)
- **Display:** Icon + tooltip (p95 target 2s)

---

## 7. UX & State Transitions

- **Loading:** Send input → `loading=true`. Input disabled, progress bar display
- **Success:** Receive `answer/citations` → display right pane → auto-select `selectedCitationId`
- **No Results:** `citations.length=0` → `EmptyState` with re-search suggestion/hints
- **Error:** `ErrorBanner` (retry button, details collapsible). Guide token setup on 401
- **Fallback:** If `notice.fallback=true`, auto-add "Please check evidence" to Answer (UI side)

---

## 8. i18n Design

- **Library:** `i18next` + `react-i18next`
- **Languages:** `ja` default, `en` included
- **Resources:** `public/locales/{ja,en}/common.json`
- **Switching:** Update `useUIStore.lang` with LangThemeSwitch, reflect in `<html lang>`
- **Date/Number:** `Intl.DateTimeFormat` / `Intl.RelativeTimeFormat`

---

## 9. Accessibility

- **Keyboard:** Tab navigation, Enter submit, Shift+Enter newline, EvidenceItem Enter/Space select
- **ARIA:** `role=tablist/tab/tabpanels`, `aria-selected`, `aria-busy`, `aria-live=polite`
- **Contrast:** AA or higher with Tailwind's `text-foreground` / `bg-muted`
- **Focus visible:** Uniform application of `focus:ring-2 focus:ring-ring`

---

## 10. Security (UI)

- Sanitize `snippet` display with **DOMPurify** (minimum allowed tags: `em,strong,a`)
- External links only to allowed domains (Open Redirect prevention)
- CSP (example): `default-src 'self'; connect-src 'self' https://api.example; frame-ancestors 'none'`
- If saving API token to localStorage, **user optional setting** and **use only when sending from UI**

---

## 11. Telemetry (UI)

- Events: `ui.send_query`, `ui.click_citation`, `ui.open_in_fess`, `ui.error`
- Send: `navigator.sendBeacon` / `fetch` (async, ignore failures)
- No PII. Hash URLs (first 12 characters)

---

**End of Document**
