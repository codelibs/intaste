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
Streaming assist endpoints using Server-Sent Events (SSE).
"""

import json
import logging
import time
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.core.security.auth import verify_api_token
from app.schemas.assist import AssistQueryRequest
from app.services.assist import AssistService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assist", tags=["assist-stream"])


def get_assist_service() -> AssistService:
    """Dependency to get AssistService instance."""
    from app.main import assist_service

    return assist_service


async def format_sse(event: str, data: dict) -> str:
    """Format Server-Sent Event message."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def stream_assist_response(
    request: AssistQueryRequest,
    service: AssistService,
) -> AsyncGenerator[str, None]:
    """
    Generate streaming response for assist query.

    Events sent:
    - start: Query processing started
    - intent: Intent extraction completed
    - citations: Search results available
    - chunk: Answer text chunk
    - complete: Processing complete with full response
    - error: Error occurred
    """
    start_time = time.time()
    session_id = request.session_id or "new"
    event_count = 0

    # Safely get options
    request_options = request.options or {}

    logger.debug(f"[{session_id}] Streaming query started: query={request.query!r}, options={request_options}")

    try:
        # Send start event
        event_count += 1
        start_event = await format_sse("start", {
            "message": "Processing query...",
            "query": request.query
        })
        logger.debug(f"[{session_id}] Streaming event #{event_count}: type=start, size={len(start_event)} bytes")
        yield start_event

        # 1. Intent extraction (non-streaming)
        logger.debug(f"[{session_id}] Starting intent extraction for streaming")
        intent_start = time.time()
        intent_result = None
        intent_ms = 0
        normalized_query = request.query.strip()

        try:
            from app.main import llm_client
            intent_result = await llm_client.intent(
                query=request.query,
                language=request_options.get("language"),
                filters=request_options.get("filters"),
                timeout_ms=settings.intent_timeout_ms,
            )
            intent_ms = int((time.time() - intent_start) * 1000)

            logger.debug(f"[{session_id}] Intent extraction completed: {intent_ms}ms, normalized_query={intent_result.normalized_query!r}")

            event_count += 1
            intent_event = await format_sse("intent", {
                "normalized_query": intent_result.normalized_query,
                "filters": intent_result.filters,
                "timing_ms": intent_ms,
            })
            logger.debug(f"[{session_id}] Streaming event #{event_count}: type=intent, size={len(intent_event)} bytes")
            yield intent_event

        except Exception as e:
            intent_ms = int((time.time() - intent_start) * 1000)
            logger.warning(f"[{session_id}] Intent extraction failed after {intent_ms}ms: {e}")
            logger.debug(f"[{session_id}] Intent error type: {type(e).__name__}, details: {str(e)}")
            intent_result = None
            logger.debug(f"[{session_id}] Using fallback normalized_query: {normalized_query!r}")

        # 2. Search (non-streaming)
        logger.debug(f"[{session_id}] Starting search for streaming")
        search_start = time.time()
        from app.main import search_provider
        from app.core.search_provider.base import SearchQuery

        # Extract filters safely
        filters = intent_result.filters if (intent_result and intent_result.filters) else request_options.get("filters", {})
        if filters is None:
            filters = {}

        search_query = SearchQuery(
            q=intent_result.normalized_query if intent_result else normalized_query,
            page=1,
            size=request_options.get("max_results", 5),
            language=request_options.get("language", "ja"),
            filters=filters,
        )

        logger.debug(f"[{session_id}] SearchQuery: {search_query}")

        search_result = await search_provider.search(search_query)
        search_ms = int((time.time() - search_start) * 1000)

        logger.debug(f"[{session_id}] Search completed: {search_ms}ms, hits={len(search_result.hits)}, total={search_result.total}")

        # Format citations
        citations = [
            {
                "id": idx + 1,
                "title": hit.title,
                "snippet": hit.snippet,
                "url": hit.url,
                "score": hit.score,
                "meta": hit.meta,
            }
            for idx, hit in enumerate(search_result.hits)
        ]

        logger.debug(f"[{session_id}] Formatted {len(citations)} citations")

        event_count += 1
        citations_event = await format_sse("citations", {
            "count": len(citations),
            "citations": citations,
            "timing_ms": search_ms,
        })
        logger.debug(f"[{session_id}] Streaming event #{event_count}: type=citations, size={len(citations_event)} bytes")
        yield citations_event

        # 3. Compose answer with streaming
        logger.debug(f"[{session_id}] Starting answer composition streaming")
        compose_start = time.time()

        # Prepare citation data for LLM
        citations_data = [
            {
                "title": hit.title,
                "snippet": hit.snippet,
                "url": hit.url,
            }
            for hit in search_result.hits
        ]

        logger.debug(f"[{session_id}] Citations data prepared: {len(citations_data)} items")

        # Stream answer chunks
        full_text = ""
        chunk_num = 0
        async for chunk in llm_client.compose_stream(
            query=request.query,
            normalized_query=intent_result.normalized_query if intent_result else normalized_query,
            citations_data=citations_data,
            followups=intent_result.followups if intent_result else None,
            timeout_ms=settings.compose_timeout_ms,
        ):
            full_text += chunk
            chunk_num += 1
            event_count += 1

            chunk_event = await format_sse("chunk", {"text": chunk})
            logger.debug(f"[{session_id}] Streaming event #{event_count}: type=chunk, chunk_num={chunk_num}, chunk_length={len(chunk)}, total_length={len(full_text)}")
            yield chunk_event

        compose_ms = int((time.time() - compose_start) * 1000)
        total_ms = int((time.time() - start_time) * 1000)

        logger.debug(f"[{session_id}] Composition streaming completed: chunks={chunk_num}, total_chars={len(full_text)}, compose_ms={compose_ms}ms")
        logger.debug(f"[{session_id}] Full text preview: {full_text[:200]}")

        # Validate and clean full_text to handle malformed LLM output
        # LLM might return JSON-encoded text instead of plain text
        cleaned_text = full_text
        if full_text.startswith('{'):
            try:
                # Try to parse as JSON
                parsed = json.loads(full_text)
                if isinstance(parsed, dict) and "text" in parsed:
                    logger.warning(f"[{session_id}] Detected malformed streaming output with JSON structure")
                    logger.debug(f"[{session_id}] Malformed full_text: {full_text[:200]}")
                    # Extract the actual text from the JSON
                    cleaned_text = parsed.get("text", full_text)
                    logger.debug(f"[{session_id}] Extracted cleaned text: {cleaned_text[:200]}")
            except (json.JSONDecodeError, ValueError):
                # Not JSON, use as-is
                pass

        logger.debug(f"[{session_id}] Total timings: intent={intent_ms if intent_result else 0}ms, search={search_ms}ms, compose={compose_ms}ms, total={total_ms}ms")

        # Send complete event with summary
        event_count += 1
        complete_event = await format_sse("complete", {
            "answer": {
                "text": cleaned_text,
                "suggested_questions": intent_result.followups if intent_result else [],
            },
            "citations": citations,
            "session": {
                "id": session_id,
                "turn": 1,
            },
            "timings": {
                "intent_ms": intent_ms if intent_result else 0,
                "search_ms": search_ms,
                "compose_ms": compose_ms,
                "total_ms": total_ms,
            },
        })
        logger.debug(f"[{session_id}] Streaming event #{event_count}: type=complete, size={len(complete_event)} bytes")
        logger.info(f"[{session_id}] Streaming completed: total_events={event_count}, total_ms={total_ms}ms, citations={len(citations)}")
        yield complete_event

    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.error(f"[{session_id}] Streaming error after {elapsed_ms}ms: {e}", exc_info=True)
        logger.debug(f"[{session_id}] Streaming error context: query={request.query!r}, events_sent={event_count}, error_type={type(e).__name__}")

        event_count += 1
        error_event = await format_sse("error", {
            "message": str(e),
            "type": type(e).__name__,
        })
        logger.debug(f"[{session_id}] Streaming event #{event_count}: type=error, size={len(error_event)} bytes")
        yield error_event


@router.post("/query/stream")
async def stream_query(
    request: AssistQueryRequest,
    service: AssistService = Depends(get_assist_service),
    _token: str = Depends(verify_api_token),
):
    """
    Stream assisted search results using Server-Sent Events.

    This endpoint provides real-time updates as the query is processed:
    1. Intent extraction
    2. Search execution
    3. Answer composition (streamed)

    Response format: Server-Sent Events (SSE)
    Content-Type: text/event-stream

    Events:
    - start: Query processing started
    - intent: Intent extraction completed
    - citations: Search results available
    - chunk: Answer text chunk (multiple events)
    - complete: Processing finished
    - error: Error occurred
    """
    session_id = request.session_id or "new"
    logger.debug(f"[{session_id}] POST /assist/query/stream started: query={request.query!r}")

    return StreamingResponse(
        stream_assist_response(request, service),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
