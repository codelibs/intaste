# Intaste Search Provider Abstraction Layer Design

**Document Version:** 1.0
**Last Updated:** 2025-10-12
**Target:** Intaste OSS Initial Version (API: FastAPI)

**Important:** Intaste **does not connect directly to OpenSearch**. Search is **only via Fess OpenAPI**, with a future-proof abstraction layer for provider replacement.

**Purpose:**
- Hide search infrastructure differences from UI/service layer (interface boundary)
- Ensure Fess OpenAPI consistency, mapping, and error conventions
- Enable future additions (fess-webapp-mcp, external search) **non-destructively**

---

## 1. Architecture Boundaries

```
assist service ─┬─ LLM client
                └─ SearchProvider (abstract)
                         ├─ FessSearchProvider (initial version)
                         └─ (future) MCPPassthroughProvider / Other
```

- **Dependency Direction**: `assist service` → `SearchProvider` (abstract) → concrete `FessSearchProvider`
- **Forbidden**: `assist service` directly depending on Fess HTTP/parameters

---

## 2. Domain Model

```typescript
// Common normalized model (similar to API response)
export type SearchHit = {
  id: string;            // Stable ID (url hash or fess id)
  title: string;
  url: string;           // Absolute URL (Open in Fess navigation)
  snippet?: string;      // May contain HTML (sanitize in UI)
  score?: number;
  meta?: Record<string, any>; // contentType/site/lastModified, etc.
}

export type SearchResult = {
  total: number;
  hits: SearchHit[];
  took_ms?: number;
  page: number;          // 1-origin
  size: number;
}

export type SearchQuery = {
  q: string;             // normalized_query
  page?: number;         // 1-origin
  size?: number;         // 1..50 recommended
  sort?: 'score'|'date_desc'|'date_asc';
  language?: string;     // 'ja' | 'en' ...
  filters?: Record<string, any>; // site/mimetype/period etc
  timeout_ms?: number;   // default FESS_TIMEOUT_MS
}
```

---

## 3. Abstract Interface

```python
# intaste-api/app/core/search_provider/base.py
from typing import Protocol, Tuple

class SearchProvider(Protocol):
    async def search(self, query: "SearchQuery") -> "SearchResult": ...
    async def health(self) -> Tuple[bool, dict]: ...  # Simple connectivity check
```

- `health()`: Minimal connectivity check for `/health` endpoint (200 or returned JSON)

---

## 4. Fess Implementation (Mapping Design)

### 4.1 Call Destination (Reference)
- Fess search OpenAPI: **`/api/v1/documents`** (user-facing)
- Fess health OpenAPI: **`/api/v1/health`** (monitoring)
- Main parameters (Fess side):
  - `q` (query)
  - `start`, `num` (paging)
  - `sort` (`score` / `last_modified desc`, etc.)
  - `fields.label`, `facet.query`, etc. (as needed)

> Actual implementation follows repository OpenAPI definition: `intaste-api/openapi/fess.yaml`

### 4.2 Parameter Conversion

| Intaste(SearchQuery) | Fess Query | Notes |
|---|---|---|
| `q` | `q` | Pass as-is (LLM normalized) |
| `page` | `start = (page-1)*size` | Convert to 0-origin |
| `size` | `num` | Upper limit follows Fess config (recommended 10–50) |
| `sort=score` | `sort=score` | Default |
| `sort=date_desc` | `sort=last_modified desc` | |
| `sort=date_asc` | `sort=last_modified asc` | |
| `filters.site` | `site` / `fields.host`, etc. | Choose based on project policy |
| `filters.mimetype` | `mimetype` | |
| `filters.updated_after` | `last_modified_from` | ISO8601 / Epoch possible (follow Fess spec) |
| `language` | `lang` | Optional |

### 4.3 Response Normalization

Fess JSON → `SearchResult` conversion:

```python
def normalize(fess_json: dict) -> SearchResult:
    total = fess_json.get("record_count", 0)
    took_ms = fess_json.get("exec_time", None)
    hits = []
    for e in fess_json.get("data", []):
        hits.append({
            "id": e.get("doc_id") or sha256(e.get("url",""))[:16],
            "title": e.get("title") or e.get("url"),
            "url": e.get("url"),
            "snippet": e.get("content_description") or e.get("digest"),
            "score": e.get("score"),
            "meta": {
                "site": e.get("host"),
                "content_type": e.get("mimetype"),
                "updated_at": e.get("last_modified"),
            }
        })
    return {"total": total, "hits": hits, "took_ms": took_ms,
            "page": query.page or 1, "size": query.size or 5}
```

> `snippet` may contain HTML fragments. **UI must sanitize** (DOMPurify).

### 4.4 HTTP Design
- Client: `httpx.AsyncClient(timeout=FESS_TIMEOUT_MS)`
- Retry: **1 exponential backoff** for `5xx` and `connect/read timeout`
- Headers: `User-Agent: intaste/<version>`, transparent `X-Request-Id`
- Exception mapping on failure:
  - Connection: `FessUnavailableError` → API: `UPSTREAM_FESS_ERROR`
  - Timeout: `FessTimeoutError` → API: `TIMEOUT`
  - JSON conversion failure: `FessBadResponseError` → API: `UPSTREAM_FESS_ERROR`

### 4.5 Paging
- Maintain `page` (1-origin) and `size`, UI primarily based on single top-N results.
- Reserve room to return `next_token` for future extension.

---

## 5. Implementation Skeleton

```python
# app/core/search_provider/fess.py
from .base import SearchProvider
from pydantic import BaseModel
import httpx, hashlib

class SearchQuery(BaseModel):
    q: str
    page: int | None = 1
    size: int | None = 5
    sort: str | None = "score"
    language: str | None = None
    filters: dict | None = None
    timeout_ms: int | None = None

class FessSearchProvider(SearchProvider):
    def __init__(self, base_url: str, timeout_ms: int):
        self.base_url = base_url.rstrip('/')
        self.timeout_ms = timeout_ms

    async def search(self, query: SearchQuery) -> dict:
        start = max(0, ((query.page or 1) - 1) * (query.size or 5))
        params = {"q": query.q, "start": start, "num": query.size or 5}
        if query.sort == "date_desc":
            params["sort"] = "last_modified desc"
        elif query.sort == "date_asc":
            params["sort"] = "last_modified asc"
        else:
            params["sort"] = "score"
        # filters example
        if query.filters:
            if site := query.filters.get("site"):
                params["site"] = site
            if mt := query.filters.get("mimetype"):
                params["mimetype"] = mt
        async with httpx.AsyncClient(timeout=query.timeout_ms or self.timeout_ms) as client:
            url = f"{self.base_url}/api/v1/documents"
            r = await client.get(url, params=params)
            r.raise_for_status()
            raw = r.json()
        # Normalization
        hits = []
        for e in raw.get("data", []):
            hid = e.get("doc_id") or hashlib.sha256((e.get("url") or "").encode()).hexdigest()[:16]
            hits.append({
                "id": hid,
                "title": e.get("title") or e.get("url"),
                "url": e.get("url"),
                "snippet": e.get("content_description") or e.get("digest"),
                "score": e.get("score"),
                "meta": {
                    "site": e.get("host"),
                    "content_type": e.get("mimetype"),
                    "updated_at": e.get("last_modified"),
                },
            })
        return {
            "total": raw.get("record_count", 0),
            "hits": hits,
            "took_ms": raw.get("exec_time"),
            "page": query.page or 1,
            "size": query.size or 5,
        }

    async def health(self):
        try:
            async with httpx.AsyncClient(timeout=2.0) as c:
                r = await c.get(f"{self.base_url}/api/v1/health")
                data = r.json()
                health_data = data.get("data", {})
                status = health_data.get("status", "unknown")
                is_healthy = status == "green" and not health_data.get("timed_out", False)
                return (is_healthy, {"status": status})
        except Exception as e:
            return (False, {"error": str(e)})
```

---

## 6. Error Conventions (Propagation to API Layer)

| Event | Provider Exception | API Error Code |
|---|---|---|
| Fess 5xx | `FessUnavailableError` | `UPSTREAM_FESS_ERROR` (502/503) |
| Timeout | `FessTimeoutError` | `TIMEOUT` (504) |
| 4xx (400/401/403) | `FessBadRequest` | `BAD_REQUEST` (400/403) |
| Invalid JSON | `FessBadResponseError` | `UPSTREAM_FESS_ERROR` |

- Assist service maintains **fallback strategy** (includes UI suggestions for 0 citations)

---

## 7. Security & Privacy

- URL/title, etc. **hash before log output** (sha256 first 12 characters)
- Transparently pass `X-Request-Id` for audit and trace correlation
- Fixed `User-Agent`, cooperate with Fess rate control

---

## 8. Configuration & Tuning

| Item | Default | Adjustment Points |
|---|---:|---|
| `FESS_TIMEOUT_MS` | 2000 | 1000–3000 based on network environment |
| `size` | 5 | Trade-off with UI display and LLM synthesis time |
| `sort` | `score` | `date_desc` also effective for internal enterprise |

---

## 9. Testing (Provider Perspective)

- Normal: Representative response → normalization mapping as expected (title/url/snippet/meta)
- Exception: 5xx/timeout/invalid JSON → exception conversion → map to appropriate code in API
- Load: p95 < 300ms on 100 consecutive requests (local)

---

## 10. Future Extensions (Compatibility Policy)

### 10.1 MCP Passthrough
- `FessMCPProvider`: Tool calls via `fess-webapp-mcp` plugin. Intaste **conversation control only**
- Additional interface example: `tools(query) -> citations`. Normalize return value to `SearchResult`

### 10.2 External Search Providers
- Can be replaced by implementing `SearchProvider`. Example: REST search API, internal DMS, etc.
- **No breaking changes**: Extend additional fields in `meta` (`SearchHit` immutable)

---

## 11. Implementation Location

- Abstract: `intaste-api/app/core/search_provider/base.py`
- Fess: `intaste-api/app/core/search_provider/fess.py`
- Dependency injection: Selected via environment variable at `assist` service startup (initial version fixed to `fess`)

---

**End of Document**
