# Assera Logging & Audit Design

**Document Version:** 1.0
**Last Updated:** 2025-10-12
**Target:** Assera OSS Initial Version (UI: Next.js / API: FastAPI / LLM: Ollama / Search: Fess OpenAPI)

**Purpose:** Define specifications for structured logs, distributed traces, metrics, and audit logs aimed at **production-grade observability**.

**Principles:**
- **Minimal collection, PII minimization** (aligned with Security Design v1.0)
- **Record as JSON to standard output** (container operation premise)
- **End-to-end correlation with X-Request-Id**
- **Failure observability** (visualization of thresholds, retries, fallbacks)

---

## 1. Component-Specific Log Policy

| Component | Log Medium | Format | Purpose |
|--------------------|--------|------|----------------------------------|
| assera-ui (Next.js) | stdout | JSON | Main UI events (send, click, error). Do not send PII |
| assera-api (FastAPI) | stdout | JSON | API receive/send, Fess/Ollama calls, exceptions, performance |
| fess | stdout | default | Reference (Assera side generally does not aggregate) |
| opensearch | stdout | default | Reference |
| ollama | stdout | default | Reference |

**Aggregation destination (future):** Designed to be forwardable to Loki / OpenSearch / Cloud Logging, etc.

---

## 2. Common Log Schema (JSON)

Required keys (common across all layers):

```json
{
  "ts": "2025-10-09T12:34:56.789Z",   // ISO8601 with ms
  "level": "INFO",                      // TRACE|DEBUG|INFO|WARN|ERROR
  "service": "assera-api",             // assera-ui|assera-api|...
  "component": "assist",               // optional: http|assist|llm|search|auth|ui
  "event": "assist.query",             // audit event name (see below)
  "request_id": "b2f7...",             // X-Request-Id (generate if none)
  "session_id": "3f3a...",             // optional (only if exists)
  "msg": "...",                        // brief explanation (Japanese possible)
  "attrs": { /* event-specific attributes */ }
}
```

**Prohibitions/Restrictions:**
- Do **not record** PII (name/email/phone/employee ID, etc.)
- Convert sensitive URL or path to **SHA-256 hash** (`url_sha256`)
- Do not output `api_token` in logs (use `api_token_sha256` if necessary)

---

## 3. Audit Events & Classification (event values)

### 3.1 Authentication/Rate Control

- `auth.success` / `auth.failure`
  `attrs`: `{ source_ip, user_agent_hash }`
- `ratelimit.blocked`
  `attrs`: `{ key_hash, limit, window_sec }`

### 3.2 Assisted Search (/assist/query)

- `assist.query` (received)
  `attrs`: `{ query_len, options:{max_results,timeout_ms}, model, provider }`
- `assist.success` (response)
  `attrs`: `{ citations_count, timings:{llm_ms,search_ms,total_ms} }`
- `assist.fallback` (fallback triggered)
  `attrs`: `{ reason:"LLM_TIMEOUT|BAD_LLM_OUTPUT|LLM_UNAVAILABLE", step:"intent|compose" }`
- `assist.error` (failure)
  `attrs`: `{ code, http_status }`

### 3.3 Search (Fess Call)

- `search.request`
  `attrs`: `{ q_len, page, size, sort, lang }`
- `search.response`
  `attrs`: `{ total, hits, took_ms }`
- `search.error`
  `attrs`: `{ http_status, fess_code }`

### 3.4 LLM (Ollama Call)

- `llm.intent.request` / `llm.intent.response`
  `attrs`: `{ model, timeout_ms, tokens_out? }`
- `llm.compose.request` / `llm.compose.response`
- `llm.error`
  `attrs`: `{ stage:"intent|compose", error:"timeout|unavailable|parse" }`

### 3.5 UI Events

- `ui.send_query`
  `attrs`: `{ query_len }`
- `ui.click_citation`
  `attrs`: `{ id, url_sha256, title_hash }`
- `ui.open_in_fess`
  `attrs`: `{ url_sha256 }`
- `ui.error`
  `attrs`: `{ code }`

---

## 4. Sample Logs

### 4.1 /assist/query Success

```json
{
  "ts":"2025-10-09T12:00:01.123Z",
  "level":"INFO",
  "service":"assera-api",
  "component":"assist",
  "event":"assist.success",
  "request_id":"8c2f...",
  "session_id":"3f3a...",
  "msg":"assist ok",
  "attrs":{
    "citations_count":3,
    "timings":{"llm_ms":210,"search_ms":180,"total_ms":480}
  }
}
```

### 4.2 Fallback (LLM Timeout)

```json
{
  "ts":"2025-10-09T12:00:01.000Z",
  "level":"WARN",
  "service":"assera-api",
  "component":"llm",
  "event":"assist.fallback",
  "request_id":"8c2f...",
  "msg":"llm timeout; used raw query",
  "attrs":{"reason":"LLM_TIMEOUT","step":"intent"}
}
```

---

## 5. Distributed Tracing (OpenTelemetry)

**Implementation Policy:**
- Trace provider: OpenTelemetry SDK (OTLP Exporter is optional)
- Tracing **enabled/disabled via environment variable** (initially disabled)
- Inherit HTTP headers (W3C Trace Context) within UI→API

**Main Spans:**
```
assist.query (server)
├─ llm.intent (client)
├─ search.fess (client)
└─ llm.compose (client)
```

**Span Attributes (Example):**
- `assist.query`: `query_len`, `citations_count`, `total_ms`
- `search.fess`: `q_len`, `size`, `hits`, `took_ms`, `http.status_code`
- `llm.*`: `model`, `timeout_ms`, `tokens_out?`, `status`

**Sampling:**
- Default 10% (`ASSERA_TRACE_SAMPLE=0.1`). **Always sample** on error.

---

## 6. Metrics (Prometheus Style)

### 6.1 Counters
- `assera_requests_total{route="/assist/query",code}`
- `assera_ratelimit_blocked_total{key}`
- `assera_llm_fallback_total{reason,stage}`

### 6.2 Histogram/Summary
- `assera_request_duration_ms_bucket{route}`
- `assera_search_duration_ms_bucket` / `assera_llm_duration_ms_bucket{stage}`
- `assera_citations_count_bucket`

### 6.3 Gauges
- `assera_inflight_requests{route}`

**UI side (optional):** `navigation_latency_ms_bucket`, `ui_errors_total{code}`

---

## 7. Retention Policy & Privacy

- **Retention period:** 30 days (changeable via environment variable)
- **Deletion:** Logs to standard output → delegate to external aggregation. Follow **GL regulations** at external destination
- **PII:** Do not collect. If unavoidably included, **immediately mask** and prevent recurrence
- **Training use:** **Never use** for LLM training

---

## 8. Implementation Guidelines

- **API:** Fixed JSON output with `structlog`/`loguru`, etc. Also JSONify `uvicorn` access logs
- **UI:** Prohibit `console.log`, aggregate to server output with dedicated logger (during SSR/Edge execution)
- **Request ID:** Number with middleware, reflect `X-Request-Id` in response
- **Hashing:** Short display (first 12 characters) of `sha256(base64(url))`

---

**End of Document**
