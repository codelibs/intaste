# Intaste Streaming Responses (SSE)

**Document Version:** 1.0
**Last Updated:** 2025-10-12
**Target:** Intaste v0.1+

**Purpose:**
This document explains the Server-Sent Events (SSE) streaming implementation in Intaste, which enables real-time incremental display of LLM-generated answers.

---

## 1. Overview

Intaste supports two query modes:

1. **Standard Mode**: Wait for complete answer before display
2. **Streaming Mode**: Display answer text incrementally as it's generated

Streaming mode provides better user experience by showing progress in real-time, especially for longer answers.

---

## 2. Architecture

### 2.1 Backend (FastAPI)

```
Client Request
    ↓
POST /api/v1/assist/query/stream
    ↓
StreamingResponse (SSE)
    ↓
Event Flow:
    - start      → Query processing begins
    - intent     → Intent extraction complete
    - citations  → Search results ready
    - chunk      → Answer text chunk (multiple)
    - complete   → Processing complete
    - error      → Error occurred
```

### 2.2 Frontend (Next.js + React)

```
User Query
    ↓
streamingEnabled ? sendStream() : send()
    ↓
queryAssistStream()
    ↓
fetch() with text/event-stream
    ↓
ReadableStream parsing
    ↓
Event callbacks → State updates
    ↓
Incremental UI rendering
```

---

## 3. API Specification

### 3.1 Endpoint

```
POST /api/v1/assist/query/stream
```

### 3.2 Request

```json
{
  "query": "What is the security policy?",
  "session_id": "optional-session-id",
  "options": {
    "max_results": 10
  }
}
```

### 3.3 Response (SSE Format)

The response uses Server-Sent Events format:

```
event: <event_type>
data: <json_payload>

```

#### Event Types

**1. start**
```
event: start
data: {"message": "Processing query..."}

```

**2. intent**
```
event: intent
data: {
  "optimized_query": "security policy documentation",
  "keywords": ["security", "policy"],
  "fallback": false
}

```

**3. citations**
```
event: citations
data: {
  "citations": [
    {
      "id": 1,
      "title": "Security Policy",
      "url": "https://example.com/security",
      "content": "Policy content...",
      "score": 0.95
    }
  ]
}

```

**4. chunk** (multiple)
```
event: chunk
data: {"text": "Based on the security policy, "}

event: chunk
data: {"text": "we recommend following these steps: "}

event: chunk
data: {"text": "1. Enable two-factor authentication"}

```

**5. complete**
```
event: complete
data: {
  "answer": {
    "text": "Complete answer text...",
    "suggested_followups": [
      "How do I enable 2FA?",
      "What are the password requirements?"
    ]
  },
  "session": {
    "id": "session-123",
    "turn": 1
  },
  "timings": {
    "intent_ms": 245,
    "search_ms": 182,
    "compose_ms": 1543,
    "total_ms": 1970
  }
}

```

**6. error**
```
event: error
data: {
  "message": "LLM service unavailable",
  "code": "LLM_ERROR"
}

```

---

## 4. Implementation Details

### 4.1 Backend Implementation

#### Streaming Ollama Client

**File**: `intaste-api/app/core/llm/ollama.py`

Key method: `compose_stream()` - Yields text chunks from Ollama

- Enables Ollama streaming mode
- Parses NDJSON stream from Ollama API
- Yields text content incrementally
- Handles errors with fallback messages

#### Streaming Router

**File**: `intaste-api/app/routers/assist_stream.py`

Key features:
- SSE event formatting (`format_sse()`)
- Event sequence: start → intent → citations → chunks → complete
- Error handling with error events
- Proper SSE headers (no-cache, keep-alive, no buffering)

### 4.2 Frontend Implementation

#### Streaming Client

**File**: `intaste-ui/src/libs/streamingClient.ts`

Key features:
- Fetch API with text/event-stream
- ReadableStream processing
- SSE message parsing (event/data format)
- Callback invocation for each event type

#### Store Integration

**File**: `intaste-ui/src/store/assist.store.ts`

Key features:
- `sendStream()` method for streaming requests
- Incremental text accumulation
- State updates for each event
- Session and timing management

#### UI Toggle

**File**: `intaste-ui/app/page.tsx`

Key features:
- Streaming mode toggle
- Streaming indicator (⚡ Streaming...)
- Preference persistence in localStorage

---

## 5. Configuration

### 5.1 Environment Variables

**Backend** (`.env`):
```bash
# Ollama streaming support (requires Ollama 0.1.0+)
OLLAMA_BASE_URL=http://localhost:11434

# Timeout for streaming requests (ms)
INTASTE_LLM_TIMEOUT_MS=60000
```

**Frontend** (`.env.local`):
```bash
# API endpoint
NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1
```

### 5.2 UI Preferences

Streaming preference is stored in localStorage:
```typescript
// Key: intaste-ui-storage
{
  "streamingEnabled": true  // Default: true
}
```

---

## 6. Performance Considerations

### 6.1 Backend

1. **Buffering**: Disable nginx buffering with `X-Accel-Buffering: no` header
2. **Timeouts**: Use longer timeouts for streaming (default: 60s)
3. **Error Handling**: Always send error event on exceptions
4. **Chunking**: Yield small chunks (10-50 tokens) for smoother display

### 6.2 Frontend

1. **Parsing**: Use efficient buffer-based SSE parsing
2. **State Updates**: Batch state updates when possible
3. **Memory**: Release ReadableStream reader after completion
4. **Error Recovery**: Handle network errors gracefully

---

## 7. Testing

### 7.1 Backend Tests

- Unit tests: `tests/unit/test_ollama_stream.py`
- Integration tests: `tests/integration/test_streaming_endpoint.py`

### 7.2 Frontend Tests

- Unit tests: `tests/libs/streamingClient.test.ts`
- Store tests: `tests/stores/assist.store.test.ts`
- E2E tests: `e2e/streaming.spec.ts`

---

## 8. Troubleshooting

### Issue: Streaming doesn't start

**Symptoms**: Loading indicator appears but no text streams

**Solutions**:
1. Check API token is set
2. Verify Ollama is running and accessible
3. Check browser console for network errors
4. Verify streaming endpoint is registered in FastAPI

### Issue: Incomplete streaming

**Symptoms**: Streaming starts but stops mid-answer

**Solutions**:
1. Check Ollama timeout settings
2. Verify network stability
3. Check for nginx buffering issues
4. Review backend logs for errors

### Issue: Chunky/delayed streaming

**Symptoms**: Text appears in large chunks, not smoothly

**Solutions**:
1. Reduce chunk size in Ollama client
2. Disable proxy buffering
3. Check network latency
4. Optimize state update batching

### Issue: Unicode characters broken

**Symptoms**: Emoji or non-ASCII characters appear incorrectly

**Solutions**:
1. Verify UTF-8 encoding in SSE response
2. Use TextDecoder with proper encoding
3. Check Content-Type includes charset=utf-8

---

## 9. Best Practices

1. **Always provide fallback**: Support both streaming and standard modes
2. **Handle errors gracefully**: Send error events, don't just disconnect
3. **Show progress indicators**: Display "Streaming..." during active streaming
4. **Support cancellation**: Allow users to stop long-running streams
5. **Test edge cases**: Empty responses, network errors, malformed data
6. **Monitor performance**: Track streaming latency and chunk rates

---

## 10. References

- [Server-Sent Events Spec](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [Ollama API Documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [FastAPI StreamingResponse](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
- [Fetch API - Streams](https://developer.mozilla.org/en-US/docs/Web/API/Streams_API)

---

**End of Document**
