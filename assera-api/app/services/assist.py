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
Assisted search service orchestrating SearchAgent → Compose flow.
"""

import logging
import time
import uuid
from typing import Any

from ..core.config import settings
from ..core.llm.base import LLMClient
from ..core.search_agent.base import SearchAgent
from ..schemas.assist import Answer, AssistQueryResponse, Citation, Session, Timings

logger = logging.getLogger(__name__)


class AssistService:
    """
    Core service for assisted search combining SearchAgent and LLM.
    """

    def __init__(self, search_agent: SearchAgent, llm_client: LLMClient):
        self.search_agent = search_agent
        self.llm_client = llm_client
        # In-memory session storage (TODO: Use Redis/database for production)
        self.sessions: dict[str, dict[str, Any]] = {}

    async def query(
        self,
        query: str,
        session_id: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> AssistQueryResponse:
        """
        Execute assisted search query.

        Flow:
        1. Search execution via SearchAgent (intent + search)
        2. Answer composition (LLM)
        3. Assemble response with citations

        Args:
            query: Natural language query
            session_id: Optional session ID for conversation tracking
            options: Optional parameters (max_results, language, filters, timeout_ms)

        Returns:
            AssistQueryResponse with answer, citations, and metadata
        """
        start_time = time.time()
        options = options or {}

        # Get or create session
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.debug(f"New session created: {session_id}")
        else:
            logger.debug(f"Using existing session: {session_id}")

        if session_id not in self.sessions:
            self.sessions[session_id] = {"turn": 0, "history": []}
            logger.debug(f"Initialized session storage for: {session_id}")

        self.sessions[session_id]["turn"] += 1
        turn = self.sessions[session_id]["turn"]
        logger.debug(f"[{session_id}:{turn}] Session turn incremented")
        logger.debug(f"[{session_id}:{turn}] Request options: {options}")

        # Add session_id to options for logging in SearchAgent
        options_with_session = {**options, "session_id": session_id}

        # Step 1: Execute search via SearchAgent (intent + search)
        logger.info(f"[{session_id}:{turn}] Starting search via SearchAgent")
        search_result = await self.search_agent.search(query, options_with_session)

        logger.info(
            f"[{session_id}:{turn}] SearchAgent completed: {len(search_result.hits)} hits, "
            f"intent={search_result.timings.intent_ms}ms, search={search_result.timings.search_ms}ms"
        )
        logger.debug(
            f"[{session_id}:{turn}] SearchAgent result: normalized_query={search_result.normalized_query!r}, "
            f"followups={search_result.followups}, ambiguity={search_result.ambiguity}"
        )

        # Step 2: Answer composition
        answer: Answer
        compose_ms = 0

        if search_result.hits:
            logger.info(f"[{session_id}:{turn}] Composing answer")
            logger.debug(
                f"[{session_id}:{turn}] Compose input: citations_count={len(search_result.hits)}, "
                f"followups={search_result.followups}, timeout={settings.compose_timeout_ms}ms"
            )

            compose_start = time.time()

            try:
                citations_data = [hit.model_dump() for hit in search_result.hits]
                logger.debug(
                    f"[{session_id}:{turn}] Citations data prepared: {len(citations_data)} items"
                )

                compose = await self.llm_client.compose(
                    query=query,
                    normalized_query=search_result.normalized_query,
                    citations_data=citations_data,
                    followups=search_result.followups,
                    timeout_ms=settings.compose_timeout_ms,
                )
                compose_ms = int((time.time() - compose_start) * 1000)

                answer = Answer(
                    text=compose.text,
                    suggested_questions=compose.suggested_questions,
                )
                logger.info(f"[{session_id}:{turn}] Answer composed ({compose_ms}ms)")
                logger.debug(
                    f"[{session_id}:{turn}] Answer details: text_length={len(answer.text)}, "
                    f"text={answer.text!r}, suggested_questions={answer.suggested_questions}"
                )

            except (TimeoutError, Exception) as e:
                compose_ms = int((time.time() - compose_start) * 1000)
                logger.warning(f"[{session_id}:{turn}] Compose failed after {compose_ms}ms: {e}")
                logger.debug(
                    f"[{session_id}:{turn}] Compose error: {type(e).__name__}, "
                    f"citations_count={len(search_result.hits)}"
                )

                # Fallback: generic guidance
                answer = Answer(
                    text="Results are displayed. Please review the sources for details.",
                    suggested_questions=search_result.followups[:3],
                )
                # Add notice if not already present
                if not search_result.notice:
                    from ..schemas.assist import Notice

                    search_result.notice = Notice(
                        fallback=True,
                        reason="LLM_TIMEOUT" if isinstance(e, TimeoutError) else "BAD_LLM_OUTPUT",
                    )
                logger.debug(
                    f"[{session_id}:{turn}] Using fallback answer: {answer}, "
                    f"notice={search_result.notice}"
                )
        else:
            # No search results
            logger.info(f"[{session_id}:{turn}] No search results, skipping answer composition")
            answer = Answer(
                text="No results found. Try different keywords or check spelling.",
                suggested_questions=["Try a broader search term", "Check document filters"],
            )
            logger.debug(f"[{session_id}:{turn}] Empty results answer: {answer}")

        # Step 3: Assemble citations
        logger.debug(f"[{session_id}:{turn}] Assembling citations: {len(search_result.hits)} hits")

        citations: list[Citation] = []
        for idx, hit in enumerate(search_result.hits, start=1):
            citation = Citation(
                id=idx,
                title=hit.title,
                snippet=hit.snippet,
                url=hit.url,
                score=hit.score,
                meta=hit.meta,
            )
            citations.append(citation)
            if logger.isEnabledFor(logging.DEBUG) and idx <= 3:  # Log first 3 citations
                logger.debug(
                    f"[{session_id}:{turn}] Citation #{idx}: id={citation.id}, "
                    f"title={citation.title[:50]}, score={citation.score}"
                )

        # Calculate total time
        total_ms = int((time.time() - start_time) * 1000)

        logger.debug(
            f"[{session_id}:{turn}] Timings: intent={search_result.timings.intent_ms}ms, "
            f"search={search_result.timings.search_ms}ms, compose={compose_ms}ms, total={total_ms}ms"
        )

        # Store in session history
        history_entry = {
            "turn": turn,
            "query": query,
            "normalized_query": search_result.normalized_query,
            "citations_count": len(citations),
        }
        self.sessions[session_id]["history"].append(history_entry)
        logger.debug(f"[{session_id}:{turn}] Session history updated: {history_entry}")
        logger.debug(
            f"[{session_id}:{turn}] Total history entries: {len(self.sessions[session_id]['history'])}"
        )

        response = AssistQueryResponse(
            answer=answer,
            citations=citations,
            session=Session(id=session_id, turn=turn),
            timings=Timings(
                llm_ms=search_result.timings.intent_ms + compose_ms,
                search_ms=search_result.timings.search_ms,
                total_ms=total_ms,
            ),
            notice=search_result.notice,
        )

        logger.info(
            f"[{session_id}:{turn}] Query completed: total_ms={total_ms}, "
            f"citations={len(citations)}, notice={'Yes' if search_result.notice else 'No'}"
        )
        logger.debug(
            f"[{session_id}:{turn}] Final response: answer_length={len(answer.text)}, "
            f"citations_count={len(citations)}, "
            f"suggested_questions_count={len(answer.suggested_questions)}"
        )

        return response
