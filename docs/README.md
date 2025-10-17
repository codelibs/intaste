# Intaste Documentation Index

**Last Updated:** 2025-10-17
**Version:** 1.0

Welcome to the Intaste documentation! This index provides a comprehensive guide to all technical documentation for the Intaste AI-assisted search platform.

---

## 📚 Documentation Structure

The documentation is organized into the following categories:

### 1. Requirements
High-level project overview and requirements specification.

- **[Project Overview](01_requirements/project-overview.md)** - Complete project overview including objectives, architecture, technology stack, and roadmap
- **[Implementation Status](01_requirements/implementation-status.md)** - Current implementation status and feature tracking

### 2. Architecture
System architecture and design principles.

- **[System Architecture](02_architecture/system-architecture.md)** - Logical and deployment architecture, component configuration, communication paths, and network design
- **[Process Flow Design](02_architecture/process-flow-design.md)** - Detailed query processing flow, streaming responses, and phase-based pipeline design
- **[Search Provider Abstraction](02_architecture/search-provider-abstraction.md)** - Abstract layer design for search providers, Fess implementation, and future extensibility
- **[Streaming Responses](02_architecture/streaming-responses.md)** - Server-Sent Events (SSE) implementation for real-time answer streaming

### 3. API
API specifications and detailed design.

- **[API Specification](03_api/api-specification.md)** - Complete REST API specification including authentication, endpoints, data models, error handling, and internal algorithms

### 4. UI
User interface design and implementation.

- **[UI Design Specification](04_ui/ui-design-specification.md)** - Comprehensive UI design including component structure, state management, API integration, and accessibility

### 5. Deployment
Deployment configurations and environment setup.

- **[Docker Compose Design](05_deployment/docker-compose-design.md)** - Complete Docker Compose deployment guide including production and development configurations, healthchecks, and startup ordering
- **[Environment Configuration](05_deployment/environment-configuration.md)** - Environment variable management, configuration validation, and secret handling

### 6. Security
Security design and best practices.

- **[Security Design](06_security/security-design.md)** - Comprehensive security design including authentication, network boundaries, CORS/CSP, logging policies, LLM safety, and threat modeling

### 7. Operations
Operational guidelines and monitoring.

- **[Operations & Monitoring](07_operations/operations-monitoring.md)** - Monitoring strategy, health checks, metrics design, log policies, and alert recommendations
- **[Logging & Audit Design](07_operations/logging-audit-design.md)** - Structured logging, distributed tracing, audit events, and retention policies

### 8. Development
Development workflows and contribution guidelines.

- **[Development Guidelines](08_development/development-guidelines.md)** - Coding standards, branch strategy, commit conventions, testing strategy, CI/CD, and release procedures

---

## 🚀 Quick Start Guides

### For Developers
1. Start with **[Project Overview](01_requirements/project-overview.md)** to understand the system
2. Review **[System Architecture](02_architecture/system-architecture.md)** for component structure
3. Check **[Development Guidelines](08_development/development-guidelines.md)** for coding standards
4. Follow **[Docker Compose Design](05_deployment/docker-compose-design.md)** to run locally

### For Deployers
1. Read **[Project Overview](01_requirements/project-overview.md)** for requirements
2. Study **[Docker Compose Design](05_deployment/docker-compose-design.md)** for deployment
3. Configure using **[Environment Configuration](05_deployment/environment-configuration.md)**
4. Implement **[Security Design](06_security/security-design.md)** recommendations
5. Set up monitoring from **[Operations & Monitoring](07_operations/operations-monitoring.md)**

### For API Users
1. Review **[API Specification](03_api/api-specification.md)** for endpoint details
2. Understand **[Process Flow Design](02_architecture/process-flow-design.md)** for request processing
3. Check **[Security Design](06_security/security-design.md)** for authentication

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    Intaste UI                        │
│            (Next.js + shadcn/ui)                    │
└──────────────────┬──────────────────────────────────┘
                   │ REST/HTTPS (X-Intaste-Token)
                   ↓
┌─────────────────────────────────────────────────────┐
│                  Intaste API                         │
│              (FastAPI + Python)                     │
└──────────────┬─────────────────┬────────────────────┘
               │                 │
               │ OpenAPI         │ HTTP
               ↓                 ↓
┌──────────────────────┐  ┌─────────────────────┐
│  Search Provider     │  │   LLM Provider      │
│    (Fess)            │  │    (Ollama)         │
└──────────────────────┘  └─────────────────────┘
```

**Key Principles:**
- Intaste **does not directly access OpenSearch** - only via Fess API
- Search provider abstraction enables future extensibility
- API-first design with comprehensive OpenAPI specification
- Security-first with API token authentication and strict CORS/CSP

---

## 📋 Key Features

- **AI-Assisted Search:** Natural language query understanding with LLM
- **Evidence-Based Responses:** Answers grounded in search results with citations
- **Streaming Responses:** Real-time updates via Server-Sent Events (SSE)
- **Multi-language Support:** Japanese and English
- **Docker-Based Deployment:** One-command startup with Docker Compose
- **Open Source:** Apache License 2.0

---

## 🔧 Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, React 19, shadcn/ui, TailwindCSS, Zustand |
| API | FastAPI, Python 3.13, Pydantic, Uvicorn |
| Search | Fess 14.x (OpenAPI) |
| LLM | Ollama (gpt-oss default) |
| Deployment | Docker Compose, GitHub Actions |

---

## 📖 Document Conventions

All documents follow this structure:
- **Document Version:** Semantic versioning
- **Last Updated:** ISO date format
- **Target/Purpose:** Clear scope definition
- **Sections:** Numbered with clear hierarchy

---

## 🤝 Contributing

Please refer to **[Development Guidelines](08_development/development-guidelines.md)** for:
- Branch strategy and commit conventions
- Code quality standards
- Testing requirements
- Pull request process
- Release procedures

---

## 📝 License

Intaste is licensed under the Apache License 2.0. See the LICENSE file in the repository root for details.

---

## 📞 Support

- **GitHub Issues:** Report bugs and request features
- **GitHub Discussions:** Community discussions and questions
- **Documentation:** This comprehensive guide

---

## 🗺️ Documentation Roadmap

### Current (v1.0)
- ✅ Complete architecture and design specifications
- ✅ API and UI documentation
- ✅ Deployment and operations guides
- ✅ Security and development guidelines

### Planned (Future Versions)
- ✅ Streaming response implementation (see [Streaming Responses](02_architecture/streaming-responses.md))
- ⏳ Multi-provider extension guide
- ⏳ Kubernetes deployment guide
- ⏳ Advanced monitoring and observability
- ⏳ API client SDKs documentation

---

**Note:** All documentation is maintained in English. Original Japanese documents have been migrated and consolidated into this structured format for better maintainability and international collaboration.

---

*Generated: 2025-10-17 | Intaste Documentation Team*
