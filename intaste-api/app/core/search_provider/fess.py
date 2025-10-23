# Copyright (c) 2025 CodeLibs
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Fess search provider implementation.
"""

import hashlib
import logging
from typing import Any

import httpx

from .base import SearchHit, SearchQuery, SearchResult

logger = logging.getLogger(__name__)


class FessSearchProvider:
    """
    Fess OpenAPI search provider implementation.
    """

    def __init__(self, base_url: str, timeout_ms: int = 2000):
        self.base_url = base_url.rstrip("/")
        self.timeout_ms = timeout_ms
        self.client = httpx.AsyncClient(timeout=timeout_ms / 1000.0)

    async def search(self, query: SearchQuery) -> SearchResult:
        """
        Execute search via Fess OpenAPI and normalize results.
        """
        import time

        logger.debug(
            f"Fess search started: query={query.q!r}, page={query.page}, size={query.size}"
        )
        logger.debug(
            f"Search query details: language={query.language}, sort={query.sort}, filters={query.filters}"
        )

        # Convert page/size to Fess start/num
        start = max(0, (query.page - 1) * query.size)
        params: dict[str, Any] = {
            "q": query.q,
            "start": start,
            "num": query.size,
        }

        # Map sort parameter
        if query.sort == "date_desc":
            params["sort"] = "last_modified.desc"
        elif query.sort == "date_asc":
            params["sort"] = "last_modified.asc"
        else:
            params["sort"] = "score.desc"

        # Apply filters if provided
        if query.filters:
            if site := query.filters.get("site"):
                params["site"] = site
                logger.debug(f"Applied site filter: {site}")
            if mimetype := query.filters.get("mimetype"):
                params["mimetype"] = mimetype
                logger.debug(f"Applied mimetype filter: {mimetype}")
            if updated_after := query.filters.get("updated_after"):
                params["last_modified_from"] = updated_after
                logger.debug(f"Applied updated_after filter: {updated_after}")

        try:
            url = f"{self.base_url}/api/v1/documents"
            timeout = query.timeout_ms / 1000.0 if query.timeout_ms else self.timeout_ms / 1000.0

            logger.debug(f"Fess API call: url={url}, params={params}, timeout={timeout}s")

            start_time = time.time()
            response = await self.client.get(url, params=params, timeout=timeout)
            elapsed_ms = int((time.time() - start_time) * 1000)

            logger.debug(
                f"Fess response received: status={response.status_code}, elapsed={elapsed_ms}ms"
            )

            response.raise_for_status()
            raw_data = response.json()

            logger.debug(f"Fess raw response keys: {list(raw_data.keys())}")
            logger.debug(
                f"Fess response: record_count={raw_data.get('record_count')}, page_count={raw_data.get('page_count')}, exec_time={raw_data.get('exec_time')}s"
            )
            logger.debug(f"Fess returned {len(raw_data.get('data', []))} documents")

            if logger.isEnabledFor(logging.DEBUG) and raw_data.get("data"):
                for idx, doc in enumerate(raw_data["data"][:3], 1):  # Log first 3 documents
                    logger.debug(
                        f"Fess doc #{idx}: id={doc.get('doc_id') or doc.get('id')}, title={doc.get('title', 'N/A')[:50]}, url={doc.get('url', 'N/A')[:80]}, score={doc.get('score')}"
                    )

            result = self._normalize_response(raw_data, query)
            logger.debug(
                f"Fess search normalized: total={result.total}, hits={len(result.hits)}, took={result.took_ms}ms"
            )

            return result

        except httpx.TimeoutException as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Fess search timeout after {elapsed_ms}ms: {e}")
            logger.debug(
                f"Timeout config: requested={timeout}s, elapsed={elapsed_ms}ms, query={query.q!r}"
            )
            raise TimeoutError(f"Fess search timeout after {timeout}s") from e
        except httpx.HTTPStatusError as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"Fess HTTP error: status={e.response.status_code}, elapsed={elapsed_ms}ms"
            )
            logger.debug(f"Fess error response: {e.response.text[:500]}")
            logger.debug(f"Fess request: url={url}, params={params}")
            raise RuntimeError(f"Fess returned {e.response.status_code}") from e
        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000) if "start_time" in locals() else 0
            logger.error(f"Fess search error after {elapsed_ms}ms: {e}")
            logger.debug(
                f"Fess error details: type={type(e).__name__}, query={query.q!r}, params={params}"
            )
            raise

    def _normalize_response(self, raw_data: dict[str, Any], query: SearchQuery) -> SearchResult:
        """
        Normalize Fess JSON response to SearchResult.
        """
        logger.debug(f"Normalizing Fess response: raw_data_keys={list(raw_data.keys())}")

        # Fess API v1 returns flat structure with top-level fields
        total = raw_data.get("record_count", 0)
        # Convert exec_time from seconds (float) to milliseconds (int)
        took_ms = (
            int(raw_data["exec_time"] * 1000) if raw_data.get("exec_time") is not None else None
        )
        results = raw_data.get("data", [])

        logger.debug(f"Normalizing {len(results)} documents: total={total}, took_ms={took_ms}")

        hits: list[SearchHit] = []
        for idx, doc in enumerate(results, start=1):
            url = doc.get("url", "")

            # Priority: 1. Fess doc_id, 2. id field, 3. URL hash, 4. stable fallback
            doc_id = (
                doc.get("doc_id")
                or doc.get("id")
                or (hashlib.sha256(url.encode()).hexdigest()[:16] if url else None)
                or f"unknown-{hashlib.sha256(str(doc).encode()).hexdigest()[:16]}"
            )

            # Log when using fallbacks (helps detect API issues)
            if not doc.get("doc_id") and not doc.get("id"):
                if url:
                    logger.debug(f"Using URL hash for document ID: {doc_id}")
                else:
                    logger.warning(
                        f"Document missing doc_id, id, and url. Using doc hash: {doc_id}"
                    )

            hit = SearchHit(
                id=doc_id,
                title=doc.get("title") or doc.get("url", f"Document {idx}"),
                url=url,
                snippet=doc.get("content_description") or doc.get("digest"),
                score=doc.get("score"),
                meta={
                    "site": doc.get("host"),
                    "content_type": doc.get("mimetype"),
                    "updated_at": doc.get("last_modified"),
                },
            )
            hits.append(hit)

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    f"Normalized hit #{idx}: id={hit.id}, title={hit.title[:50]}, score={hit.score}, url={hit.url[:80]}"
                )
                logger.debug(f"  snippet_length={len(hit.snippet or '')}, meta={hit.meta}")

        result = SearchResult(
            total=total,
            hits=hits,
            took_ms=took_ms,
            page=query.page,
            size=query.size,
        )

        logger.debug(
            f"Normalization complete: SearchResult(total={result.total}, hits_count={len(result.hits)}, took_ms={result.took_ms}, page={result.page}, size={result.size})"
        )

        return result

    async def health(self) -> tuple[bool, dict[str, Any]]:
        """
        Check Fess health status.
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/health", timeout=2.0)
            response.raise_for_status()
            data = response.json()
            health_data = data.get("data", {})
            status = health_data.get("status", "unknown")
            is_healthy = status == "green" and not health_data.get("timed_out", False)
            return (
                is_healthy,
                {"status": status, "timed_out": health_data.get("timed_out", False)},
            )
        except Exception as e:
            return (False, {"error": str(e)})

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()
