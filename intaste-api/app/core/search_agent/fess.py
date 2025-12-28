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
Fess search agent implementation.

This agent uses LLM for intent extraction and Fess for search execution.
"""

import asyncio
import logging
import time
from collections.abc import AsyncGenerator
from typing import Any

from ..llm.base import IntentOutput, LLMClient
from ..llm.prompts import (
    IntentParams,
    RelevanceParams,
    RetryIntentNoResultsParams,
    RetryIntentParams,
    get_registry,
)
from ..search_provider.base import SearchHit, SearchProvider, SearchQuery
from .base import (
    BaseSearchAgent,
    CitationsEventData,
    IntentEventData,
    SearchEvent,
)

logger = logging.getLogger(__name__)


class FessSearchAgent(BaseSearchAgent):
    """
    Search agent implementation using Fess search provider.

    Workflow:
    1. Extract search intent via LLM (query normalization, filters, followups)
    2. Execute search via Fess search provider
    3. Return aggregated results
    """

    def __init__(
        self,
        search_provider: SearchProvider,
        llm_client: LLMClient,
        intent_timeout_ms: int = 2000,
        search_timeout_ms: int = 2000,
        agent_id: str | None = None,
        agent_name: str | None = None,
    ):
        """
        Initialize FessSearchAgent.

        Args:
            search_provider: Fess search provider instance
            llm_client: LLM client for intent extraction
            intent_timeout_ms: Timeout for intent extraction (default: 2000ms)
            search_timeout_ms: Timeout for search execution (default: 2000ms)
            agent_id: Unique identifier for multi-agent scenarios
            agent_name: Human-readable agent name
        """
        self.search_provider = search_provider
        self.llm_client = llm_client
        self.intent_timeout_ms = intent_timeout_ms
        self.search_timeout_ms = search_timeout_ms
        self.agent_id = agent_id or "fess"
        self.agent_name = agent_name or "FessSearchAgent"

    async def search_stream(
        self,
        query: str,
        options: dict[str, Any] | None = None,
    ) -> AsyncGenerator[SearchEvent]:
        """
        Execute search with streaming progress updates, including relevance evaluation and retry.

        Yields:
            SearchEvent(type="status"): Processing phase updates
            SearchEvent(type="intent"): Intent extraction completed
            SearchEvent(type="citations"): Search results available (intermediate, if retry happens)
            SearchEvent(type="relevance"): Relevance evaluation completed
            SearchEvent(type="retry"): Retry search starting
            SearchEvent(type="citations"): Final search results
        """
        from ..config import settings
        from .base import RelevanceEventData, RetryEventData, StatusEventData

        options = options or {}
        session_id = options.get("session_id", "unknown")

        # Configuration
        max_retries = options.get("max_retries", settings.intaste_max_retry_count)
        threshold = options.get("relevance_threshold", settings.intaste_relevance_threshold)

        logger.debug(
            f"[{session_id}] FessSearchAgent.search_stream started: query={query!r}, "
            f"max_retries={max_retries}, threshold={threshold}"
        )

        # Tracking variables
        retry_count = 0
        intent: IntentOutput | None = None
        previous_normalized_query: str | None = None
        search_result: Any = None
        evaluated_hits: list[SearchHit] = []

        # Timing accumulators
        total_intent_ms = 0
        total_search_ms = 0
        total_relevance_ms = 0

        # Retry loop
        while retry_count <= max_retries:
            is_retry = retry_count > 0

            # ========================================
            # Step 1: Intent extraction
            # ========================================
            yield SearchEvent(
                type="status",
                data=StatusEventData(phase="intent"),
                agent_id=self.agent_id,
                agent_name=self.agent_name,
            )

            logger.info(
                f"[{session_id}] Starting {'retry ' if is_retry else ''}intent extraction "
                f"(attempt {retry_count + 1})"
            )
            intent_start = time.time()

            try:
                if is_retry and previous_normalized_query and evaluated_hits:
                    # Retry intent extraction with low-score context
                    intent = await self._extract_retry_intent(
                        query=query,
                        previous_normalized_query=previous_normalized_query,
                        hits=evaluated_hits,
                        language=options.get("language", "en"),
                        session_id=session_id,
                        timeout_ms=options.get(
                            "retry_intent_timeout_ms", settings.retry_intent_timeout_ms
                        ),
                    )
                else:
                    # Normal intent extraction - get template from registry
                    registry = get_registry()
                    intent_template = registry.get("intent", IntentParams)

                    intent = await self.llm_client.intent(
                        query=query,
                        system_prompt=intent_template.system_prompt,
                        user_template=intent_template.user_template,
                        language=options.get("language", "en"),
                        filters=options.get("filters"),
                        query_history=options.get("query_history"),
                        timeout_ms=options.get("intent_timeout_ms", self.intent_timeout_ms),
                    )

                intent_ms = int((time.time() - intent_start) * 1000)
                total_intent_ms += intent_ms
                logger.info(
                    f"[{session_id}] Intent extracted: {intent.normalized_query} "
                    f"(ambiguity: {intent.ambiguity}, {intent_ms}ms)"
                )
                logger.debug(
                    f"[{session_id}] Intent details: normalized_query={intent.normalized_query!r}, "
                    f"filters={intent.filters}, followups={intent.followups}"
                )

            except (TimeoutError, Exception) as e:
                intent_ms = int((time.time() - intent_start) * 1000)
                total_intent_ms += intent_ms
                logger.warning(f"[{session_id}] Intent extraction failed after {intent_ms}ms: {e}")
                logger.debug(f"[{session_id}] Intent error: {type(e).__name__}, details: {str(e)}")

                # Fallback: use original query
                intent = IntentOutput(
                    normalized_query=query.strip(),
                    filters=options.get("filters"),
                    followups=[],
                    ambiguity="medium",
                )
                logger.debug(f"[{session_id}] Using fallback intent: {intent}")

            # Yield intent event
            yield SearchEvent(
                type="intent",
                data=IntentEventData(
                    normalized_query=intent.normalized_query,
                    filters=intent.filters,
                    followups=intent.followups,
                    ambiguity=intent.ambiguity,
                    timing_ms=intent_ms,
                ),
                agent_id=self.agent_id,
                agent_name=self.agent_name,
            )

            # ========================================
            # Step 2: Search execution
            # ========================================
            yield SearchEvent(
                type="status",
                data=StatusEventData(phase="search"),
                agent_id=self.agent_id,
                agent_name=self.agent_name,
            )

            logger.info(f"[{session_id}] Executing {'retry ' if is_retry else ''}search")
            logger.debug(
                f"[{session_id}] Search input: normalized_query={intent.normalized_query!r}, "
                f"max_results={options.get('max_results', settings.intaste_max_search_results)}"
            )

            search_start = time.time()

            try:
                search_query = SearchQuery(
                    q=intent.normalized_query,
                    page=1,
                    size=options.get("max_results", settings.intaste_max_search_results),
                    language=options.get("language", "en"),
                    filters=intent.filters or options.get("filters"),
                    timeout_ms=options.get(
                        "retry_search_timeout_ms" if is_retry else "search_timeout_ms",
                        settings.retry_search_timeout_ms if is_retry else self.search_timeout_ms,
                    ),
                )
                logger.debug(f"[{session_id}] SearchQuery created: {search_query}")

                search_result = await self.search_provider.search(search_query)
                search_ms = int((time.time() - search_start) * 1000)
                total_search_ms += search_ms
                logger.info(
                    f"[{session_id}] Search completed: {len(search_result.hits)} hits "
                    f"(total: {search_result.total}, {search_ms}ms)"
                )

                if logger.isEnabledFor(logging.DEBUG) and search_result.hits:
                    for idx, hit in enumerate(search_result.hits[:3], 1):
                        logger.debug(
                            f"[{session_id}] Hit #{idx}: id={hit.id}, "
                            f"title={hit.title[:50]}, score={hit.score}"
                        )

            except (TimeoutError, Exception) as e:
                search_ms = int((time.time() - search_start) * 1000)
                total_search_ms += search_ms
                logger.error(f"[{session_id}] Search failed after {search_ms}ms: {e}")
                logger.debug(
                    f"[{session_id}] Search error: {type(e).__name__}, "
                    f"query={intent.normalized_query!r}"
                )
                # Search failure is critical - propagate exception
                raise RuntimeError(f"Search provider error: {e}") from e

            # ========================================
            # Step 3: Relevance evaluation
            # ========================================
            if search_result.hits:
                yield SearchEvent(
                    type="status",
                    data=StatusEventData(phase="relevance"),
                    agent_id=self.agent_id,
                    agent_name=self.agent_name,
                )

                logger.info(f"[{session_id}] Starting relevance evaluation")
                relevance_start = time.time()

                try:
                    evaluated_hits = await self._evaluate_relevance(
                        query=query,
                        normalized_query=intent.normalized_query,
                        hits=search_result.hits,
                        session_id=session_id,
                        timeout_ms=options.get(
                            "retry_relevance_timeout_ms" if is_retry else "relevance_timeout_ms",
                            (
                                settings.retry_relevance_timeout_ms
                                if is_retry
                                else settings.relevance_timeout_ms
                            ),
                        ),
                        evaluation_count=options.get(
                            "relevance_evaluation_count",
                            settings.intaste_relevance_evaluation_count,
                        ),
                    )

                    relevance_ms = int((time.time() - relevance_start) * 1000)
                    total_relevance_ms += relevance_ms

                    # Get max score
                    max_score = max(
                        (
                            hit.relevance_score
                            for hit in evaluated_hits
                            if hit.relevance_score is not None
                        ),
                        default=0.0,
                    )

                    logger.info(
                        f"[{session_id}] Relevance evaluation completed: "
                        f"max_score={max_score:.2f}, {relevance_ms}ms"
                    )

                    # Yield relevance event
                    yield SearchEvent(
                        type="relevance",
                        data=RelevanceEventData(
                            evaluated_count=len(evaluated_hits),
                            max_score=max_score,
                            timing_ms=relevance_ms,
                        ),
                        agent_id=self.agent_id,
                        agent_name=self.agent_name,
                    )

                except Exception as e:
                    relevance_ms = int((time.time() - relevance_start) * 1000)
                    total_relevance_ms += relevance_ms
                    logger.error(
                        f"[{session_id}] Relevance evaluation failed after {relevance_ms}ms: {e}"
                    )
                    # Continue with unevaluated hits
                    evaluated_hits = search_result.hits
                    max_score = 0.0
            else:
                # No hits to evaluate
                evaluated_hits = []
                max_score = 0.0
                logger.info(f"[{session_id}] No hits to evaluate")

            # ========================================
            # Step 4: Retry decision
            # ========================================
            should_retry = self._should_retry(
                hits=evaluated_hits,
                threshold=threshold,
                retry_count=retry_count,
                max_retries=max_retries,
            )

            if should_retry:
                retry_count += 1
                previous_normalized_query = intent.normalized_query

                logger.info(
                    f"[{session_id}] Max score ({max_score:.2f}) below threshold ({threshold}). "
                    f"Retrying (attempt {retry_count + 1}/{max_retries + 1})"
                )

                # Yield retry event
                yield SearchEvent(
                    type="retry",
                    data=RetryEventData(
                        attempt=retry_count,
                        reason=f"Max relevance score ({max_score:.2f}) below threshold ({threshold})",
                        previous_max_score=max_score,
                    ),
                    agent_id=self.agent_id,
                    agent_name=self.agent_name,
                )

                # Continue to next iteration
                continue
            else:
                # Exit retry loop
                logger.info(
                    f"[{session_id}] Search complete. Max score: {max_score:.2f}, "
                    f"retry_count: {retry_count}"
                )
                break

        # ========================================
        # Final: Yield citations event
        # ========================================
        yield SearchEvent(
            type="citations",
            data=CitationsEventData(
                hits=evaluated_hits,
                total=search_result.total if search_result else 0,
                timing_ms=total_search_ms,
            ),
            agent_id=self.agent_id,
            agent_name=self.agent_name,
        )

        logger.debug(
            f"[{session_id}] FessSearchAgent.search_stream completed: "
            f"intent={total_intent_ms}ms, search={total_search_ms}ms, "
            f"relevance={total_relevance_ms}ms, retry_count={retry_count}"
        )

    async def health(self) -> tuple[bool, dict[str, Any]]:
        """
        Check health status of search provider and LLM client.

        Returns:
            Tuple of (is_healthy, details)
        """
        search_healthy, search_details = await self.search_provider.health()
        llm_healthy, llm_details = await self.llm_client.health()

        is_healthy = search_healthy and llm_healthy
        details = {
            "search_provider": search_details,
            "llm_client": llm_details,
        }

        return (is_healthy, details)

    async def close(self) -> None:
        """
        Close search provider and LLM client connections.
        """
        await self.search_provider.close()
        await self.llm_client.close()

    async def _evaluate_relevance(
        self,
        query: str,
        normalized_query: str,
        hits: list[SearchHit],
        session_id: str,
        timeout_ms: int,
        evaluation_count: int | None = None,
    ) -> list[SearchHit]:
        """
        Evaluate relevance of search results in parallel and update relevance_score and relevance_reason fields.

        Args:
            query: Original user query
            normalized_query: Normalized search query
            hits: Search results to evaluate
            session_id: Session identifier for logging
            timeout_ms: Total timeout budget for all evaluations
            evaluation_count: Number of top results to evaluate (None = evaluate all)

        Returns:
            List of SearchHit with relevance_score and relevance_reason populated, sorted by relevance_score descending
        """
        from ..config import settings

        # Get relevance template from registry
        registry = get_registry()
        relevance_template = registry.get("relevance", RelevanceParams)

        # Determine which hits to evaluate
        hits_to_evaluate = hits[:evaluation_count] if evaluation_count else hits
        hits_not_evaluated = hits[evaluation_count:] if evaluation_count else []

        # Get max concurrent evaluations from settings
        max_concurrent = settings.intaste_relevance_max_concurrent

        logger.info(
            f"[{session_id}] Evaluating relevance for {len(hits_to_evaluate)} of {len(hits)} results "
            f"(max_concurrent={max_concurrent})"
        )

        # Calculate per-hit timeout (distribute budget evenly)
        per_hit_timeout = (
            timeout_ms // max(len(hits_to_evaluate), 1) if hits_to_evaluate else timeout_ms
        )

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)

        async def evaluate_single_hit(
            hit: SearchHit, idx: int
        ) -> tuple[SearchHit, Exception | None]:
            """Evaluate a single hit with semaphore control."""
            async with semaphore:
                try:
                    search_result_dict = {
                        "title": hit.title,
                        "snippet": hit.snippet or "",
                        "url": hit.url,
                    }

                    relevance_output = await self.llm_client.relevance(
                        query=query,
                        normalized_query=normalized_query,
                        search_result=search_result_dict,
                        system_prompt=relevance_template.system_prompt,
                        user_template=relevance_template.user_template,
                        timeout_ms=per_hit_timeout,
                    )

                    # Create new SearchHit with relevance_score and relevance_reason
                    evaluated_hit = hit.model_copy(
                        update={
                            "relevance_score": relevance_output.score,
                            "relevance_reason": relevance_output.reason,
                        }
                    )

                    logger.debug(
                        f"[{session_id}] Hit #{idx} relevance: score={relevance_output.score:.2f}, "
                        f"reason={relevance_output.reason[:100]}"
                    )

                    return (evaluated_hit, None)

                except Exception as e:
                    logger.warning(
                        f"[{session_id}] Failed to evaluate relevance for hit #{idx}: {e}"
                    )
                    return (hit, e)

        # Execute evaluations in parallel with overall timeout
        try:
            async with asyncio.timeout(timeout_ms / 1000):
                tasks = [
                    evaluate_single_hit(hit, idx) for idx, hit in enumerate(hits_to_evaluate, 1)
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)

        except TimeoutError:
            logger.error(
                f"[{session_id}] Relevance evaluation timed out after {timeout_ms}ms. "
                "Returning results without evaluation."
            )
            # Return hits without evaluation
            return hits

        # Process results
        evaluated_hits = []
        failed_count = 0
        for result in results:
            if isinstance(result, BaseException):
                # Unexpected exception from gather itself
                logger.error(f"[{session_id}] Unexpected evaluation error: {result}")
                failed_count += 1
            elif isinstance(result, tuple):
                evaluated_hit, error = result
                evaluated_hits.append(evaluated_hit)
                if error is not None:
                    failed_count += 1

        if failed_count > 0:
            logger.warning(
                f"[{session_id}] {failed_count}/{len(hits_to_evaluate)} evaluations failed"
            )

        # Combine evaluated and non-evaluated hits
        all_hits = evaluated_hits + hits_not_evaluated

        # Sort by relevance_score descending (None values go to end)
        all_hits.sort(
            key=lambda h: h.relevance_score if h.relevance_score is not None else -1.0,
            reverse=True,
        )

        if all_hits and all_hits[0].relevance_score is not None:
            logger.info(
                f"[{session_id}] Relevance evaluation complete. "
                f"Max score: {all_hits[0].relevance_score:.2f}"
            )

        return all_hits

    def _should_retry(
        self,
        hits: list[SearchHit],
        threshold: float,
        retry_count: int,
        max_retries: int,
    ) -> bool:
        """
        Determine if retry search is needed based on relevance scores.

        Args:
            hits: Evaluated search results (may be empty for 0 results)
            threshold: Minimum acceptable relevance score
            retry_count: Current retry count
            max_retries: Maximum allowed retries

        Returns:
            True if retry is needed, False otherwise
        """
        # No retry if max retries reached
        if retry_count >= max_retries:
            return False

        # If no results, always retry to find alternative queries
        if not hits:
            return True

        # Check if best result meets threshold
        max_score = max(
            (hit.relevance_score for hit in hits if hit.relevance_score is not None),
            default=0.0,
        )

        should_retry = max_score < threshold
        return should_retry

    async def _extract_retry_intent(
        self,
        query: str,
        previous_normalized_query: str,
        hits: list[SearchHit],
        language: str,
        session_id: str,
        timeout_ms: int,
    ) -> IntentOutput:
        """
        Extract improved search intent for retry based on low-scoring results or no results.

        Args:
            query: Original user query
            previous_normalized_query: Previous normalized query that yielded poor results
            hits: Low-scoring search results (may be empty for 0 results)
            language: Query language
            session_id: Session identifier for logging
            timeout_ms: Timeout for intent extraction

        Returns:
            Improved IntentOutput for retry search
        """
        # Get retry intent templates from registry
        registry = get_registry()

        logger.info(f"[{session_id}] Extracting retry intent")

        # Choose appropriate template based on whether we have results
        if not hits:
            # No results case: use broader query strategy
            logger.info(f"[{session_id}] Using no-results template for retry")
            retry_template = registry.get("retry_intent_no_results", RetryIntentNoResultsParams)

            # Prepare template parameters using Pydantic model
            template_params = RetryIntentNoResultsParams(
                query=query,
                previous_normalized_query=previous_normalized_query,
                language=language,
            ).model_dump()
        else:
            # Low-score results case: analyze why scores were low
            logger.info(f"[{session_id}] Using low-score template for retry ({len(hits)} results)")
            retry_template = registry.get("retry_intent", RetryIntentParams)

            # Format low-scoring results for prompt
            low_score_results_lines = []
            for idx, hit in enumerate(hits[:5], 1):
                score = hit.relevance_score if hit.relevance_score is not None else 0.0
                low_score_results_lines.append(f"{idx}. [Score: {score:.2f}] {hit.title[:100]}")
            low_score_results = "\n".join(low_score_results_lines)

            # Prepare template parameters using Pydantic model
            template_params = RetryIntentParams(
                query=query,
                previous_normalized_query=previous_normalized_query,
                language=language,
                low_score_results=low_score_results,
            ).model_dump()

        logger.debug(f"[{session_id}] Retry intent extraction started")

        try:
            intent = await self.llm_client.intent(
                query=query,
                system_prompt=retry_template.system_prompt,
                user_template=retry_template.user_template,
                language=language,
                filters=None,
                query_history=None,
                timeout_ms=timeout_ms,
                template_params=template_params,
            )
            logger.info(f"[{session_id}] Retry intent extracted: {intent.normalized_query}")
            return intent

        except Exception as e:
            logger.error(f"[{session_id}] Retry intent extraction failed: {e}")
            # Fallback: use original query
            return IntentOutput(
                normalized_query=query.strip(),
                filters=None,
                followups=[],
                ambiguity="medium",
            )
