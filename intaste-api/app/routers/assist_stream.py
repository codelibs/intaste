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
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.core.security.auth import verify_api_token
from app.i18n import _
from app.schemas.assist import AssistQueryRequest
from app.services.assist import AssistService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assist", tags=["assist-stream"])


def get_assist_service() -> AssistService:
    """Dependency to get AssistService instance."""
    from app.main import assist_service

    if assist_service is None:
        raise RuntimeError("AssistService not initialized")
    return assist_service


async def format_sse(event: str, data: dict[str, Any]) -> str:
    """Format Server-Sent Event message."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def stream_assist_response(
    request: AssistQueryRequest,
    service: AssistService,
) -> AsyncGenerator[str]:
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
    request_options["session_id"] = session_id

    # Add query_history if provided
    if request.query_history:
        request_options["query_history"] = request.query_history

    logger.debug(
        f"[{session_id}] Streaming query started: query={request.query!r}, options={request_options}, query_history_count={len(request.query_history) if request.query_history else 0}"
    )

    try:
        # Get language from options
        language = request_options.get("language", "en")

        # Send start event
        event_count += 1
        start_event = await format_sse(
            "start",
            {"message": _("Processing query...", language=language), "query": request.query},
        )
        logger.debug(
            f"[{session_id}] Streaming event #{event_count}: type=start, size={len(start_event)} bytes"
        )
        yield start_event

        # Step 1 & 2: Intent extraction and search via SearchAgent
        logger.debug(f"[{session_id}] Starting SearchAgent stream")

        intent_data = None
        citations_data = None

        async for event in service.search_agent.search_stream(
            query=request.query,
            options=request_options,
        ):
            if event.type == "status":
                status_data = event.status_data
                if status_data:  # Type guard for mypy
                    event_count += 1

                    status_event = await format_sse(
                        "status",
                        {
                            "phase": status_data.phase,
                        },
                    )
                    logger.debug(
                        f"[{session_id}] Streaming event #{event_count}: type=status, "
                        f"phase={status_data.phase}"
                    )
                    yield status_event

            elif event.type == "intent":
                intent_data = event.intent_data
                if intent_data:  # Type guard for mypy
                    event_count += 1

                    intent_event = await format_sse(
                        "intent",
                        {
                            "normalized_query": intent_data.normalized_query,
                            "filters": intent_data.filters,
                            "followups": intent_data.followups,
                            "timing_ms": intent_data.timing_ms,
                        },
                    )
                    logger.debug(
                        f"[{session_id}] Streaming event #{event_count}: type=intent, "
                        f"size={len(intent_event)} bytes"
                    )
                    yield intent_event

            elif event.type == "citations":
                citations_data = event.citations_data
                if citations_data:  # Type guard for mypy
                    # Format citations for SSE
                    citations = [
                        {
                            "id": idx + 1,
                            "title": hit.title,
                            "snippet": hit.snippet,
                            "url": hit.url,
                            "score": hit.score,
                            "relevance_score": hit.relevance_score,
                            "meta": hit.meta,
                        }
                        for idx, hit in enumerate(citations_data.hits)
                    ]

                    event_count += 1
                    citations_event = await format_sse(
                        "citations",
                        {
                            "count": len(citations),
                            "citations": citations,
                            "timing_ms": citations_data.timing_ms,
                        },
                    )
                    logger.debug(
                        f"[{session_id}] Streaming event #{event_count}: type=citations, "
                        f"size={len(citations_event)} bytes, hits={len(citations)}"
                    )
                    yield citations_event

            elif event.type == "relevance":
                relevance_data = event.relevance_data
                if relevance_data:  # Type guard for mypy
                    event_count += 1

                    relevance_event = await format_sse(
                        "relevance",
                        {
                            "evaluated_count": relevance_data.evaluated_count,
                            "max_score": relevance_data.max_score,
                            "timing_ms": relevance_data.timing_ms,
                        },
                    )
                    logger.debug(
                        f"[{session_id}] Streaming event #{event_count}: type=relevance, "
                        f"max_score={relevance_data.max_score:.2f}"
                    )
                    yield relevance_event

            elif event.type == "retry":
                retry_data = event.retry_data
                if retry_data:  # Type guard for mypy
                    event_count += 1

                    retry_event = await format_sse(
                        "retry",
                        {
                            "attempt": retry_data.attempt,
                            "reason": retry_data.reason,
                            "previous_max_score": retry_data.previous_max_score,
                        },
                    )
                    logger.debug(
                        f"[{session_id}] Streaming event #{event_count}: type=retry, "
                        f"attempt={retry_data.attempt}"
                    )
                    yield retry_event

        # Validate we received all necessary events
        if not intent_data:
            raise RuntimeError("SearchAgent did not emit intent event")
        if not citations_data:
            raise RuntimeError("SearchAgent did not emit citations event")

        logger.debug(
            f"[{session_id}] SearchAgent stream completed: "
            f"intent={intent_data.timing_ms}ms, search={citations_data.timing_ms}ms"
        )

        # Yield status: answer composition starting
        event_count += 1
        compose_status_event = await format_sse("status", {"phase": "compose"})
        logger.debug(f"[{session_id}] Streaming event #{event_count}: type=status, phase=compose")
        yield compose_status_event

        # Step 3: Compose answer with streaming
        logger.debug(f"[{session_id}] Starting answer composition streaming")
        compose_start = time.time()

        # Prepare citation data for LLM (include relevance_score and relevance_reason)
        citations_for_llm = [
            {
                "title": hit.title,
                "snippet": hit.snippet,
                "url": hit.url,
                "relevance_score": hit.relevance_score,
                "relevance_reason": hit.relevance_reason,
            }
            for hit in citations_data.hits
        ]

        logger.debug(f"[{session_id}] Citations data prepared: {len(citations_for_llm)} items")

        # Stream answer chunks
        full_text = ""
        chunk_num = 0
        compose_stream = service.llm_client.compose_stream(
            query=request.query,
            normalized_query=intent_data.normalized_query,
            citations_data=citations_for_llm,
            followups=intent_data.followups,
            language=request_options.get("language", "en"),
            timeout_ms=settings.compose_timeout_ms,
            selected_threshold=settings.intaste_selected_relevance_threshold,
        )
        async for chunk in compose_stream:
            full_text += chunk
            chunk_num += 1
            event_count += 1

            chunk_event = await format_sse("chunk", {"text": chunk})
            logger.debug(
                f"[{session_id}] Streaming event #{event_count}: type=chunk, "
                f"chunk_num={chunk_num}, chunk_length={len(chunk)}, total_length={len(full_text)}"
            )
            yield chunk_event

        compose_ms = int((time.time() - compose_start) * 1000)
        total_ms = int((time.time() - start_time) * 1000)

        logger.debug(
            f"[{session_id}] Composition streaming completed: chunks={chunk_num}, "
            f"total_chars={len(full_text)}, compose_ms={compose_ms}ms"
        )
        logger.debug(f"[{session_id}] Full text preview: {full_text[:200]}")

        # Calculate total LLM time (intent extraction + answer composition)
        llm_ms = intent_data.timing_ms + compose_ms

        logger.debug(
            f"[{session_id}] Total timings: intent={intent_data.timing_ms}ms, "
            f"search={citations_data.timing_ms}ms, compose={compose_ms}ms, "
            f"llm={llm_ms}ms, total={total_ms}ms"
        )

        # Send complete event with summary
        event_count += 1
        complete_event = await format_sse(
            "complete",
            {
                "answer": {
                    "text": full_text,
                    "suggested_questions": intent_data.followups,
                },
                "citations": citations,
                "session": {
                    "id": session_id,
                    "turn": 1,
                },
                "timings": {
                    "llm_ms": llm_ms,
                    "search_ms": citations_data.timing_ms,
                    "total_ms": total_ms,
                    "intent_ms": intent_data.timing_ms,
                    "compose_ms": compose_ms,
                },
            },
        )
        logger.debug(
            f"[{session_id}] Streaming event #{event_count}: type=complete, "
            f"size={len(complete_event)} bytes"
        )
        logger.info(
            f"[{session_id}] Streaming completed: total_events={event_count}, "
            f"total_ms={total_ms}ms, citations={len(citations)}"
        )
        yield complete_event

    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        # Log detailed error for debugging (server-side only)
        logger.error(f"[{session_id}] Streaming error after {elapsed_ms}ms: {e}", exc_info=True)
        logger.debug(
            f"[{session_id}] Streaming error context: query={request.query!r}, "
            f"events_sent={event_count}, error_type={type(e).__name__}"
        )

        # Map internal exceptions to user-friendly error codes
        # Do NOT expose internal error messages to clients
        error_code = "PROCESSING_ERROR"
        error_message = "An error occurred while processing your request"

        if isinstance(e, TimeoutError):
            error_code = "TIMEOUT"
            error_message = "Request timed out. Please try again."
        elif isinstance(e, RuntimeError):
            error_code = "SERVICE_ERROR"
            error_message = "Service temporarily unavailable. Please try again later."

        event_count += 1
        error_event = await format_sse(
            "error",
            {
                "code": error_code,
                "message": error_message,
            },
        )
        logger.debug(
            f"[{session_id}] Streaming event #{event_count}: type=error, " f"code={error_code}"
        )
        yield error_event


@router.post("/query")
async def stream_query(
    request: AssistQueryRequest,
    service: AssistService = Depends(get_assist_service),
    _token: str = Depends(verify_api_token),
) -> StreamingResponse:
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
    logger.debug(f"[{session_id}] POST /assist/query started: query={request.query!r}")

    return StreamingResponse(
        stream_assist_response(request, service),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
