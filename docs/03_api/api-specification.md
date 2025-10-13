# Assera API Specification

**Document Version:** 1.0
**Last Updated:** 2025-10-12
**API Base URL:** `/api/v1`
**Authentication:** API Key (Header: X-Assera-Token)
**Dependencies:** Fess Search OpenAPI (Assera uses Fess REST only. No OpenSearch connection)

---

## 0. Design Policy

- Assera follows "guidance over summary" as a basic policy, keeping generated text short and emphasizing evidence (citations) presentation and drill-down.
- LLM uses Ollama (default: `gpt-oss`) with limited use for search intent extraction, suggested question generation, and concise explanations.
- Search calls Fess REST API (OpenAPI) via Search Provider abstraction.
- UI→API requires API Key authentication. Initial version uses single role with no authorization.

---

## 1. Security

### 1.1 Authentication
- **Header:** `X-Assera-Token: <api-key>`
- **401 (Unauthorized) conditions:**
  - Header missing
  - Invalid token
- **403 (Forbidden) conditions:**
  - For future role control (not used in initial version)

### 1.2 CORS
- By default, only assera-ui origin allowed. Expandable via environment variables.

### 1.3 Rate Control (Recommended Implementation)
- **Soft limit:** 60 req/min/key (initial recommended value)
- **On excess:** 429 Too Many Requests + Retry-After header

---

## 2. Resource List

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/assist/query` | Receive natural language query, extract intent with LLM → Fess search → return answer + evidence + suggestions |
| POST | `/assist/feedback` | Record user evaluation of answer/evidence |
| GET | `/models` | List available models (enumerate from Ollama) |
| POST | `/models/select` | Switch default or session-scoped model |
| GET | `/health` | Health check (can be unauthenticated) |

Appendix: Future extensions like GET `/sessions/:id`, etc. (out of initial scope)

---

## 3. Data Models

### 3.1 Common Types

```typescript
// IDs
Guid: string // UUID v4 recommended

// Timings
Timings: {
  "llm_ms": number,
  "search_ms": number,
  "total_ms": number
}

// Citation (evidence)
Citation: {
  "id": number,                 // Reference number in response (1..n)
  "title": string,              // Title from Fess search hit
  "snippet": string,            // Excerpt (can be highlighted)
  "url": string,                // Link via Fess
  "score": number,              // Search score (Fess normalized value)
  "meta"?: {                    // Optional meta
    "updated_at"?: string,      // ISO8601
    "author"?: string,
    "path"?: string,
    "content_type"?: string
  }
}

// Answer (brief explanation + evidence guidance + suggestions)
Answer: {
  "text": string,                    // Concise explanation (generated)
  "suggested_questions": string[]    // Drill-down candidates (generated)
}
```

### 3.2 `/assist/query` I/O

**Request**
```json
{
  "query": "Tell me about the latest security policy",
  "session_id": "3f3a3f49-0e0b-44a1-ae05-8c1b2e4a2c43", // optional
  "options": {
    "max_results": 10,
    "language": "en",
    "filters": { "department": "Security" },
    "timeout_ms": 5000
  }
}
```

**Response**
```json
{
  "answer": {
    "text": "Latest version is July 2024 revision [1][2]. Compare revision points?",
    "suggested_questions": [
      "What's the summary of revisions?",
      "What's the difference from old version?",
      "Who's the approver?"
    ]
  },
  "citations": [
    {
      "id": 1,
      "title": "security_policy_v2024_07.pdf",
      "snippet": "…This policy was revised in July 2024…",
      "url": "https://fess.example.local/doc/abc123",
      "score": 12.3,
      "meta": { "updated_at": "2024-07-10T09:00:00Z", "content_type": "application/pdf" }
    },
    {
      "id": 2,
      "title": "security_guideline_v2023_12.docx",
      "snippet": "…guideline…",
      "url": "https://fess.example.local/doc/def456",
      "score": 10.1
    }
  ],
  "session": { "id": "3f3a3f49-0e0b-44a1-ae05-8c1b2e4a2c43", "turn": 2 },
  "timings": { "llm_ms": 210, "search_ms": 180, "total_ms": 480 }
}
```

### 3.3 `/assist/feedback` I/O

**Request**
```json
{
  "session_id": "3f3a3f49-0e0b-44a1-ae05-8c1b2e4a2c43",
  "turn": 2,
  "rating": "up",                // "up" | "down"
  "comment": "Evidence 1 was accurate. Revision date was helpful."
}
```

**Response**
```json
{ "status": "ok" }
```

### 3.4 `/models` (GET)

**Response**
```json
{
  "default": "gpt-oss",
  "available": ["gpt-oss", "mistral", "llama3"],
  "selected_per_session": {
    "3f3a3f49-0e0b-44a1-ae05-8c1b2e4a2c43": "mistral"
  }
}
```

### 3.5 `/models/select` (POST)

**Request**
```json
{
  "model": "mistral",
  "scope": "session",            // "default" | "session"
  "session_id": "3f3a3f49-0e0b-44a1-ae05-8c1b2e4a2c43"
}
```

**Response**
```json
{ "status": "ok" }
```

### 3.6 `/health` (GET)
- **200:** `{ "status": "ok", "version": "0.1.0" }`

---

## 4. Exception/Error Specifications

### 4.1 Common Error Response Format

```json
{
  "error": {
    "code": "AUTH_INVALID_TOKEN",   // Machine-readable code
    "message": "invalid API token",  // Human-readable
    "details": { "hint": "check X-Assera-Token" },
    "request_id": "a1b2c3d4"
  }
}
```

### 4.2 Representative HTTP Status and Codes

| HTTP | code | Representative Cause |
|------|------|---------------------|
| 400 | BAD_REQUEST | Invalid parameters, JSON schema mismatch |
| 401 | AUTH_INVALID_TOKEN | Authentication header missing/invalid |
| 403 | FORBIDDEN | For future role control (not used in initial version) |
| 408 | TIMEOUT | Timeout due to Fess / LLM response delay |
| 409 | CONFLICT | Conflict in models/select, etc. |
| 413 | PAYLOAD_TOO_LARGE | Input exceeds threshold |
| 429 | RATE_LIMITED | Rate limit exceeded |
| 500 | INTERNAL_ERROR | Unexpected server error |
| 502 | UPSTREAM_FESS_ERROR | Fess side error forwarding |
| 503 | LLM_UNAVAILABLE | Ollama down/overloaded |

### 4.3 Retry Policy
- **429/503:** Retry according to Retry-After header
- **502:** Max 3 retries with exponential backoff

---

## 5. Internal Algorithm (Overview)

### 5.1 `/assist/query` Processing Stages

1. **Auth:** Verify `X-Assera-Token`
2. **Intent Extraction:** LLM prompt
   - Output: `normalized_query`, `filters`, `followup_candidates`
3. **Search:** Execute `normalized_query` with SearchProvider (Fess)
4. **Format:** Build `citations[]` from hits
5. **Response Generation:** Brief explanation with LLM and `suggested_questions[]`
6. **Response:** `answer` + `citations` + `session` + `timings`

### 5.2 LLM Prompt Policy (Template)

- **Intent extraction** (output JSON only)
  - Input: `query`
  - Output example:
    ```json
    {
      "normalized_query": "security policy revision date latest",
      "filters": {"language": "en"},
      "followups": ["What's the summary of revisions?", "What's the difference from old version?"]
    }
    ```

- **Explanation generation** (guide to evidence without exaggeration)

---

## 6. Implementation Notes (FastAPI)

- **Authentication dependency:** Verify `X-Assera-Token` with `Depends(api_key_auth)`
- **Schema:** Define above JSON schema with pydantic v2 (BaseModel)
- **HTTP client:** Call Fess / Ollama with `httpx.AsyncClient`
- **Timeout:** Distribute `timeout_ms` within API (e.g., 60% LLM, 40% Fess)
- **Logging:** Pass `request_id` with `X-Request-Id` (generate if absent), return on error

---

## 7. Testing Perspectives

- **`/assist/query` normal system:** Japanese query, both 0 and multiple citations cases
- **Exception system:** Reproduce 401/408/429/502/503 with mock
- **Model switching:** `/models` → `/models/select` → reflected in `/assist/query`

---

## 8. Appendix

- **Fess OpenAPI Schema (User Search API):**
  `https://raw.githubusercontent.com/codelibs/fess/refs/heads/master/src/main/config/openapi/openapi-user.yaml`
- **Assera** does not directly access OpenSearch (design constraint)

---

**End of Document**
