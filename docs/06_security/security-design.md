# Intaste Security Design Specification

**Document Version:** 1.0
**Last Updated:** 2025-10-12
**Target:** Intaste OSS Initial Version (UI: Next.js / API: FastAPI / LLM: Ollama / Search: Fess OpenAPI)

**Prerequisites:**
- Intaste **does not directly access OpenSearch**. Search only via Fess REST/OpenAPI.
- UI→API uses API Key authentication (`X-Intaste-Token`). Future extensible to OIDC/JWT.
- Distribution via Docker Compose. External exposure is `intaste-ui` only (default).

---

## 1. Basic Security Principles

- **Minimal Exposure:** Only UI externally accessible. API/LLM/Fess/OpenSearch on internal network.
- **Zero Trust Premise:** Explicit authentication even for UI→API. Conscious of authorization boundaries in internal communication.
- **Log Minimization:** Suppress logging of sensitive info like PII, file paths. Thorough hashing and masking.
- **Secure by Default:** Non-root execution, `no-new-privileges`, strict CSP/CORS.
- **Dependency Management:** Standardize SBOM generation and vulnerability scanning (CI).

---

## 2. Authentication & Authorization

### 2.1 UI→API Authentication (Initial Version)

- **Method:** **API Key** (fixed-length random 32+ characters)
- **Header:** `X-Intaste-Token: <api-key>`
- **401 conditions:** Header missing, mismatch, expired
- **Issuance/Storage:** Via `.env`. Do not include actual values in distribution examples
- **Revocation:** Immediate invalidation on API restart or key replacement (future: keystore/multiple keys)

### 2.2 Future Extensions (Recommended Design)

- **JWT:** HS256 signature, `exp/iat/aud` required, minimum validity 1h, rotation
- **OIDC:** Enterprise SSO (AzureAD/Google/Keycloak, etc.)
- Authorization: Grant `role=user|admin` as `scope` (out of initial scope)

### 2.3 CSRF

- Current token sent in **header**, so CSRF impact limited. Future Cookie use applies `SameSite=Strict`, `CSRF-Token` double submit.

---

## 3. Network Boundaries & Exposure Policy

### 3.1 Separation via Compose

- Only `intaste-ui` exposes `ports` (e.g., `3000:3000`)
- `intaste-api`, `fess`, `opensearch`, `ollama` only `expose`. **No external exposure**
- Internal network: All services in `intaste-net`

### 3.2 Ingress/TLS (Operational Option)

- **TLS Termination** with reverse proxy (Nginx/Caddy/Traefik). UI→API on same origin or proxy to subpath `/api/v1`
- Recommended header: `Strict-Transport-Security: max-age=31536000; includeSubDomains` (TLS-required environments only)

### 3.3 Egress Control

- API container prohibits external network access in principle (Ollama/Fess internal only)
- Future: Whitelist connection destinations with eBPF/iptables

---

## 4. CORS / CSP / Headers

### 4.1 CORS (API)

- **Allowed origin:** `intaste-ui` only (enumerate in environment variable)
- **Allowed methods:** `GET, POST`
- **Allowed headers:** `Content-Type, X-Intaste-Token, X-Request-Id`
- **Credentials:** `false` (no Cookie use)

### 4.2 CSP (UI)

Example (strict):
- `default-src 'self'`
- `script-src 'self' 'unsafe-inline'` (minimum necessary. Future nonce/hash)
- `style-src 'self' 'unsafe-inline'`
- `img-src 'self' data:`
- `connect-src 'self' https://ui-host https://api-host` (replace with actual operational values)
- `frame-ancestors 'none'` (clickjacking prevention)

### 4.3 Other Security Headers

- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `X-Frame-Options: DENY` (or CSP `frame-ancestors 'none'`)
- Appropriate `Permissions-Policy` (disable camera/microphone/geolocation)

---

## 5. Logging / Audit / Masking

### 5.1 Log Policy

- **Minimalism:** Do not save full user input. Only summary metadata (character count, processing ms, count)
- **PII:** **Mask** email/phone/employee ID, etc. (`<EMAIL>`, `<PHONE>`)
- **URL/Path:** Do not leave actual URL in logs, record as **SHA-256 hash**
- **Request ID:** Number `X-Request-Id` and link across all layers

### 5.2 Audit Events

- `auth.failure` (401 count)
- `assist.query` (required ms, citations count)
- `assist.error` (by code)
- `open_in_fess` (URL hash, count)

### 5.3 Storage Location

- Local: Container standard output (`docker logs`)
- Future: Forward to OpenSearch / Loki / Cloud Logging

---

## 6. LLM Safety Design

### 6.1 Prompt Injection Countermeasures

- Specify "prohibit non-JSON output" in **System Prompt** (strict JSON for Intent/Compose)
- Do not embed input **quotes as-is** (escape/limit)
- **JSON parse** output, discard + retry on schema deviation (`BAD_LLM_OUTPUT`)

### 6.2 Hallucination Suppression

- Answer assumes **evidence guidance**. Prohibit assertions. Dates/numbers only if they exist in citations
- On timeout, **citations only** return fallback

### 6.3 Data Leakage Prevention

- Ollama is **internal model/local inference**. Do not send to external API (design principle)
- If allowing external LLM in future, implement **confidential filter** and **PII redaction** upstream

---

## 7. Input/Output Validation / Sanitization

- **API acceptance:** Schema validation with `pydantic`, size limit (e.g., 4096 chars)
- **UI display:** Fess `snippet` **sanitized with `dompurify`**, minimize allowed tags (`em`, etc.)
- **URL:** Click destination **whitelisted to Fess domain only**. Prevent Open Redirect

---

## 8. Container / OS Security

- **Non-root execution** (create UID/GID in Dockerfile)
- `security_opt: no-new-privileges:true`
- `read-only` root where possible (UI/API runtime)
- Remove excess Capabilities, prohibit `SYS_ADMIN`
- Thorough **healthcheck** (avoid DoS with queue)
- **Resource limits:** Explicit `mem_limit`, `cpus` (future)

---

## 9. Dependencies & Supply Chain

- **SBOM:** Generate with `syft`/`cyclonedx`, attach to deliverables
- **Vulnerability Scanning:** Integrate `grype`/`trivy` into CI
- **Image Pinning:** Recommend **digest pinning** instead of `:latest` (initial version prioritizes convenience)
- **Language Dependencies:** Ensure reproducibility with `uv lock` (Python), `npm ci` (Node)

---

## 10. Data Classification and Retention

- Input query/log assumes **Level-2 (Internal)**. Default retention period 30 days (changeable by environment)
- LLM I/O **not used for training** (explicit)
- If audit requirements exist, retain 90 days to external SIEM

---

## 11. Threat Modeling (Summary)

| Threat | Countermeasure |
|---|---|
| Authentication bypass | API Key validation, rate limiting, hard-to-guess key length |
| CSRF | Header token method, future Cookie: SameSite+CSRF measures |
| XSS | DOMPurify sanitization, strict CSP |
| Open Redirect | Fess domain whitelist |
| SSRF | Limit external egress, URL validation |
| DoS | Rate limiting, timeouts, healthcheck, resource limits |
| Prompt injection | JSON output only, schema validation, escape dangerous input |
| Information leakage | Log masking, URL hashing, prohibit external LLM transmission |

---

## 12. Rate Limiting & Timeouts

- **Soft limit:** **60 req/min/key** (initial recommendation)
- **On excess:** `429 Too Many Requests` (with `Retry-After`)
- **Timeout:** Total budget 5s for `/assist/query` (LLM:2s/Fess:2s/Compose:1s guideline)

---

## 13. Testing / Audit

- **Static analysis:** `bandit` (Python), `eslint` (TS)
- **Dependency scanning:** `trivy`, `npm audit` (CI)
- **e2e:** Automatic testing of XSS/open redirect/clickjacking (Playwright)
- **Load:** p95/p99 latency with continuous queries
- **Penetration:** Simple diagnosis guide with ZAP/Burp in README

---

## 14. Operational Guide (Excerpt)

- Make TLS required with front proxy. Enable HSTS (note application conditions)
- Do not include actual keys in `.env`. **External Secret management** (Vault/SOPS, etc.)
- Backup/restore procedures (Fess/OpenSearch data in separate chapter)

---

## 15. Future Extensions

- OIDC/JWT authorization, audit log signing, tamper detection
- For K8s: NetworkPolicy/PodSecurity/Secrets management
- Monitoring integration (Prometheus/Grafana) and alert threshold definitions

---

**End of Document**
