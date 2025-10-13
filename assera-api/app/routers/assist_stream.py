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
    request_options["session_id"] = session_id

    logger.debug(
        f"[{session_id}] Streaming query started: query={request.query!r}, options={request_options}"
    )

    try:
        # Send start event
        event_count += 1
        start_event = await format_sse(
            "start", {"message": "Processing query...", "query": request.query}
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
            if event.type == "intent":
                intent_data = event.intent_data
                if intent_data:  # Type guard for mypy
                    event_count += 1

                    intent_event = await format_sse(
                        "intent",
                        {
                            "normalized_query": intent_data.normalized_query,
                            "filters": intent_data.filters,
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

        # Validate we received all necessary events
        if not intent_data:
            raise RuntimeError("SearchAgent did not emit intent event")
        if not citations_data:
            raise RuntimeError("SearchAgent did not emit citations event")

        logger.debug(
            f"[{session_id}] SearchAgent stream completed: "
            f"intent={intent_data.timing_ms}ms, search={citations_data.timing_ms}ms"
        )

        # Step 3: Compose answer with streaming
        logger.debug(f"[{session_id}] Starting answer composition streaming")
        compose_start = time.time()

        # Prepare citation data for LLM
        citations_for_llm = [
            {
                "title": hit.title,
                "snippet": hit.snippet,
                "url": hit.url,
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
            timeout_ms=settings.compose_timeout_ms,
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

        # Validate and clean full_text to handle malformed LLM output
        # LLM might return JSON-encoded text instead of plain text
        cleaned_text = full_text
        if full_text.startswith("{"):
            try:
                # Try to parse as JSON
                parsed = json.loads(full_text)
                if isinstance(parsed, dict) and "text" in parsed:
                    logger.warning(
                        f"[{session_id}] Detected malformed streaming output with JSON structure"
                    )
                    logger.debug(f"[{session_id}] Malformed full_text: {full_text[:200]}")
                    # Extract the actual text from the JSON
                    cleaned_text = parsed.get("text", full_text)
                    logger.debug(f"[{session_id}] Extracted cleaned text: {cleaned_text[:200]}")
            except (json.JSONDecodeError, ValueError):
                # Not JSON, use as-is
                pass

        logger.debug(
            f"[{session_id}] Total timings: intent={intent_data.timing_ms}ms, "
            f"search={citations_data.timing_ms}ms, compose={compose_ms}ms, total={total_ms}ms"
        )

        # Send complete event with summary
        event_count += 1
        complete_event = await format_sse(
            "complete",
            {
                "answer": {
                    "text": cleaned_text,
                    "suggested_questions": intent_data.followups,
                },
                "citations": citations,
                "session": {
                    "id": session_id,
                    "turn": 1,
                },
                "timings": {
                    "intent_ms": intent_data.timing_ms,
                    "search_ms": citations_data.timing_ms,
                    "compose_ms": compose_ms,
                    "total_ms": total_ms,
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
        logger.error(f"[{session_id}] Streaming error after {elapsed_ms}ms: {e}", exc_info=True)
        logger.debug(
            f"[{session_id}] Streaming error context: query={request.query!r}, "
            f"events_sent={event_count}, error_type={type(e).__name__}"
        )

        event_count += 1
        error_event = await format_sse(
            "error",
            {
                "message": str(e),
                "type": type(e).__name__,
            },
        )
        logger.debug(
            f"[{session_id}] Streaming event #{event_count}: type=error, "
            f"size={len(error_event)} bytes"
        )
        yield error_event


@router.post("/query/stream")
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
