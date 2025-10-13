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
Assisted search service orchestrating Intent → Search → Compose flow.
"""

import logging
import time
import uuid
from typing import Any

from ..core.config import settings
from ..core.llm.base import IntentOutput, LLMClient
from ..core.search_provider.base import SearchProvider, SearchQuery
from ..schemas.assist import Answer, AssistQueryResponse, Citation, Notice, Session, Timings

logger = logging.getLogger(__name__)


class AssistService:
    """
    Core service for assisted search combining LLM and search provider.
    """

    def __init__(self, search_provider: SearchProvider, llm_client: LLMClient):
        self.search_provider = search_provider
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
        1. Intent extraction (LLM)
        2. Search execution (Search Provider)
        3. Answer composition (LLM)
        4. Assemble response with citations

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

        # Initialize timings
        intent_ms = 0
        search_ms = 0
        compose_ms = 0
        notice: Notice | None = None

        # Step 1: Intent extraction
        logger.info(f"[{session_id}:{turn}] Starting intent extraction")
        logger.debug(
            f"[{session_id}:{turn}] Intent input: query={query!r}, language={options.get('language', 'ja')}, filters={options.get('filters')}, timeout={settings.intent_timeout_ms}ms"
        )

        intent_start = time.time()

        try:
            intent = await self.llm_client.intent(
                query=query,
                language=options.get("language", "ja"),
                filters=options.get("filters"),
                timeout_ms=settings.intent_timeout_ms,
            )
            intent_ms = int((time.time() - intent_start) * 1000)
            logger.info(
                f"[{session_id}:{turn}] Intent extracted: {intent.normalized_query} "
                f"(ambiguity: {intent.ambiguity}, {intent_ms}ms)"
            )
            logger.debug(
                f"[{session_id}:{turn}] Intent details: normalized_query={intent.normalized_query!r}, filters={intent.filters}, followups={intent.followups}, ambiguity={intent.ambiguity}"
            )

        except (TimeoutError, Exception) as e:
            intent_ms = int((time.time() - intent_start) * 1000)
            logger.warning(
                f"[{session_id}:{turn}] Intent extraction failed after {intent_ms}ms: {e}"
            )
            logger.debug(
                f"[{session_id}:{turn}] Intent error type: {type(e).__name__}, details: {str(e)}"
            )

            # Fallback: use original query
            intent = IntentOutput(
                normalized_query=query.strip(),
                filters=options.get("filters"),
                followups=[],
                ambiguity="medium",
            )
            notice = Notice(
                fallback=True,
                reason="LLM_TIMEOUT" if isinstance(e, TimeoutError) else "LLM_UNAVAILABLE",
            )
            logger.debug(f"[{session_id}:{turn}] Using fallback intent: {intent}, notice={notice}")

        # Step 2: Search execution
        logger.info(f"[{session_id}:{turn}] Executing search")
        logger.debug(
            f"[{session_id}:{turn}] Search input: normalized_query={intent.normalized_query!r}, max_results={options.get('max_results', 5)}, filters={intent.filters or options.get('filters')}"
        )

        search_start = time.time()

        try:
            search_query = SearchQuery(
                q=intent.normalized_query,
                page=1,
                size=options.get("max_results", 5),
                language=options.get("language", "ja"),
                filters=intent.filters or options.get("filters"),
                timeout_ms=settings.search_timeout_ms,
            )
            logger.debug(f"[{session_id}:{turn}] SearchQuery created: {search_query}")

            search_result = await self.search_provider.search(search_query)
            search_ms = int((time.time() - search_start) * 1000)
            logger.info(
                f"[{session_id}:{turn}] Search completed: {len(search_result.hits)} hits "
                f"(total: {search_result.total}, {search_ms}ms)"
            )
            logger.debug(
                f"[{session_id}:{turn}] Search result details: total={search_result.total}, hits_count={len(search_result.hits)}, took_ms={search_result.took_ms}, page={search_result.page}, size={search_result.size}"
            )

            if logger.isEnabledFor(logging.DEBUG) and search_result.hits:
                for idx, hit in enumerate(search_result.hits[:3], 1):  # Log first 3 hits
                    logger.debug(
                        f"[{session_id}:{turn}] Hit #{idx}: id={hit.id}, title={hit.title[:50]}, score={hit.score}, url={hit.url[:80]}"
                    )

        except (TimeoutError, Exception) as e:
            search_ms = int((time.time() - search_start) * 1000)
            logger.error(f"[{session_id}:{turn}] Search failed after {search_ms}ms: {e}")
            logger.debug(
                f"[{session_id}:{turn}] Search error type: {type(e).__name__}, query={intent.normalized_query!r}, filters={intent.filters}"
            )
            # Return error - search is critical
            raise RuntimeError(f"Search provider error: {e}") from e

        # Step 3: Answer composition
        answer: Answer
        if search_result.hits:
            logger.info(f"[{session_id}:{turn}] Composing answer")
            logger.debug(
                f"[{session_id}:{turn}] Compose input: citations_count={len(search_result.hits)}, followups={intent.followups}, timeout={settings.compose_timeout_ms}ms"
            )

            compose_start = time.time()

            try:
                citations_data = [hit.model_dump() for hit in search_result.hits]
                logger.debug(
                    f"[{session_id}:{turn}] Citations data prepared: {len(citations_data)} items"
                )

                compose = await self.llm_client.compose(
                    query=query,
                    normalized_query=intent.normalized_query,
                    citations_data=citations_data,
                    followups=intent.followups,
                    timeout_ms=settings.compose_timeout_ms,
                )
                compose_ms = int((time.time() - compose_start) * 1000)

                answer = Answer(
                    text=compose.text,
                    suggested_questions=compose.suggested_questions,
                )
                logger.info(f"[{session_id}:{turn}] Answer composed ({compose_ms}ms)")
                logger.debug(
                    f"[{session_id}:{turn}] Answer details: text_length={len(answer.text)}, text={answer.text!r}, suggested_questions={answer.suggested_questions}"
                )

            except (TimeoutError, Exception) as e:
                compose_ms = int((time.time() - compose_start) * 1000)
                logger.warning(f"[{session_id}:{turn}] Compose failed after {compose_ms}ms: {e}")
                logger.debug(
                    f"[{session_id}:{turn}] Compose error type: {type(e).__name__}, citations_count={len(search_result.hits)}"
                )

                # Fallback: generic guidance
                answer = Answer(
                    text="Results are displayed. Please review the sources for details.",
                    suggested_questions=intent.followups[:3],
                )
                if not notice:
                    notice = Notice(
                        fallback=True,
                        reason="LLM_TIMEOUT" if isinstance(e, TimeoutError) else "BAD_LLM_OUTPUT",
                    )
                logger.debug(
                    f"[{session_id}:{turn}] Using fallback answer: {answer}, notice={notice}"
                )
        else:
            # No search results
            logger.info(f"[{session_id}:{turn}] No search results, skipping answer composition")
            answer = Answer(
                text="No results found. Try different keywords or check spelling.",
                suggested_questions=["Try a broader search term", "Check document filters"],
            )
            logger.debug(f"[{session_id}:{turn}] Empty results answer: {answer}")

        # Step 4: Assemble citations
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
                    f"[{session_id}:{turn}] Citation #{idx}: id={citation.id}, title={citation.title[:50]}, score={citation.score}"
                )

        # Calculate total time
        total_ms = int((time.time() - start_time) * 1000)

        logger.debug(
            f"[{session_id}:{turn}] Timings: intent={intent_ms}ms, search={search_ms}ms, compose={compose_ms}ms, total={total_ms}ms"
        )

        # Store in session history
        history_entry = {
            "turn": turn,
            "query": query,
            "normalized_query": intent.normalized_query,
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
            timings=Timings(llm_ms=intent_ms + compose_ms, search_ms=search_ms, total_ms=total_ms),
            notice=notice,
        )

        logger.info(
            f"[{session_id}:{turn}] Query completed: total_ms={total_ms}, citations={len(citations)}, notice={'Yes' if notice else 'No'}"
        )
        logger.debug(
            f"[{session_id}:{turn}] Final response: answer_length={len(answer.text)}, citations_count={len(citations)}, suggested_questions_count={len(answer.suggested_questions)}"
        )

        return response
