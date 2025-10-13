# Assera Docker Compose Deployment Design

**Document Version:** 1.0
**Last Updated:** 2025-10-12
**Target:** Assera OSS deployment (local/PoC distribution). UI: Next.js, API: FastAPI, Search: Fess (OpenAPI), LLM: Ollama. Assera API **does not connect to OpenSearch** (Fess only).

**Purpose:**
Enable one-command startup with `docker compose up -d`, with development hot-reload, healthcheck/dependency order, and network isolation standardization.

---

## 1. File Structure

```
repo-root/
├─ compose.yaml                  # Distribution/PoC (production-equivalent behavior)
├─ compose.dev.yaml              # Developer local (hot-reload)
├─ .env.example                  # Required environment variable template
├─ assera-api/                   # FastAPI (uv managed)
│  ├─ Dockerfile
│  └─ app/ ...
├─ assera-ui/                    # Next.js
│  ├─ Dockerfile
│  └─ app/ ...
└─ docs/ ...
```

---

## 2. Common Network and Exposure Policy

- All services belong to `assera-net` (bridge)
- **External exposure is `assera-ui` only** (default). API/Ollama/Fess/OpenSearch only `expose`, no external ports
- Reverse proxy (Nginx/Caddy/Traefik) optional in user environment (HTTPS termination)

---

## 3. compose.yaml (Distribution/PoC)

**Key Points:**
- Startup order: `opensearch → fess → ollama → assera-api → assera-ui` (`depends_on` + `healthcheck`)
- Exposure policy: `assera-ui:3000` only. Others `expose` only (internal network)
- Permissions: Non-root execution, `no-new-privileges` for hardening

```yaml
version: "3.9"
name: assera

services:
  assera-ui:
    build: ./assera-ui
    image: ghcr.io/codelibs/assera-ui:latest
    ports:
      - "3000:3000"    # Only external exposure port
    environment:
      NEXT_PUBLIC_API_BASE: "/api/v1"
      NEXT_PUBLIC_LATENCY_THRESHOLDS: "500,1500"
    depends_on:
      assera-api:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:3000/"]
      interval: 30s
      timeout: 5s
      retries: 5
    networks: [assera-net]

  assera-api:
    build: ./assera-api
    image: ghcr.io/codelibs/assera-api:latest
    expose: ["8000"]
    environment:
      TZ: ${TZ:-UTC}
      ASSERA_API_TOKEN: ${ASSERA_API_TOKEN}
      ASSERA_DEFAULT_MODEL: ${ASSERA_DEFAULT_MODEL:-gpt-oss}
      FESS_BASE_URL: ${FESS_BASE_URL:-http://fess:8080}
      OLLAMA_BASE_URL: ${OLLAMA_BASE_URL:-http://ollama:11434}
      ALLOWED_ORIGINS: ${ALLOWED_ORIGINS:-http://localhost:3000}
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
    depends_on:
      fess:
        condition: service_healthy
      ollama:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 5s
      retries: 5
    networks: [assera-net]

  fess:
    image: ghcr.io/codelibs/fess:latest
    expose: ["8080"]
    environment:
      ES_HTTP_URL: http://opensearch:9200
      JAVA_TOOL_OPTIONS: "-Xms512m -Xmx1024m"
    depends_on:
      opensearch:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 10
    volumes:
      - fess-data:/var/lib/fess
    networks: [assera-net]

  opensearch:
    image: opensearchproject/opensearch:2
    expose: ["9200", "9600"]
    environment:
      discovery.type: single-node
      plugins.security.disabled: "true"
      OPENSEARCH_JAVA_OPTS: "-Xms1g -Xmx1g"
    ulimits:
      memlock: {soft: -1, hard: -1}
      nofile: {soft: 65535, hard: 65535}
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:9200/_cluster/health"]
      interval: 30s
      timeout: 10s
      retries: 10
    volumes:
      - os-data:/usr/share/opensearch/data
    networks: [assera-net]

  ollama:
    image: ollama/ollama:latest
    expose: ["11434"]
    volumes:
      - ollama-models:/root/.ollama
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:11434/api/tags"]
      interval: 30s
      timeout: 5s
      retries: 5
    networks: [assera-net]

volumes:
  os-data:
  fess-data:
  ollama-models:

networks:
  assera-net:
    driver: bridge
```

---

## 4. compose.dev.yaml (Developer Hot-reload)

```yaml
version: "3.9"

services:
  assera-ui:
    build:
      context: ./assera-ui
    volumes:
      - ./assera-ui:/app
      - /app/node_modules
    environment:
      NEXT_PUBLIC_API_BASE: "http://localhost:8000/api/v1"
    command: ["npm", "run", "dev"]

  assera-api:
    build:
      context: ./assera-api
    volumes:
      - ./assera-api:/app
    environment:
      LOG_LEVEL: DEBUG
    command: ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

**Usage Example:**
```bash
# Development: default compose + dev overlay
docker compose -f compose.yaml -f compose.dev.yaml up --build
```

---

## 5. Environment Variables (.env.example)

```dotenv
# === Assera common ===
ASSERA_PROFILE=dist
ASSERA_API_TOKEN=change-me
ASSERA_DEFAULT_MODEL=gpt-oss
ASSERA_SEARCH_PROVIDER=fess
TZ=UTC

# === Endpoints (internal) ===
FESS_BASE_URL=http://fess:8080
OLLAMA_BASE_URL=http://ollama:11434

# === API ===
ALLOWED_ORIGINS=http://localhost:3000
RATE_LIMIT_RPM=60
LOG_LEVEL=INFO
```

> Actual values in `.env`. Do not commit to repository.

---

## 6. Initial Model Fetch (Ollama)

Initial model fetch required for first time (PoC uses `gpt-oss`):

```bash
# After starting containers
docker exec -it assera-ollama-1 ollama pull gpt-oss
```

Or use init container (alternative):
```yaml
  ollama-init:
    image: ollama/ollama:latest
    entrypoint: ["/bin/sh", "-lc", "ollama pull gpt-oss"]
    depends_on:
      ollama:
        condition: service_healthy
    networks: [assera-net]
    restart: "no"
```

---

## 7. Security Considerations

- External exposure **UI only**. API/Ollama/Fess/OS limited to internal network
- Terminate TLS/HSTS with reverse proxy, reverse proxy `/api` to `assera-api:8000`
- Apply `X-Frame-Options`/`frame-ancestors 'none'` to UI (clickjacking prevention)
- Do not output URL/token in logs (hash/mask)

---

## 8. Resource Guidelines & Tuning

| Service | CPU | MEM | Notes |
|---|---:|---:|---|
| opensearch | 1–2 vCPU | 2–4 GB | Adjust Java heap `-Xms/-Xmx` |
| fess | 1 vCPU | 1–2 GB | Increases during initial crawling |
| ollama | 2–4 vCPU | 4–8 GB | Model size dependent |
| assera-api/ui | 0.5 vCPU | 256–512 MB | Lightweight |

---

## 9. Reverse Proxy Example (Caddy)

```caddyfile
:443 {
  tls you@example.com
  encode zstd gzip

  @api path /api/*
  handle @api {
    reverse_proxy assera-api:8000
  }

  handle {
    reverse_proxy assera-ui:3000
  }
}
```

> Integrate UI and API under same domain (`/` and `/api`) to eliminate CORS (recommended).

---

## 10. Startup/Stop/Diagnostic Commands

```bash
# Startup
docker compose up -d --build

# Health status
docker compose ps

# Logs
docker compose logs -f assera-api

# Cleanup (preserve persistent data)
docker compose down

# Complete deletion (delete persistent data too)
docker compose down -v
```

---

## 11. Known Pitfalls

- Post-onboarding: Ollama model not fetched → `/assist/query` prone to fallback
- Immediately after Fess startup: OpenSearch initialization wait. Set sufficient healthcheck retries
- Windows environment: `memlock`/`ulimits` may not work → reduce heap size for workaround

---

## 12. Future Extensions

- Function switch using `profiles:` (e.g., `profile: observability` adds Prometheus/OTEL Collector)
- K8s conversion (provide `kompose` template or Helm Chart)
- Additional service considerations for MCP (fess-webapp-mcp) integration

---

**End of Document**
