# Intaste — Intelligent Assistive Search Technology

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

> **An open platform for intelligent, assistive, and human-centered search**

**Intaste** is an open-source platform that combines enterprise search with intelligent assistance. Designed with a human-centered philosophy, Intaste keeps users in control while providing AI-powered intent extraction and evidence-based guidance. Search results from Fess serve as transparent evidence, with LLM usage carefully limited to assistance rather than replacement. Built with Next.js (UI) and FastAPI (API).

---

## 1. Overview

- **Architecture**: `intaste-ui` (Next.js) / `intaste-api` (FastAPI) / `fess` (Search) / `opensearch` (For Fess) / `ollama` (LLM)
- **Principle**: Intaste **does not directly access OpenSearch** (only via Fess REST/OpenAPI)
- **Default Model**: Ollama `gpt-oss` (configurable)
- **License**: Apache License 2.0

---

## 2. Requirements

- Docker 24+ / Docker Compose v2+
- CPU x86_64 (arm64 also works, depending on Ollama model compatibility)
- Memory: 6–8GB recommended (including OpenSearch/Fess/Ollama)

---

## 3. Quick Start (5 Minutes)

```bash
# 1) Clone repository
$ git clone https://github.com/codelibs/intaste.git
$ cd intaste

# 2) Setup environment variables
$ cp .env.example .env
$ sed -i.bak \
  -e "s/INTASTE_API_TOKEN=.*/INTASTE_API_TOKEN=$(openssl rand -hex 24)/" \
  -e "s/INTASTE_UID=.*/INTASTE_UID=$(id -u)/" \
  -e "s/INTASTE_GID=.*/INTASTE_GID=$(id -g)/" \
  .env

# 3) Initialize data directories (Linux only)
$ make init-dirs
# Note: macOS/Windows users can skip this step

# 4) Start services (build on first run)
$ docker compose up -d --build

# 5) Pull LLM model (first time only)
$ docker compose exec ollama ollama pull gpt-oss

# 6) Health check
$ curl -fsS http://localhost:3000 > /dev/null && echo 'UI OK'
$ curl -fsS http://localhost:8000/api/v1/health && echo 'API OK'

# 7) Access in browser
# http://localhost:3000
```

> **Note**: Initial startup of OpenSearch/Fess may take several minutes. Compose uses `depends_on + healthcheck` to control startup order.

---

## 4. Health Checks

Intaste provides multiple health check endpoints for monitoring and orchestration:

### 4.1 Basic Health Check

```bash
curl http://localhost:8000/api/v1/health
# Returns: {"status":"ok"}
```

### 4.2 Liveness Probe (Kubernetes)

```bash
curl http://localhost:8000/api/v1/health/live
# Returns: {"status":"ok"}
```

- Use for Kubernetes `livenessProbe`
- Checks if the process is alive
- Does NOT check dependencies

### 4.3 Readiness Probe (Kubernetes)

```bash
curl http://localhost:8000/api/v1/health/ready
# Returns: {"status":"ready"} or {"status":"not_ready"}
```

- Use for Kubernetes `readinessProbe`
- Checks if service is ready to accept traffic
- Verifies Fess and Ollama are healthy
- Returns HTTP 503 if not ready

### 4.4 Detailed Health Check

```bash
curl http://localhost:8000/api/v1/health/detailed | jq .
```

Example response:

```json
{
  "status": "healthy",
  "timestamp": "2025-01-10T12:34:56.789Z",
  "version": "0.1.0",
  "dependencies": {
    "fess": {
      "status": "healthy",
      "response_time_ms": 45,
      "error": null
    },
    "ollama": {
      "status": "healthy",
      "response_time_ms": 123,
      "error": null
    }
  }
}
```

**Status values**:

- `healthy` - All dependencies are healthy
- `degraded` - Some dependencies are degraded but service still operational
- `unhealthy` - Critical dependencies are down

See [intaste-api/kubernetes-example.yaml](intaste-api/kubernetes-example.yaml) for Kubernetes deployment configuration.

---

## 5. Testing the System

### 5.1 API Smoke Test

```bash
# Use INTASTE_API_TOKEN from .env for X-Intaste-Token header
TOKEN=$(grep ^INTASTE_API_TOKEN .env | cut -d= -f2)

curl -sS -H "X-Intaste-Token: $TOKEN" \
     -H 'Content-Type: application/json' \
     -X POST http://localhost:8000/api/v1/assist/query \
     -d '{"query":"What is the latest security policy?"}' | jq .
```

- Success if you receive `answer.text` with `[1][2]…` style `citations`.

### 5.2 Model List / Selection

```bash
curl -sS -H "X-Intaste-Token: $TOKEN" http://localhost:8000/api/v1/models | jq .
# Example: {"default":"gpt-oss","available":["gpt-oss","mistral","llama3"]}

curl -sS -H "X-Intaste-Token: $TOKEN" \
     -H 'Content-Type: application/json' \
     -X POST http://localhost:8000/api/v1/models/select \
     -d '{"model":"mistral","scope":"session","session_id":"00000000-0000-0000-0000-000000000000"}'
```

### 5.3 Streaming Responses (SSE)

Intaste can stream LLM responses in real-time.

**Using the UI**:
- Toggle streaming mode with the "⚡ Stream" checkbox in the header (default: enabled)
- During streaming, displays "⚡ Streaming..."
- Answer text appears incrementally as it's generated

**Testing the API**:
```bash
# Server-Sent Events (SSE) endpoint
curl -sS -H "X-Intaste-Token: $TOKEN" \
     -H 'Content-Type: application/json' \
     -H 'Accept: text/event-stream' \
     -X POST http://localhost:8000/api/v1/assist/query/stream \
     -d '{"query":"What is the latest security policy?"}'

# Event stream format:
# event: start
# data: {"message":"Processing query..."}
#
# event: intent
# data: {"optimized_query":"...","keywords":[...]}
#
# event: citations
# data: {"citations":[...]}
#
# event: chunk
# data: {"text":"Answer text..."}
#
# event: complete
# data: {"answer":{...},"session":{...},"timings":{...}}
```

See [STREAMING.md](STREAMING.md) for detailed documentation.

---

## 6. Development Mode (Hot Reload)

```bash
# Specify dev compose as layer
$ docker compose -f compose.yaml -f compose.dev.yaml up -d --build

# Follow logs
$ docker compose logs -f intaste-api intaste-ui
```

- `intaste-api`: `uvicorn --reload`
- `intaste-ui`: `npm run dev -p 3000`

---

## 7. Configuration (.env)

| Variable | Default | Description |
|---|---|---|
| `INTASTE_API_TOKEN` | — | UI→API authentication key (required) |
| `INTASTE_DEFAULT_MODEL` | `gpt-oss` | Default Ollama model |
| `INTASTE_SEARCH_PROVIDER` | `fess` | Search provider (v0.1 supports fess only) |
| `FESS_BASE_URL` | `http://fess:8080` | Internal URL for API to call Fess |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Internal URL for API to call Ollama |
| `NEXT_PUBLIC_API_BASE` | `/api/v1` | API base path from UI |
| `TZ` | `UTC` | Timezone |

> **Security**: Set `INTASTE_API_TOKEN` to a sufficiently long random value.

---

## 8. Directory Structure

```
intaste/
├─ compose.yaml                # Production deployment
├─ compose.dev.yaml            # Development (hot reload)
├─ .env.example                # Environment variables sample
├─ Makefile                    # Common commands (up/down/logs)
├─ intaste-ui/                  # Next.js (App Router)
│   ├─ app/                    # Pages
│   ├─ src/                    # State/Components
│   └─ Dockerfile
├─ intaste-api/                 # FastAPI
│   ├─ app/                    # Routers/Services
│   ├─ core/                   # LLM/Search provider abstractions
│   └─ Dockerfile
└─ ops/                        # Health scripts/Monitoring
```

---

## 9. Using the UI

1. Enter a natural language question in the input field at the top and press Enter
2. View the brief answer with citation markers like `[1][2]…` in the center
3. Check selected document snippets in the right panel
4. Click "Open in Fess" to view the original document
5. Click suggested follow-ups at the bottom for conversational drill-down

> If no citations are found, the UI provides hints for refining the search.

---

## 10. Security Considerations

- Only `intaste-ui:3000` should be externally exposed. Keep `intaste-api`, `fess`, `opensearch`, and `ollama` on internal network
- UI→API authentication uses `X-Intaste-Token` header (no cookies)
- UI CSP/CORS configured with minimal privileges (see Security Design Document v0.1)

---

## 11. Troubleshooting

| Symptom | Cause / Solution |
|---|---|
| Permission denied on data/ directory (Linux) | Container UID/GID mismatch with host. Run `make init-dirs` or manually: `sudo chown -R 1000:1000 data/{opensearch,dictionary}` |
| UI returns 404/timeout | API health check failed. Check `docker compose ps` and `docker compose logs intaste-api` |
| Search always returns 0 results | Fess index not built. Check Fess admin panel / Crawl configuration |
| LLM error 503 | `ollama pull gpt-oss` not executed / insufficient memory. Switch to lighter model |
| API 401 error | `X-Intaste-Token` not set or mismatch. Sync `.env` value with UI |
| Slow startup | OpenSearch/Fess initialization in progress. Wait until health status shows `green/yellow` |

---

## 12. Contributing

1. Create an Issue with reproduction steps and expected behavior
2. Fork → Create branch (`feat/*`, `fix/*`)
3. Pass lint/unit tests and create PR
4. Update design documents (docs/) for major changes

Code conventions (recommended):
- API: `ruff` + `black`, UI: ESLint + Prettier
- Commit messages: Conventional Commits (`feat:`, `fix:`, `docs:` …)

---

## 13. License

```
Apache License 2.0
Copyright (c) 2025 CodeLibs
```

- Copyright notices in `NOTICE`
- Dependent OSS licenses consolidated in `THIRD-PARTY-NOTICES` (future)

---

## 14. Testing

```bash
# API tests
cd intaste-api
pytest --cov

# UI unit tests
cd intaste-ui
npm test

# E2E tests
cd intaste-ui
npm run test:e2e
```

See [TESTING.md](TESTING.md) for detailed documentation.

## 15. Documentation

- [TESTING.md](TESTING.md) - Test execution and test writing guide
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development and contribution guide
- [docs/](docs/) - Comprehensive design documents
  - [System Architecture](docs/02_architecture/system-architecture.md)
  - [Streaming Responses](docs/02_architecture/streaming-responses.md)
  - [Implementation Status](docs/01_requirements/implementation-status.md)
  - [Development Guidelines](docs/08_development/development-guidelines.md)
- [intaste-api/README.md](intaste-api/README.md) - API specification and development guide
- [intaste-ui/README.md](intaste-ui/README.md) - UI specification and development guide

