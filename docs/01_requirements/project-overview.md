# Intaste Project Overview

**Document Version:** 1.0
**Last Updated:** 2025-10-12
**Status:** Active

## Document Purpose

This document provides a comprehensive overview of the Intaste project, including its technical architecture, development policies, key features, and license conditions. It serves as the primary reference for developers, deployers, and community participants.

---

## 1. Project Overview

**Name:** Intaste
**Type:** Open Source AI-Assisted Search Platform
**License:** Apache License 2.0
**Development:** GitHub OSS (under CodeLibs organization)

Intaste is an **AI-assisted search platform** provided as open-source software. It analyzes user queries in natural language and generates responses by combining Fess search results with LLM (e.g., Ollama). Intaste itself does not depend on Fess or OpenSearch; the API layer is abstracted, allowing for easy addition of other search providers.

---

## 2. System Architecture Overview

```
+------------------------+
|      Intaste UI         |  ← Next.js / shadcn / Tailwind / i18n
+-----------+------------+
            |
            | (REST / HTTPS, X-Intaste-Token)
            v
+------------------------+
|      Intaste API        |  ← FastAPI / Python / JWT / OpenAPI
+-----------+------------+
            |
            | (Provider abstraction layer)
            v
+------------------------+
|  Search Provider (Fess) |  ← Access via Fess OpenAPI
+------------------------+
|  LLM Provider (Ollama)  |  ← Local model or Remote LLM
+------------------------+
```

**Component Configuration:**

- **Intaste UI**: SPA using Next.js + shadcn/ui + TailwindCSS. State management with Zustand, i18n support, accessible search UI.
- **Intaste API**: Lightweight backend using FastAPI. Integrates LLM and Fess, provides Assist API.
- **Fess**: Search engine. Accessed only via Intaste API, no direct access from UI.
- **Ollama**: Provides LLM as local inference environment (models pulled on demand).

---

## 3. Project Objectives

Intaste's development objectives are threefold:

1. **Standardization of LLM-Assisted Search through Open Source**
   Realize an architecture deployable in private environments as OSS.

2. **Safe Integration of Search Systems and LLM**
   Generate evidence-based responses based on Fess search results without directly passing data to LLM.

3. **Reusable Structure for Enterprises and Individual Developers**
   Abstract the API layer to allow future replacement of search engines and LLMs other than Fess.

---

## 4. Technology Stack

| Layer | Technology | Primary Role |
|--------|------|----------|
| Frontend | Next.js 15 / React 19 / shadcn/ui / TailwindCSS / Zustand / i18next | UI/UX, state management, internationalization |
| API Server | FastAPI / Python 3.13 / Pydantic / Uvicorn | REST API provision, search & LLM integration |
| Search Layer | Fess 14.x (OpenAPI) | Search result provision, metadata management |
| LLM Layer | Ollama (gpt-oss, etc.) | Answer generation, inference processing |
| Deployment | Docker Compose / GitHub Actions | Startup order management, CI/CD, OSS distribution |
| Authentication | API Token (X-Intaste-Token) | Security between UI and API |

---

## 5. Feature Overview

### User-Facing Features

- Conversational search interface
- LLM answers based on search results
- Links to reference documents (via Fess)
- Multi-language support (Japanese/English)
- Theme switching (light/dark)
- API token configuration and storage

### Developer-Facing Features

- REST-based Assist API provision
- Extension to non-Fess providers via Provider abstraction layer
- Log/metrics output mechanism (OpenTelemetry support planned)

---

## 6. API Overview

**Base URL**: `/api/v1`

| Endpoint | Method | Overview |
|----------------|-----------|------|
| `/assist/query` | POST | Submit query and return integrated LLM + search results answer |
| `/assist/feedback` | POST | Submit user evaluation of answer |
| `/health` | GET | Confirm service health |
| `/models` | GET | Get configuration info and model list |

---

## 7. Distinctive Design Policies

1. **Search Provider Abstraction**
   - Access via `SearchProvider` interface, not directly referencing Fess only
   - Easy extension examples: ElasticSearch, Vespa, MeiliSearch, etc.

2. **Flexible LLM Provider Configuration**
   - Standard is Ollama, but can switch to OpenAI / Azure OpenAI via environment variables (future extension)

3. **Security-First Design**
   - Only API Token authentication allowed from UI
   - Minimize external CORS, ensure traceability with X-Request-ID

4. **OSS Transparency**
   - Compliant with Apache 2.0, does not impede commercial or research use
   - All design documents, Docker configuration, and OpenAPI definitions included

---

## 8. Deployment Configuration

- `compose.yaml`: For production/PoC (with healthcheck and dependency order)
- `compose.dev.yaml`: Hot-reload configuration for development
- Network: Unified in `intaste-net`, only `intaste-ui` exposed externally
- Recommended environment: Linux / Docker Engine 24+, 8GB RAM or more

---

## 9. OSS Operations Policy

- **Public Repository**: GitHub (`github.com/codelibs/intaste`)
- **Issue Management**: Unified in GitHub Issues + Discussions
- **Release Policy**:
  - v0.1: Basic features (Assist API + UI)
  - v0.2: Streaming response support
  - v0.3: Multi-provider support, Telemetry features
- **Documentation Structure**:
  - `README.md`: Startup procedure, overview
  - `docs/`: Design documents, API specifications, license information

---

## 10. Future Plans

| Phase | Feature Enhancements |
|-----------|---------------|
| v0.2 | Streaming responses, SSE-compatible UI, LLM fallback improvements |
| v0.3 | Multi-search provider extension, authentication method expansion (JWT) |
| v0.4 | Monitoring and metrics output (Prometheus / OTEL Collector) |
| v1.0 | Stable release, official OSS community launch |

---

## 11. Contribution Guidelines (Summary)

- Pull Request-based development flow adopted
- Main branches: `main` (stable), `develop` (development)
- Code standards: PEP8 (Python) / ESLint + Prettier (TypeScript) compliance
- Commit messages: Conventional Commits compliance

---

## 12. Commercial Use and Disclaimer

- Intaste is available for commercial use under Apache License 2.0
- Development team does not guarantee operation; deployment is the responsibility of each user
- Quality of external LLM models and search service results is not covered by guarantee

---

**End — Intaste System Overview v1.0**
