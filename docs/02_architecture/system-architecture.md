# Assera System Architecture Design

**Document Version:** 1.0
**Last Updated:** 2025-10-12
**Target:** Assera OSS Initial Version (UI: Next.js / API: FastAPI / Search: Fess OpenAPI / LLM: Ollama)

**Purpose:**
Define component configuration, communication paths, network/ports, startup order, and operational modes (on-premises/cloud) as standards, ensuring consistency with other design documents (API/UI/Security/Operations & Monitoring/Testing).

---

## 1. Overall Configuration (Logical Architecture)

```
+----------------------+             +--------------------+
|        User          |  HTTPS      |     Assera UI      |
|  (Browser: SPA)      +------------>+  Next.js (3000)    |
+----------------------+             +----------+---------+
                                                |
                                                | HTTP (internal, same origin or /api proxy)
                                                v
                                      +---------+----------+
                                      |     Assera API     |
                                      | FastAPI (8000)     |
                                      +----+---------+-----+
                                           |         |
                      HTTP (internal)      |         | HTTP (internal)
                                           |         |
                                           v         v
                                +----------+--+   +--+-----------+
                                |   Fess      |   |    Ollama    |
                                | WebApp 8080 |   | 11434        |
                                +------+------+   +--------------+
                                       |
                                       | HTTP (internal)
                                       v
                                +------+------------------+
                                |  OpenSearch 9200/9600   |
                                |  (Fess-dedicated)       |
                                +-------------------------+
```

**Principle:** Assera **does not connect directly to OpenSearch**. Search is only via Fess REST/OpenAPI.

---

## 2. Deployment View (Docker Compose)

- **Services:** `assera-ui`, `assera-api`, `fess`, `opensearch`, `ollama`
- **Network:** All services contained in `assera-net` (bridge)
- **External Exposure:** Only `assera-ui:3000/tcp` by default. Others only `expose`
- **Startup Order:** `opensearch → fess → ollama → assera-api → assera-ui` (`depends_on + healthcheck`)

---

## 3. Communication Specifications (Interfaces)

### 3.1 UI → API

- **Protocol:** HTTP/1.1 (HTTP/2 compatible in future)
- **Endpoint:** `/api/v1/*`
- **Authentication:** Header `X-Assera-Token`
- **CORS:** Only UI origin allowed (same origin recommended / reverse proxy `/api` subpath)

### 3.2 API → Fess

- **Search Endpoint:** `GET {FESS_BASE_URL}/api/v1/documents?q=...`
- **Health Endpoint:** `GET {FESS_BASE_URL}/api/v1/health`
- **Authentication:** None or `Authorization` (environment dependent)
- **Timeout:** 2s (part of /assist total 5s)

### 3.3 API → Ollama

- **Endpoint:** `POST {OLLAMA_BASE_URL}/api/chat` (or `generate` depending on model)
- **Timeout:** 2–3s (intent extraction/explanation generation)

### 3.4 Fess → OpenSearch (Reference)

- `FESS_ES_URL=http://opensearch:9200` (internal)

---

## 4. Port/Protocol List

| Service | Port | Protocol | Public | Purpose |
|---|---:|---|---|---|
| assera-ui | 3000 | HTTP(S) | **External** | SPA delivery, API proxy (optional) |
| assera-api | 8000 | HTTP | Internal | REST API (/assist, etc.) |
| fess | 8080 | HTTP | Internal | Search REST/OpenAPI, admin UI (internal ops) |
| opensearch | 9200/9600 | HTTP | Internal | Fess backend |
| ollama | 11434 | HTTP | Internal | LLM execution |

---

## 5. Configuration and Settings Management

### 5.1 Environment Variables (Excerpt)

- `ASSERA_API_TOKEN` (required)
- `ASSERA_DEFAULT_MODEL=gpt-oss`
- `ASSERA_SEARCH_PROVIDER=fess`
- `FESS_BASE_URL=http://fess:8080`
- `OLLAMA_BASE_URL=http://ollama:11434`
- `NEXT_PUBLIC_API_BASE=/api/v1`

### 5.2 Handling Secrets

- Load from `.env`. Do not include actual values in repository
- Recommend Secret management (Vault/SOPS, etc.) in operations

---

## 6. Failure Modes and Fallbacks

| Event | Impact | API Behavior | UI Behavior | Operational Response |
|---|---|---|---|---|
| Ollama high latency/down | Answer generation unavailable | `LLM_UNAVAILABLE` / **return citations only** | Display re-search suggestion | Switch/restart model |
| Fess high latency/down | Search unavailable | `UPSTREAM_FESS_ERROR` / `TIMEOUT` | Display "search server busy" | Restart Fess/OS, check crawling |
| OpenSearch startup delay | Fess search unavailable | Fess waits / API returns 502/504 | Suggest retry | Review startup order/healthcheck |
| API high load | Latency increase | `429` rate limiting | Retry UI | Adjust limits/scale |

- Timeout total budget: 5s for `/assist/query` (intent extraction 2s, search 2s, explanation 1s)

---

## 7. Availability & Scalability

### 7.1 Scaling Strategy (PoC → Small-Scale Operations)

- **UI/API:** Multiple replicas (future). Single in Compose. Sessions are stateless
- **Fess/OpenSearch:** Single node premise (PoC). Future clustering (standard Fess/OS features)
- **Ollama:** Memory optimization based on model size. Can be replaced with external inference API (LLM abstraction layer)

### 7.2 Performance Indicators

- `/assist/query` p95 ≤ 2s (small scale, 10 results)
- LLM timeout rate < 5%
- Monitor empty hit rate (query quality indicator)

---

## 8. Security Boundaries (Summary)

- External exposure only for `assera-ui`. API/LLM/Fess/OS on internal network
- API authentication: `X-Assera-Token` required. CORS limited to UI origin
- UI: CSP restricts `connect-src` to API only. `frame-ancestors 'none'`
- HTML sanitization (DOMPurify) protects right pane highlight display

(Details: See "Security Design Specification v1.0")

---

## 9. Deployment Patterns

### 9.1 Local/PoC (Compose Default)

- `docker compose up -d --build`
- Initial model fetch: `ollama pull gpt-oss`

### 9.2 Behind Reverse Proxy (HTTPS Termination)

- TLS termination with Nginx/Caddy/Traefik
- Integrate UI and API under same domain (`/` and `/api`) (avoid CORS)

### 9.3 Cloud Verification

- Use Compose as-is on single VM
- Mount persistent volumes (OpenSearch/Fess/Ollama models) to external storage

---

## 10. Observability (Summary)

- Structured JSON logs (`ts/level/service/event/request_id`)
- Prometheus-style metrics (latency, fallback rate, 5xx rate)
- Distributed tracing via OpenTelemetry (optional, 10% sampling)

(Details: See "Logging & Audit Design Specification v1.0")

---

## 11. Implementation Directory Mapping

| Item | Implementation Location |
|---|---|
| API routers | `assera-api/app/routers/*.py` |
| Assist service | `assera-api/app/services/assist.py` |
| Search Provider abstraction | `assera-api/app/core/search_provider/*` |
| LLM client | `assera-api/app/core/llm/*` |
| UI pages | `assera-ui/app/page.tsx` |
| UI state | `assera-ui/src/stores/*` |

---

## 12. Risks and Responses

| Risk | Response |
|---|---|
| Dependent service startup delay | Healthcheck and retry, timeout allocation review |
| Model memory shortage | Choose lightweight model, adjust `num_ctx/num_predict` |
| Search API specification changes | Absorb via Search Provider abstraction, escape to `meta` |

---

## 13. Change Management

- Changes to this document managed via PR. Link to release tags
- For major changes, update cross-references in related design documents (API/UI/Security/Compose)

---

**End of Document**
