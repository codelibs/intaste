# Intaste Operations & Monitoring Design

**Document Version:** 1.0
**Last Updated:** 2025-10-12
**Target:** Intaste OSS Initial Version (UI: Next.js / API: FastAPI / Search: Fess OpenAPI / LLM: Ollama)

**Purpose:**
Define monitoring, log, metrics, and alert design guidelines to enable flexible user monitoring and operation of Intaste's operational status. As OSS, use **design independent of specific monitoring tools**.

---

## 1. Premises and Design Policy

- Intaste is **OSS middleware**; monitoring tool selection and threshold settings left to users
- This document defines monitoring "recommended items, structure, perspectives"
- Adopt metrics design to facilitate deployment with OSS stack like **Prometheus + Grafana**, assuming operation on container infrastructure (Docker Compose / Kubernetes)

---

## 2. Monitoring Configuration Overview

| Layer | Monitoring Target | Overview |
|--------|----------|------|
| Application | FastAPI, Next.js | Health check, error rate, response time |
| LLM Layer | Ollama | Model operation confirmation, inference time, abnormal response ratio |
| Search Layer | Fess/OpenSearch | API response, error rate, index count |
| Infrastructure | Container/Host | CPU, memory, disk, network |
| Integration | OpenTelemetry/Prometheus | Various metrics collection, trace integration |

---

## 3. Health Checks

### 3.1 API
- **Endpoint:** `/api/v1/health`
- **No authentication required:** Simple connectivity check for API, Fess, Ollama (HTTP 200 only)
- **Detailed diagnosis (future extension):** `/api/v1/status` concept to return each dependent module status as JSON

### 3.2 UI
- Monitor if `/` returns 200 response
- Liveness: Confirm HTTP 200 + HTML title string

### 3.3 Container
- Docker health check example:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
  interval: 30s
  timeout: 5s
  retries: 3
```

---

## 4. Metrics Design (API / FastAPI)

| Metric Name | Type | Description |
|--------------|------|------|
| `intaste_request_count_total` | counter | Total requests (path, status, method labels) |
| `intaste_request_latency_ms` | histogram | Request latency (p50/p95/p99 aggregation) |
| `intaste_llm_latency_ms` | histogram | Intent / Compose each call response time |
| `intaste_fess_latency_ms` | histogram | Fess search API response time |
| `intaste_error_total` | counter | Stage-specific error (intent/search/compose) count |
| `intaste_fallback_total` | counter | LLM fallback occurrence count |
| `intaste_rate_limit_count` | counter | Rate limit occurrence count |
| `intaste_active_sessions` | gauge | Current session count |
| `intaste_model_selected_total` | counter | Model selection count (model label) |

> Collectable via OpenTelemetry or Prometheus Exporter.

---

## 5. Log Design

### 5.1 Structured Logs
- **Output format:** JSON (1 event per line)
- **Output destination:** `stdout` (Docker standard output)
- **Required fields:** `timestamp`, `level`, `request_id`, `path`, `status`, `elapsed_ms`
- **Optional fields:** `session_id`, `stage`, `reason`, `model`, `user_agent`

### 5.2 Log Level Policy

| Level | Representative Content |
|--------|----------|
| DEBUG | Configuration loading, dependency call details (for development) |
| INFO | Startup/normal response/user operation events |
| WARN | LLM retry, fallback occurrence |
| ERROR | Fess/Ollama response abnormality, unhandled exceptions |

### 5.3 Masking / Anonymization
- Mask API Key, URL, user input before log output
- Do not output request body at INFO. Limited to DEBUG only

---

## 6. Alert Design (Recommended Indicators)

| Category | Condition | Recommended Threshold | Response Policy |
|------|------|----------|----------|
| Response delay | p95 > 3s | Continuous 5+ minutes | Check Fess/Ollama load |
| Error rate | 5xx > 2% | Continuous 10+ minutes | API restart, dependency connectivity check |
| Fallback rate | >10% | Continuous 15+ minutes | Adjust LLM settings or timeout |
| LLM no response | 3 consecutive failures | Immediate notification | Confirm Ollama down |
| Fess response failure | 3 consecutive failures | Immediate notification | Consider Fess restart |

> OSS users can set custom thresholds with Prometheus Alertmanager, etc.

---

## 7. Trace Design

- Standard adoption of OpenTelemetry (OTEL). Use following as trace units:
  - `/assist/query` (root span)
  - Intent LLM call (child span)
  - Fess search call (child span)
  - Compose LLM call (child span)
- Propagation header: `traceparent` (W3C Trace Context compliant)
- Visualization: Recommend Grafana Tempo / Jaeger, etc.

---

## 8. Dashboard Example (Recommended Items)

| Category | Visualization Items |
|----------|------------|
| Performance | Request count, latency p95, error rate |
| LLM | Intent/Compose latency, fallback count |
| Search | Fess response time, error count |
| Model selection | Usage rate by model, session count |
| Resources | CPU, MEM, network I/O |

> OSS users can freely visualize with Grafana, etc.

---

## 9. Operational Guidelines

- **Startup confirmation:** `/health` normal response, confirm `Intaste API started` in logs
- **Configuration changes:** Re-apply with `compose down && compose up -d` after `.env` editing
- **Log rotation:** Recommend forwarding docker logs → fluentd / loki, etc.
- **Backup targets:** Configuration files (`.env`), search index (Fess/OpenSearch)
- **Updates:** Rebuild according to OSS release notes (`docker compose pull` → `up -d`)

---

## 10. Security & Audit Perspective

- Record `request_id`, `session_id`, `ip_hash` in audit log (INFO level)
- Prohibit saving tokens or input content. Hash if necessary (SHA256)
- OSS distribution explicitly states **security responsibility delegated to users** in README

---

## 11. SLO / SLA Reference Values

| Indicator | Target Value (SLO) | Notes |
|------|--------------|------|
| API uptime | 99.5% | OSS standard, user operation dependent |
| Response latency(p95) | Within 2.5s | `/assist/query` standard |
| LLM fallback rate | <5% | Stable operation indicator |
| Error rate | <1% | Including Fess/Ollama |

---

## 12. Future Extensions

- Metrics integration via MCP (fess-webapp-mcp)
- Bundled provision with OpenTelemetry Collector
- Addition of `intastectl` CLI for status confirmation commands

---

**End of Document**
