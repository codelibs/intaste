# Assera Process Flow Design

**Document Version:** 1.0
**Last Updated:** 2025-10-12

## Architecture Overview

Assera is an AI-assisted search system that understands natural language search queries and provides appropriate search results and answers.

### Main Components

- **Assera UI**: Next.js/React-based frontend, real-time updates via Server-Sent Events (SSE)
- **Assera API**: FastAPI-based backend, integrating LLM and Fess search
- **LLM Client**: Interface with LLM providers like Ollama
- **Search Provider**: Interface with Fess search engine

---

## Assera UI

### Search Query Processing Flow

#### 1. User Input
- User enters search term or natural language query in the input field
- QueryInput component receives the text

#### 2. API Request Submission
- Calls `sendStream()` method from `assist.store.ts`
- If Session ID exists, send as conversation context
- POST request to `/api/v1/assist/query/stream` endpoint

#### 3. Processing Streaming Response
`streamingClient.ts` receives Server-Sent Events (SSE) for real-time updates:

| Event | Timing | UI Update |
|---------|----------|-----------|
| `start` | Processing begins | Display loading state |
| `intent` | Intent extraction complete | Display normalized query (optional) |
| `citations` | Search complete | Display search results in EvidencePanel |
| `chunk` | Answer generation in progress | Incrementally add text to AnswerBubble |
| `complete` | Processing complete | Display final answer and suggested questions, update Session info |
| `error` | Error occurs | Display error message in ErrorBanner |

#### 4. Result Display
- **AnswerBubble**: AI-generated answer text and suggested questions
- **EvidencePanel**: Search result citations (title, snippet, URL, score)
- **LatencyIndicator**: Display processing time (Intent, Search, Compose, Total)

#### 5. Session Management
- Manage Session ID and turn count in `session.store.ts`
- Available as conversation history for next query (planned for API implementation)

---

## Assera API

### Search Query Processing Flow

Assera API processes search queries through a 3-stage pipeline:

#### Overall Flow (Streaming Mode)

```
User Query
  ↓
[1] Intent Extraction (LLM)
  ↓ (event: intent)
[2] Search Execution (Fess)
  ↓ (event: citations)
[3] Answer Composition (LLM, streaming)
  ↓ (event: chunk × N)
Final Response (event: complete)
```

---

### Phase 1: Intent Extraction

**Responsibility**: Optimize user's natural language query for search engine using LLM

**Processing**:
1. Receive query (consider conversation history if Session info included, future)
2. Call `LLMClient.intent()` (`app/core/llm/ollama.py`, etc.)
3. LLM generates:
   - **normalized_query**: Query optimized for search engine
   - **filters**: Recommended search filters (site, file type, etc.)
   - **followups**: Suggested questions for user (up to 3)
   - **ambiguity**: Query ambiguity level (low/medium/high)

**Timeout**: `settings.intent_timeout_ms` (default configuration)

**Error Handling**:
- On timeout or LLM failure, use original query as-is (fallback)
- Set `Notice` flag to notify UI of LLM failure

**Streaming Output**:
```json
event: intent
data: {
  "normalized_query": "optimized query",
  "filters": {"site": "example.com"},
  "timing_ms": 500
}
```

---

### Phase 2: Search Execution

**Responsibility**: Execute search in Fess search engine and retrieve related documents

**Processing**:
1. Build `SearchQuery` using Phase 1's `normalized_query` and `filters`
2. Call `SearchProvider.search()` (`app/core/search_provider/fess.py`)
3. Execute search via Fess OpenAPI:
   - Parameter conversion (page/size → start/num)
   - Sort settings (relevance, date ascending/descending)
   - Filter application (site, mimetype, updated_after, etc.)
4. Normalize search results:
   - Convert each document to `SearchHit` object
   - Extract title, URL, snippet, score, metadata

**Timeout**: `settings.search_timeout_ms`

**Error Handling**:
- Search is essential, so fail entire request on error
- Properly propagate timeout or HTTP errors

**Streaming Output**:
```json
event: citations
data: {
  "count": 5,
  "citations": [
    {
      "id": "1",
      "title": "Document Title",
      "snippet": "Text matching search...",
      "url": "https://example.com/doc",
      "score": 0.95,
      "metadata": {"site": "example.com", "content_type": "text/html"}
    }
  ],
  "timing_ms": 150
}
```

---

### Phase 3: Answer Composition

**Responsibility**: Generate concise answer based on search results using LLM

**Processing**:
1. Execute only if search results exist
2. Call `LLMClient.compose_stream()` (streaming mode)
3. Pass to LLM:
   - Original query and normalized query
   - Citation data from search results (title, snippet, URL)
   - Follow-up questions generated in Phase 1
4. Return LLM-generated answer text via streaming (max 300 characters)

**Timeout**: `settings.compose_timeout_ms`

**Error Handling**:
- On timeout or LLM failure, return generic guidance message
  - Example: "Results are displayed. Please review the sources for details."
- Set `Notice` flag

**If Search Results are 0**:
- Skip answer generation
- Return "No results found. Try different keywords or check spelling."

**Streaming Output**:
```json
event: chunk
data: {"text": "Based on search results"}

event: chunk
data: {"text": ", this document contains"}

event: chunk
data: {"text": "..."}
```

**Completion Event**:
```json
event: complete
data: {
  "answer": {
    "text": "Complete answer text",
    "suggested_followups": ["Suggested question 1", "Suggested question 2"]
  },
  "citations": [...],
  "timings": {
    "intent_ms": 500,
    "search_ms": 150,
    "compose_ms": 800,
    "total_ms": 1450
  }
}
```

---

## Session Management

**Current Implementation**:
- `AssistService` maintains Session information in memory
- Tracks Session ID and turn count
- Records history of each query (query, normalized query, citation count)

**Future Extensions**:
- Persistence using Redis/database
- Passing conversation history context to LLM
- Improved intent understanding in multi-turn conversations

---

## Future Extension Points

### 1. Iterative Search

**Purpose**: Automatically retry search if search results are insufficient

**Implementation Plan**:
1. Evaluate search results after Phase 2
2. Re-search if:
   - 0 search results
   - Search result scores below threshold
   - Low relevance evaluation by LLM
3. Modify query and retry up to 2-3 times
4. Notify each attempt as streaming event

### 2. Contextual Search (Using Conversation History)

**Purpose**: Improve search accuracy using previous search context

**Implementation Plan**:
1. Pass Session history to LLM Intent phase
2. Expand query considering previous query and answer
3. Inherit and adjust filters

### 3. Re-ranking of Search Results

**Purpose**: Evaluate relevance of search results using LLM and reorder

**Implementation Plan**:
1. Add re-ranking phase between Phase 2 and Phase 3
2. LLM calculates relevance score with query
3. Reorder citations based on score

### 4. Multimodal Support

**Purpose**: Search and display non-text content like images, PDFs

**Implementation Plan**:
1. Include content type in Fess search results
2. Implement image preview, PDF viewer in UI
3. Generate image descriptions if LLM supports multimodal

---

## Performance Optimization

### Timeout Configuration

Each phase timeout set in `app/core/config.py`:

```python
intent_timeout_ms: int = 5000    # Intent extraction
search_timeout_ms: int = 3000    # Fess search
compose_timeout_ms: int = 10000  # Answer generation
```

### Parallel Processing Possibilities

Currently sequential processing, but consider for future:
- Parallel execution of intent extraction and initial search (start search with original query)
- Parallel execution of multiple search strategies (different query transformations)

---

## Error Handling Strategy

| Error Type | Phase | Response |
|-----------|-------|---------|
| Intent LLM timeout | 1 | Continue with original query, set Notice flag |
| Intent LLM failure | 1 | Continue with original query, set Notice flag |
| Search timeout | 2 | Return error response (essential processing) |
| Search connection error | 2 | Return error response (essential processing) |
| Compose LLM timeout | 3 | Return generic message, set Notice flag |
| Compose LLM failure | 3 | Return generic message, set Notice flag |

---

## Summary

Assera's search processing flow combines LLM-based intent understanding and answer generation with Fess fast search and SSE real-time updates for a user-friendly design. Future enhancements like re-search, conversation history utilization, and re-ranking will provide even more advanced search experiences.
