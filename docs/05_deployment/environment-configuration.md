# Intaste Environment Configuration Management

**Document Version:** 1.0
**Last Updated:** 2025-10-12
**Target:** Intaste OSS Initial Version (UI: Next.js / API: FastAPI / Search: Fess OpenAPI / LLM: Ollama)

**Purpose:**
Unify **definition, defaults, validation, priority, and secret management** of environment variables and configuration to prevent misconfig and confidential exposure in local/distribution (PoC)/future operational environments.

---

## 1. Configuration Model (Layers and Priority)

```
(High Priority)  1. Process environment variables (container env / CI secrets)
                2. .env (project root, for docker compose)
                3. .env.local (developer local only, gitignored)
                4. Component defaults (default in code)
(Low Priority)
```

- **Principle:** All settings injected via **environment variables** (12-factor)
- **Compose:** Reads `.env` and reflects in `environment:`
- **Secrets:** Do not include actual values in Git (no actual values in `.env`, CI/Secrets management)

---

## 2. Configuration Items List (Standard)

### 2.1 Common

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `TZ` | string | `UTC` | Optional | Timezone |
| `INTASTE_PROFILE` | enum(`dev`,`dist`) | `dist` | Optional | Configuration profile (development/distribution) |
| `INTASTE_API_TOKEN` | secret | — | **Required** | UI→API API Key (32+ characters) |
| `INTASTE_SEARCH_PROVIDER` | enum | `fess` | Optional | Search provider (initial version fixed to `fess`) |
| `INTASTE_DEFAULT_MODEL` | string | `gpt-oss` | Optional | Ollama default model name |

### 2.2 API (FastAPI)

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `PORT` | int | `8000` | Optional | API listen port |
| `ALLOWED_ORIGINS` | csv | `http://localhost:3000` | Optional | CORS allowed origins (comma-separated) |
| `RATE_LIMIT_RPM` | int | `60` | Optional | Requests per minute limit per API Key |
| `REQ_TIMEOUT_MS` | int | `5000` | Optional | Total budget for `/assist/query` (ms) |
| `LLM_TIMEOUT_MS` | int | `3000` | Optional | LLM call timeout (ms) |
| `FESS_TIMEOUT_MS` | int | `2000` | Optional | Fess call timeout (ms) |
| `LOG_LEVEL` | enum | `INFO` | Optional | API log level (DEBUG/INFO/WARN/ERROR) |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | url | — | Optional | OTLP export destination (disabled if empty) |

### 2.3 UI (Next.js)

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `NEXT_PUBLIC_API_BASE` | path | `/api/v1` | Optional | UI→API base path (relative recommended) |
| `NEXT_PUBLIC_LATENCY_THRESHOLDS` | csv(int,int) | `500,1500` | Optional | Low/med/high latency thresholds (ms) |

### 2.4 Integration Destinations (Internal Endpoints)

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `FESS_BASE_URL` | url | `http://fess:8080` | Optional | API→Fess call destination (internal) |
| `OLLAMA_BASE_URL` | url | `http://ollama:11434` | Optional | API→Ollama call destination (internal) |

---

## 3. Validation and Startup Checks

### 3.1 API (pydantic v2)

```python
from pydantic import BaseModel, Field, HttpUrl

class Settings(BaseModel):
    intaste_api_token: str = Field(min_length=32, alias='INTASTE_API_TOKEN')
    intaste_default_model: str = Field(default='gpt-oss', alias='INTASTE_DEFAULT_MODEL')
    allowed_origins: list[str] = Field(default=['http://localhost:3000'], alias='ALLOWED_ORIGINS')
    req_timeout_ms: int = Field(default=5000, ge=1000, le=20000, alias='REQ_TIMEOUT_MS')
    fess_base_url: HttpUrl = Field(default='http://fess:8080', alias='FESS_BASE_URL')
```

- Startup failure criteria: **Required items unset / type mismatch / out of threshold** → immediate error (`SystemExit`)
- Do not output actual token in logs. Mask (first 4 digits + `…`)

### 3.2 UI (Next.js)

- Only `NEXT_PUBLIC_*` exposed to client. `process.env` injected at build time
- Unset/type error → **build failure** (validation script in `scripts: prebuild`)

---

## 4. Profiles and Defaults

| Profile | Purpose | Representative Settings |
|---|---|---|
| `dev` | Local development (`compose.dev.yaml`) | `LOG_LEVEL=DEBUG`, `ALLOWED_ORIGINS=*` (caution) |
| `dist` | Distribution (PoC/evaluation) | Minimum privilege (CORS UI origin only, strict CSP), log at `INFO` |

> Mechanism to inject **safe defaults** by overriding at startup with `INTASTE_PROFILE` (code-side preset).

---

## 5. Secret Management

- `.env.example` contains **dummy values only**. Actual values in `.env` (PoC) or inject from CI/Secret management
- Do not commit `.env` in shared environments
- Generation: Recommend length of `openssl rand -hex 24` or more
- Do not output tokens, etc. in logs/audit, use SHA-256 hash if necessary

---

## 6. `.env.example` Template

```dotenv
# === Intaste common ===
INTASTE_PROFILE=dist
INTASTE_API_TOKEN=change-me
INTASTE_DEFAULT_MODEL=gpt-oss
INTASTE_SEARCH_PROVIDER=fess
TZ=UTC

# === Endpoints (internal) ===
FESS_BASE_URL=http://fess:8080
OLLAMA_BASE_URL=http://ollama:11434

# === API ===
PORT=8000
ALLOWED_ORIGINS=http://localhost:3000
RATE_LIMIT_RPM=60
REQ_TIMEOUT_MS=5000
LLM_TIMEOUT_MS=3000
FESS_TIMEOUT_MS=2000
LOG_LEVEL=INFO

# === UI ===
NEXT_PUBLIC_API_BASE=/api/v1
NEXT_PUBLIC_LATENCY_THRESHOLDS=500,1500
```

---

## 7. Compose Integration and Substitution

- `compose.yaml` automatically reads `.env` and reflects in `environment:`
- Sensitive values injected via **environment variables** not `secrets:` (simplicity priority, migrate to Secret for K8s)
- Example:
```yaml
services:
  intaste-api:
    environment:
      - INTASTE_API_TOKEN=${INTASTE_API_TOKEN}
      - FESS_BASE_URL=${FESS_BASE_URL}
```

---

## 8. Timeout/Rate Limit Guidelines

- `/assist/query` budget `REQ_TIMEOUT_MS` allocated **intent extraction(40%) / search(40%) / explanation(20%)**
- `RATE_LIMIT_RPM` default 60. Adjust in operations

---

## 9. Failure Behavior

| Event | Detection | At Startup | At Runtime |
|---|---|---|---|
| Required variable missing | Type validation | **Startup failure** | — |
| Invalid URL | Parse failure | **Startup failure** | — |
| Timeout invalid | Out of range | **Startup failure** | — |
| Invalid CORS | Actual access | Warning log | Reject request (403) |

---

**End of Document**
