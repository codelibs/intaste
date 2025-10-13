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

import logging
import time
from collections.abc import AsyncGenerator
from typing import Any

from ..llm.base import IntentOutput, LLMClient
from ..llm.prompts import INTENT_SYSTEM_PROMPT, INTENT_USER_TEMPLATE
from ..search_provider.base import SearchProvider, SearchQuery
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
    ):
        """
        Initialize FessSearchAgent.

        Args:
            search_provider: Fess search provider instance
            llm_client: LLM client for intent extraction
            intent_timeout_ms: Timeout for intent extraction (default: 2000ms)
            search_timeout_ms: Timeout for search execution (default: 2000ms)
        """
        self.search_provider = search_provider
        self.llm_client = llm_client
        self.intent_timeout_ms = intent_timeout_ms
        self.search_timeout_ms = search_timeout_ms

    async def search_stream(
        self,
        query: str,
        options: dict[str, Any] | None = None,
    ) -> AsyncGenerator[SearchEvent, None]:
        """
        Execute search with streaming progress updates.

        Yields:
            SearchEvent(type="intent"): Intent extraction completed
            SearchEvent(type="citations"): Search results available
        """
        options = options or {}
        session_id = options.get("session_id", "unknown")

        logger.debug(f"[{session_id}] FessSearchAgent.search_stream started: query={query!r}")

        # Step 1: Intent extraction
        logger.info(f"[{session_id}] Starting intent extraction")
        intent_start = time.time()
        intent: IntentOutput

        try:
            intent = await self.llm_client.intent(
                query=query,
                system_prompt=INTENT_SYSTEM_PROMPT,
                user_template=INTENT_USER_TEMPLATE,
                language=options.get("language", "en"),
                filters=options.get("filters"),
                timeout_ms=options.get("intent_timeout_ms", self.intent_timeout_ms),
            )
            intent_ms = int((time.time() - intent_start) * 1000)
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
        )

        # Step 2: Search execution
        logger.info(f"[{session_id}] Executing search")
        logger.debug(
            f"[{session_id}] Search input: normalized_query={intent.normalized_query!r}, "
            f"max_results={options.get('max_results', 5)}"
        )

        search_start = time.time()

        try:
            search_query = SearchQuery(
                q=intent.normalized_query,
                page=1,
                size=options.get("max_results", 5),
                language=options.get("language", "en"),
                filters=intent.filters or options.get("filters"),
                timeout_ms=options.get("search_timeout_ms", self.search_timeout_ms),
            )
            logger.debug(f"[{session_id}] SearchQuery created: {search_query}")

            search_result = await self.search_provider.search(search_query)
            search_ms = int((time.time() - search_start) * 1000)
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
            logger.error(f"[{session_id}] Search failed after {search_ms}ms: {e}")
            logger.debug(
                f"[{session_id}] Search error: {type(e).__name__}, "
                f"query={intent.normalized_query!r}"
            )
            # Search failure is critical - propagate exception
            raise RuntimeError(f"Search provider error: {e}") from e

        # Yield citations event
        yield SearchEvent(
            type="citations",
            data=CitationsEventData(
                hits=search_result.hits,
                total=search_result.total,
                timing_ms=search_ms,
            ),
        )

        logger.debug(
            f"[{session_id}] FessSearchAgent.search_stream completed: "
            f"intent={intent_ms}ms, search={search_ms}ms"
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
