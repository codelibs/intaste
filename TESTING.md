# Intaste Testing Guide

This document provides comprehensive information about testing the Intaste application.

## Overview

Intaste uses a multi-layer testing strategy:

1. **Unit Tests** - Test individual components in isolation
2. **Integration Tests** - Test API endpoints with mocked dependencies
3. **E2E Tests** - Test complete user flows across the entire stack

## Test Technology Stack

### Backend (intaste-api)
- **pytest** - Test framework
- **pytest-cov** - Code coverage
- **pytest-asyncio** - Async test support
- **httpx** - HTTP client for testing

### Frontend (intaste-ui)
- **vitest** - Unit test framework
- **@testing-library/react** - Component testing
- **@playwright/test** - E2E testing
- **jsdom** - DOM simulation

## Running Tests

### API Tests

```bash
# From repository root
cd intaste-api

# Install dependencies including dev dependencies
uv pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term

# Run specific test file
pytest tests/unit/test_ollama_client.py

# Run tests matching pattern
pytest -k "test_intent"

# Run with verbose output
pytest -v

# Run unit tests only
pytest tests/unit/ -m unit

# Run integration tests only
pytest tests/integration/ -m integration
```

### UI Unit Tests

```bash
# From intaste-ui directory
cd intaste-ui

# Install dependencies
npm install

# Run all tests
npm test

# Run with UI
npm run test:ui

# Run with coverage
npm run test:coverage

# Run specific test file
npm test -- tests/components/QueryInput.test.tsx

# Watch mode (runs tests on file changes)
npm test -- --watch
```

### E2E Tests

```bash
# From intaste-ui directory
cd intaste-ui

# Install Playwright browsers (first time only)
npx playwright install

# Run E2E tests
npm run test:e2e

# Run with UI mode
npm run test:e2e:ui

# Run in debug mode
npm run test:e2e:debug

# Run specific test file
npx playwright test e2e/search-flow.spec.ts

# Run on specific browser
npx playwright test --project=chromium
```

## Test Structure

### API Test Structure

```
intaste-api/tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Unit tests
│   ├── test_ollama_client.py
│   ├── test_fess_provider.py
│   └── test_assist_service.py
└── integration/             # Integration tests
    └── test_api_endpoints.py
```

### UI Test Structure

```
intaste-ui/
├── tests/
│   ├── setup.ts             # Test setup and globals
│   ├── utils/
│   │   └── test-utils.tsx   # Test utilities and helpers
│   ├── components/          # Component tests
│   │   ├── QueryInput.test.tsx
│   │   ├── AnswerBubble.test.tsx
│   │   └── EvidenceItem.test.tsx
│   ├── libs/                # Library tests
│   │   └── streamingClient.test.ts
│   └── stores/              # Store tests
│       ├── assist.store.test.ts
│       ├── ui.store.test.ts
│       └── session.store.test.ts
└── e2e/                     # E2E tests
    ├── search-flow.spec.ts
    ├── citation-interaction.spec.ts
    ├── accessibility.spec.ts
    └── streaming.spec.ts
```

## Streaming Tests

Intaste includes comprehensive tests for Server-Sent Events (SSE) streaming functionality:

### API Streaming Tests

**Unit Tests** (`tests/unit/test_ollama_stream.py`):
- Tests streaming text generation from Ollama
- Validates NDJSON parsing and chunk accumulation
- Tests error handling, timeouts, and Unicode support
- Tests empty chunks, malformed JSON, and HTTP errors

**Integration Tests** (`tests/integration/test_streaming_endpoint.py`):
- Tests `/api/v1/assist/query/stream` endpoint
- Validates SSE event format (start, intent, citations, chunk, complete, error)
- Tests authentication, authorization, and session management
- Tests fallback strategies and error propagation

Example API streaming test:
```python
@pytest.mark.asyncio
async def test_compose_stream_success(ollama_client, httpx_mock):
    """Test successful streaming composition."""
    stream_data = [
        {"message": {"content": "Hello "}, "done": False},
        {"message": {"content": "world"}, "done": False},
        {"done": True},
    ]

    ndjson_content = "\n".join(json.dumps(item) for item in stream_data)
    httpx_mock.add_response(
        url="http://localhost:11434/api/chat",
        method="POST",
        status_code=200,
        content=ndjson_content.encode("utf-8"),
    )

    chunks = []
    async for chunk in ollama_client.compose_stream(
        query="test", normalized_query="test", citations_data=[]
    ):
        chunks.append(chunk)

    assert chunks == ["Hello ", "world"]
```

### UI Streaming Tests

**Unit Tests** (`tests/libs/streamingClient.test.ts`):
- Tests SSE client with fetch API and ReadableStream
- Validates event parsing and callback invocation
- Tests partial messages across chunks
- Tests error handling and network failures

**Store Tests** (`tests/stores/assist.store.test.ts`):
- Tests streaming state management
- Validates incremental text accumulation
- Tests citation updates during streaming
- Tests error handling and state cleanup

Example UI streaming test:
```typescript
it('accumulates text chunks during streaming', async () => {
  const sseData =
    'event: chunk\ndata: {"text":"Hello "}\n\n' +
    'event: chunk\ndata: {"text":"world"}\n\n' +
    'event: complete\ndata: {"answer":{"text":"Hello world"},"session":{}}\n\n';

  const mockReadableStream = {
    getReader: () => ({
      read: vi.fn()
        .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode(sseData) })
        .mockResolvedValueOnce({ done: true }),
      releaseLock: vi.fn(),
    }),
  };

  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    body: mockReadableStream,
  });

  await useAssistStore.getState().sendStream('test query');

  const state = useAssistStore.getState();
  expect(state.answer?.text).toBe('Hello world');
  expect(state.streaming).toBe(false);
});
```

**E2E Tests** (`e2e/streaming.spec.ts`):
- Tests streaming toggle UI
- Tests incremental text display
- Tests streaming with citations
- Tests error handling and recovery
- Tests streaming vs standard mode switching
- Tests preference persistence

Example E2E streaming test:
```typescript
test('should display text incrementally during streaming', async ({ page }) => {
  await page.goto('/');

  await page.route('**/api/v1/assist/query/stream', async (route) => {
    const chunks = [
      'event: chunk\ndata: {"text":"First "}\n\n',
      'event: chunk\ndata: {"text":"second "}\n\n',
      'event: chunk\ndata: {"text":"third"}\n\n',
      'event: complete\ndata: {"answer":{"text":"First second third"}}\n\n',
    ];

    await route.fulfill({
      status: 200,
      contentType: 'text/event-stream',
      body: chunks.join(''),
    });
  });

  const input = page.locator('textarea[placeholder*="question"]');
  await input.fill('test question');
  await input.press('Enter');

  const answer = page.locator('[data-testid="answer-bubble"]').first();
  await expect(answer).toContainText('First second third', { timeout: 5000 });
});
```

### Running Streaming Tests

```bash
# API streaming tests
cd intaste-api
pytest tests/unit/test_ollama_stream.py -v
pytest tests/integration/test_streaming_endpoint.py -v

# UI streaming tests
cd intaste-ui
npm test -- tests/libs/streamingClient.test.ts
npm test -- tests/stores/assist.store.test.ts -t Streaming

# E2E streaming tests
npm run test:e2e -- e2e/streaming.spec.ts
```

## Writing Tests

### API Unit Test Example

```python
# intaste-api/tests/unit/test_example.py
import pytest
from app.core.llm.ollama import OllamaClient

@pytest.mark.unit
@pytest.mark.asyncio
async def test_intent_extraction(ollama_client):
    """Test successful intent extraction"""
    result = await ollama_client.intent("What is the security policy?")

    assert result.optimized_query is not None
    assert len(result.intent_tags) > 0
    assert result.confidence > 0.0
```

### UI Component Test Example

```typescript
// intaste-ui/tests/components/Example.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { renderWithProviders, screen } from '../utils/test-utils';
import userEvent from '@testing-library/user-event';
import QueryInput from '@/components/input/QueryInput';

describe('QueryInput', () => {
  it('calls onSubmit when Enter is pressed', async () => {
    const handleSubmit = vi.fn();
    const user = userEvent.setup();

    renderWithProviders(
      <QueryInput value="test" onChange={() => {}} onSubmit={handleSubmit} />
    );

    const textarea = screen.getByPlaceholderText(/ask a question/i);
    await user.click(textarea);
    await user.keyboard('{Enter}');

    expect(handleSubmit).toHaveBeenCalled();
  });
});
```

### E2E Test Example

```typescript
// intaste-ui/e2e/example.spec.ts
import { test, expect } from '@playwright/test';

test('should submit query and display results', async ({ page }) => {
  await page.goto('/');

  // Enter query
  const input = page.getByPlaceholder(/ask a question/i);
  await input.fill('What is the security policy?');
  await input.press('Enter');

  // Verify results
  await expect(page.getByText(/answer/i)).toBeVisible();
});
```

## Test Fixtures and Utilities

### API Fixtures (conftest.py)

- `test_settings` - Test configuration
- `mock_search_provider` - Mocked search provider
- `mock_llm_client` - Mocked LLM client
- `client` - FastAPI test client
- `async_client` - Async HTTP client
- `auth_headers` - Authentication headers

### UI Test Utilities

- `renderWithProviders()` - Render components with required providers
- `mockApiResponse()` - Create mock API responses
- `createMockCitation()` - Generate mock citation data
- `createMockAnswer()` - Generate mock answer data
- `createMockQueryResponse()` - Full query response

## Mocking Strategies

### API Mocking

```python
# Mock search provider
from unittest.mock import AsyncMock

mock_provider = AsyncMock()
mock_provider.search.return_value = SearchResult(
    hits=[...],
    total=2,
    took_ms=150,
)
```

### UI API Mocking

```typescript
// Mock fetch
global.fetch = vi.fn().mockResolvedValue({
  ok: true,
  status: 200,
  json: async () => mockResponse,
});
```

### Playwright Route Mocking

```typescript
await page.route('**/api/v1/assist/query', async (route) => {
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(mockResponse),
  });
});
```

## Coverage Reports

### API Coverage

After running `pytest --cov`, view HTML report:
```bash
cd intaste-api
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### UI Coverage

After running `npm run test:coverage`, view report:
```bash
cd intaste-ui
open coverage/index.html  # macOS
xdg-open coverage/index.html  # Linux
```

## Continuous Integration

### Running All Tests

From repository root:

```bash
# API tests
cd intaste-api
pytest

# UI unit tests
cd ../intaste-ui
npm test -- --run

# UI E2E tests
npm run test:e2e
```

### CI Configuration Example (GitHub Actions)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  api-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: |
          cd intaste-api
          pip install uv
          uv pip install -e ".[dev]"
      - name: Run tests
        run: |
          cd intaste-api
          pytest --cov --cov-report=xml

  ui-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install dependencies
        run: |
          cd intaste-ui
          npm ci
      - name: Run unit tests
        run: |
          cd intaste-ui
          npm test -- --run --coverage
      - name: Run E2E tests
        run: |
          cd intaste-ui
          npx playwright install --with-deps
          npm run test:e2e
```

## Test Best Practices

### General

1. **Test behavior, not implementation**
2. **Use descriptive test names**
3. **Follow AAA pattern** (Arrange, Act, Assert)
4. **Keep tests independent**
5. **Mock external dependencies**
6. **Test edge cases and error handling**

### API Tests

1. **Use pytest markers** (`@pytest.mark.unit`, `@pytest.mark.integration`)
2. **Test async functions** with `@pytest.mark.asyncio`
3. **Mock external services** (Fess, Ollama)
4. **Test fallback strategies**
5. **Verify timeout handling**

### UI Tests

1. **Query by accessibility** (roles, labels) not implementation details
2. **Test user interactions** not state changes
3. **Use userEvent** for realistic interactions
4. **Wait for async updates** with `waitFor`
5. **Test accessibility** features

### E2E Tests

1. **Test critical user flows** only
2. **Mock external APIs** to avoid flakiness
3. **Use page object pattern** for complex flows
4. **Test on multiple browsers**
5. **Include mobile viewports**

## Debugging Tests

### API Test Debugging

```bash
# Run with print statements
pytest -s

# Run with debugger
pytest --pdb

# Stop at first failure
pytest -x
```

### UI Test Debugging

```bash
# Run with browser UI
npm run test:ui

# Debug specific test
npm test -- tests/components/QueryInput.test.tsx --debug

# Playwright debug
npm run test:e2e:debug
```

## Performance Testing

### Load Testing API

```bash
# Using Apache Bench
ab -n 1000 -c 10 -H "X-Intaste-Token: $TOKEN" \
   -p query.json -T application/json \
   http://localhost:8000/api/v1/assist/query

# Using k6
k6 run load-test.js
```

### UI Performance

```bash
# Lighthouse CI
npm run lighthouse

# Bundle analysis
npm run build
npm run analyze
```

## Troubleshooting

### Common Issues

**API tests fail with import errors**
```bash
# Ensure you're in the right directory and installed dev dependencies
cd intaste-api
uv pip install -e ".[dev]"
```

**UI tests fail with module not found**
```bash
# Clear node_modules and reinstall
rm -rf node_modules
npm install
```

**Playwright browsers not installed**
```bash
npx playwright install
```

**E2E tests timeout**
- Increase timeout in playwright.config.ts
- Check if dev server is running
- Verify API is accessible

## Coverage Goals

- **API**: Target 80%+ coverage
- **UI Components**: Target 80%+ coverage
- **UI Stores**: Target 90%+ coverage
- **E2E**: Cover all critical user paths

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [vitest Documentation](https://vitest.dev/)
- [Testing Library](https://testing-library.com/)
- [Playwright Documentation](https://playwright.dev/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

---

**Last Updated**: October 2025
