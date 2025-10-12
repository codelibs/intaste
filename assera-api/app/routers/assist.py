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
Assist search endpoints.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.security.auth import verify_api_token
from ..schemas.assist import AssistQueryRequest, AssistQueryResponse, FeedbackRequest
from ..services.assist import AssistService

router = APIRouter(prefix="/assist", tags=["assist"])
logger = logging.getLogger(__name__)


def get_assist_service() -> AssistService:
    """Dependency to get AssistService instance."""
    from ..main import assist_service

    if assist_service is None:
        raise RuntimeError("Assist service not initialized")
    return assist_service


@router.post(
    "/query",
    response_model=AssistQueryResponse,
    summary="Execute assisted search query",
    dependencies=[Depends(verify_api_token)],
)
async def query(
    request: AssistQueryRequest,
    assist_service: AssistService = Depends(get_assist_service),
) -> AssistQueryResponse:
    """
    Execute an assisted search query with LLM-enhanced results.

    This endpoint:
    1. Extracts search intent from natural language query (LLM)
    2. Executes search via Fess
    3. Composes a brief answer with citations (LLM)

    Args:
        request: Query request with natural language query and options

    Returns:
        AssistQueryResponse: Answer, citations, session info, and timings

    Raises:
        HTTPException: 400 for validation errors, 504 for timeouts, 502 for upstream errors
    """
    import time

    start_time = time.time()
    session_id = request.session_id or "new"

    logger.debug(f"[{session_id}] POST /assist/query started")
    logger.debug(f"[{session_id}] Request: query={request.query!r}, session_id={request.session_id}, options={request.options}")

    try:
        response = await assist_service.query(
            query=request.query,
            session_id=request.session_id,
            options=request.options,
        )

        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.info(f"[{response.session.id}:{response.session.turn}] POST /assist/query completed: {elapsed_ms}ms, citations={len(response.citations)}")
        logger.debug(f"[{response.session.id}:{response.session.turn}] Response: timings={response.timings}, notice={response.notice}")

        return response

    except TimeoutError as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.error(f"[{session_id}] Query timeout after {elapsed_ms}ms: {e}")
        logger.debug(f"[{session_id}] Timeout details: query={request.query!r}, options={request.options}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={
                "code": "TIMEOUT",
                "message": "Request timeout exceeded",
                "details": {"hint": "Try a simpler query or increase timeout"},
            },
        )
    except RuntimeError as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.error(f"[{session_id}] Upstream error after {elapsed_ms}ms: {e}")
        logger.debug(f"[{session_id}] Upstream error details: query={request.query!r}, error_type={type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": "UPSTREAM_FESS_ERROR",
                "message": "Search provider error",
                "details": {"error": str(e)},
            },
        )
    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.error(f"[{session_id}] Unexpected error in /assist/query after {elapsed_ms}ms: {e}", exc_info=True)
        logger.debug(f"[{session_id}] Error context: query={request.query!r}, session_id={request.session_id}, error_type={type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL",
                "message": "Internal server error",
            },
        )


@router.post(
    "/feedback",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit feedback on a response",
    dependencies=[Depends(verify_api_token)],
)
async def feedback(request: FeedbackRequest) -> dict[str, str]:
    """
    Submit user feedback (thumbs up/down) on an assist response.

    Feedback is logged for quality improvement but not stored in database (initial version).

    Args:
        request: Feedback with session ID, turn, rating, and optional comment

    Returns:
        Status accepted
    """
    logger.info(
        f"Feedback received: session={request.session_id}, "
        f"turn={request.turn}, rating={request.rating}"
    )
    comment_value = repr(request.comment) if hasattr(request, 'comment') else 'N/A'
    logger.debug(f"Feedback details: session={request.session_id}, turn={request.turn}, rating={request.rating}, comment={comment_value}")
    # TODO: Store in database or metrics system
    return {"status": "accepted"}
