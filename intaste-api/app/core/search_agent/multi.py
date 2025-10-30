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
Multi-agent search implementation that runs multiple search agents in parallel.
"""

import logging
import time
from collections.abc import AsyncGenerator
from typing import Any

from ..llm.base import LLMClient
from ..llm.prompts import MergeResultsParams, get_registry
from .base import (
    BaseSearchAgent,
    CitationsEventData,
    SearchAgentResult,
    SearchEvent,
    StatusEventData,
)

logger = logging.getLogger(__name__)


class MultiSearchAgent(BaseSearchAgent):
    """
    Search agent that runs multiple search agents in parallel and merges results.

    Workflow:
    1. Execute all enabled agents in parallel
    2. Stream events from all agents (with agent_id/agent_name)
    3. Collect final results from each agent
    4. Use LLM to evaluate and select/merge best results
    5. Yield final unified citations event
    """

    def __init__(
        self,
        agents: list[tuple[str, str, Any]],  # List of (agent_id, agent_name, agent_instance)
        llm_client: LLMClient,
        merge_timeout_ms: int = 5000,
    ):
        """
        Initialize MultiSearchAgent.

        Args:
            agents: List of (agent_id, agent_name, agent_instance) tuples
            llm_client: LLM client for merge evaluation
            merge_timeout_ms: Timeout for merge evaluation (default: 5000ms)
        """
        self.agents = agents
        self.llm_client = llm_client
        self.merge_timeout_ms = merge_timeout_ms
        logger.info(f"MultiSearchAgent initialized with {len(agents)} agents")

    async def search_stream(
        self,
        query: str,
        options: dict[str, Any] | None = None,
    ) -> AsyncGenerator[SearchEvent]:
        """
        Execute multiple search agents sequentially and stream unified events.

        Note: Currently executes agents sequentially for simplicity.
        Future improvement: Parallel execution with event streaming.

        Yields:
            SearchEvent: Events from all agents (with agent_id/agent_name)
            SearchEvent(type="citations"): Final merged citations
        """
        options = options or {}
        session_id = options.get("session_id", "unknown")

        logger.info(
            f"[{session_id}] MultiSearchAgent.search_stream started: "
            f"query={query!r}, num_agents={len(self.agents)}"
        )

        # Storage for final results from each agent
        agent_results: dict[str, dict[str, Any]] = {}
        collected_results = []

        # Execute each agent sequentially and stream their events
        for agent_id, agent_name, agent in self.agents:
            logger.info(f"[{session_id}] Starting agent: {agent_id} ({agent_name})")
            result = None

            try:
                async for event in agent.search_stream(query, options):
                    # Forward event (agent_id/agent_name already set by FessSearchAgent)
                    yield event

                    # Collect final citations
                    if event.type == "citations" and event.citations_data:
                        result = SearchAgentResult(
                            hits=event.citations_data.hits,
                            total=event.citations_data.total,
                            normalized_query="",
                            original_query=query,
                            followups=[],
                            filters={},
                            timings=None,
                            notice=None,
                            ambiguity="medium",
                        )

                if result:
                    collected_results.append((agent_id, agent_name, result))
                    agent_results[agent_id] = {
                        "agent_name": agent_name,
                        "result": result,
                    }
                    logger.info(
                        f"[{session_id}] Agent {agent_id} completed: {len(result.hits)} hits"
                    )

            except Exception as e:
                logger.error(f"[{session_id}] Agent {agent_id} failed: {e}")

        logger.info(
            f"[{session_id}] All agents completed: {len(collected_results)} succeeded, "
            f"{len(self.agents) - len(collected_results)} failed"
        )

        # If no agents succeeded, yield empty citations
        if not collected_results:
            logger.error(f"[{session_id}] No agents returned results")
            yield SearchEvent(
                type="citations",
                data=CitationsEventData(
                    hits=[],
                    total=0,
                    timing_ms=0,
                ),
            )
            return

        # If only one agent, use its result directly
        if len(collected_results) == 1:
            agent_id, agent_name, result = collected_results[0]
            logger.info(f"[{session_id}] Single agent result: {agent_id}")
            yield SearchEvent(
                type="citations",
                data=CitationsEventData(
                    hits=result.hits,
                    total=result.total,
                    timing_ms=0,
                ),
            )
            return

        # Multiple agents: use LLM to merge results
        logger.info(f"[{session_id}] Merging results from {len(collected_results)} agents")
        yield SearchEvent(
            type="status",
            data=StatusEventData(phase="merge"),
        )

        merge_start = time.time()
        try:
            # Prepare data for LLM merge evaluation
            agent_results_for_llm = []
            for agent_id, agent_name, result in collected_results:
                citations_data = [
                    {
                        "title": hit.title,
                        "snippet": hit.snippet,
                        "url": hit.url,
                        "relevance_score": hit.relevance_score,
                    }
                    for hit in result.hits
                ]
                max_score = max(
                    (hit.relevance_score for hit in result.hits if hit.relevance_score is not None),
                    default=0.0,
                )
                agent_results_for_llm.append((agent_id, agent_name, citations_data, max_score))

            # Call LLM to merge results - get template from registry
            registry = get_registry()
            merge_template = registry.get("merge_results", MergeResultsParams)

            merge_output = await self.llm_client.merge_results(
                query=query,
                agent_results=agent_results_for_llm,
                system_prompt=merge_template.system_prompt,
                user_template=merge_template.user_template,
                timeout_ms=self.merge_timeout_ms,
            )

            merge_ms = int((time.time() - merge_start) * 1000)
            logger.info(
                f"[{session_id}] Merge completed: selected={merge_output.selected_agent_ids}, "
                f"strategy={merge_output.merge_strategy}, {merge_ms}ms"
            )

            # Merge results according to strategy
            if merge_output.merge_strategy == "single":
                # Use only the first selected agent
                selected_agent_id = merge_output.selected_agent_ids[0]
                selected_result = agent_results[selected_agent_id]["result"]
                final_hits = selected_result.hits
                final_total = selected_result.total
            else:
                # Merge results from all selected agents
                final_hits = []
                final_total = 0
                for agent_id in merge_output.selected_agent_ids:
                    if agent_id in agent_results:
                        result = agent_results[agent_id]["result"]
                        final_hits.extend(result.hits)
                        final_total += result.total

                # Sort by relevance_score descending
                final_hits.sort(
                    key=lambda h: h.relevance_score if h.relevance_score is not None else -1.0,
                    reverse=True,
                )

            # Yield final merged citations
            yield SearchEvent(
                type="citations",
                data=CitationsEventData(
                    hits=final_hits,
                    total=final_total,
                    timing_ms=merge_ms,
                ),
            )

        except Exception as e:
            merge_ms = int((time.time() - merge_start) * 1000)
            logger.error(f"[{session_id}] Merge failed after {merge_ms}ms: {e}")

            # Fallback: use first agent's result
            agent_id, agent_name, result = collected_results[0]
            logger.info(f"[{session_id}] Using fallback agent: {agent_id}")
            yield SearchEvent(
                type="citations",
                data=CitationsEventData(
                    hits=result.hits,
                    total=result.total,
                    timing_ms=merge_ms,
                ),
            )

        logger.debug(f"[{session_id}] MultiSearchAgent.search_stream completed")

    async def health(self) -> tuple[bool, dict[str, Any]]:
        """
        Check health status of all agents and LLM client.

        Returns:
            Tuple of (is_healthy, details)
        """
        all_healthy = True
        agents_health = {}

        for agent_id, agent_name, agent in self.agents:
            try:
                is_healthy, details = await agent.health()
                agents_health[agent_id] = {
                    "agent_name": agent_name,
                    "healthy": is_healthy,
                    "details": details,
                }
                if not is_healthy:
                    all_healthy = False
            except Exception as e:
                logger.error(f"Health check failed for agent {agent_id}: {e}")
                agents_health[agent_id] = {
                    "agent_name": agent_name,
                    "healthy": False,
                    "error": str(e),
                }
                all_healthy = False

        llm_healthy, llm_details = await self.llm_client.health()
        if not llm_healthy:
            all_healthy = False

        details = {
            "agents": agents_health,
            "llm_client": llm_details,
        }

        return (all_healthy, details)

    async def close(self) -> None:
        """
        Close all agents and LLM client connections.
        """
        for agent_id, _, agent in self.agents:
            try:
                await agent.close()
            except Exception as e:
                logger.error(f"Failed to close agent {agent_id}: {e}")

        await self.llm_client.close()
