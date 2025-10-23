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
Base protocol and models for search agents.

A search agent encapsulates the entire search workflow:
1. Intent extraction (query optimization via LLM)
2. Search execution (via search provider)
3. Result aggregation

This abstraction enables support for multiple search agents
(e.g., Fess, MCP, Elasticsearch) with different query processing strategies.
"""

from collections.abc import AsyncGenerator
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field

from ...schemas.assist import Notice
from ..search_provider.base import SearchHit


class IntentEventData(BaseModel):
    """
    Event data emitted when intent extraction is complete.
    """

    normalized_query: str = Field(..., min_length=1)
    filters: dict[str, Any] | None = None
    followups: list[str] = Field(default_factory=list, max_length=3)
    ambiguity: Literal["low", "medium", "high"] = "medium"
    timing_ms: int = Field(..., ge=0)


class CitationsEventData(BaseModel):
    """
    Event data emitted when search execution is complete.
    """

    hits: list[SearchHit]
    total: int = Field(..., ge=0)
    timing_ms: int = Field(..., ge=0)


class StatusEventData(BaseModel):
    """
    Event data emitted during processing to indicate current phase.
    Used to provide user feedback while waiting for results.
    """

    phase: Literal["intent", "search", "relevance", "compose"]


class RelevanceEventData(BaseModel):
    """
    Event data emitted when relevance evaluation is complete.
    """

    evaluated_count: int = Field(..., ge=0, description="Number of results evaluated")
    max_score: float = Field(..., ge=0.0, le=1.0, description="Highest relevance score")
    timing_ms: int = Field(..., ge=0)


class RetryEventData(BaseModel):
    """
    Event data emitted when retry search is starting.
    """

    attempt: int = Field(..., ge=1, description="Retry attempt number (1-based)")
    reason: str = Field(..., min_length=1, description="Reason for retry")
    previous_max_score: float = Field(
        ..., ge=0.0, le=1.0, description="Max score from previous attempt"
    )


class SearchEvent(BaseModel):
    """
    Streaming event from search agent during query processing.

    Events are emitted in order:
    1. status(intent): Intent extraction starting
    2. intent: Intent extraction completed
    3. status(search): Search execution starting
    4. citations: Search results available
    5. status(relevance): Relevance evaluation starting
    6. relevance: Relevance evaluation completed
    7. retry: Retry search starting (if needed)
    """

    type: Literal["intent", "citations", "status", "relevance", "retry"]
    data: (
        IntentEventData | CitationsEventData | StatusEventData | RelevanceEventData | RetryEventData
    )

    @property
    def intent_data(self) -> IntentEventData | None:
        """Get intent data if this is an intent event."""
        return self.data if isinstance(self.data, IntentEventData) else None

    @property
    def citations_data(self) -> CitationsEventData | None:
        """Get citations data if this is a citations event."""
        return self.data if isinstance(self.data, CitationsEventData) else None

    @property
    def status_data(self) -> StatusEventData | None:
        """Get status data if this is a status event."""
        return self.data if isinstance(self.data, StatusEventData) else None

    @property
    def relevance_data(self) -> RelevanceEventData | None:
        """Get relevance data if this is a relevance event."""
        return self.data if isinstance(self.data, RelevanceEventData) else None

    @property
    def retry_data(self) -> RetryEventData | None:
        """Get retry data if this is a retry event."""
        return self.data if isinstance(self.data, RetryEventData) else None


class SearchAgentTimings(BaseModel):
    """
    Timing information for search agent operations.
    """

    intent_ms: int = Field(..., ge=0)
    search_ms: int = Field(..., ge=0)
    relevance_ms: int = Field(default=0, ge=0, description="Time for relevance evaluation")
    retry_count: int = Field(default=0, ge=0, description="Number of retry attempts")


class SearchAgentResult(BaseModel):
    """
    Aggregated result from search agent (non-streaming).
    """

    hits: list[SearchHit]
    total: int = Field(..., ge=0)
    normalized_query: str = Field(..., min_length=1)
    original_query: str = Field(..., min_length=1)
    followups: list[str] = Field(default_factory=list, max_length=3)
    filters: dict[str, Any] | None = None
    timings: SearchAgentTimings
    notice: Notice | None = None
    ambiguity: Literal["low", "medium", "high"] = "medium"


class SearchAgent(Protocol):
    """
    Protocol for search agents.

    A search agent processes natural language queries and returns search results
    with enriched metadata (intent, filters, followup suggestions).
    """

    async def search(
        self,
        query: str,
        options: dict[str, Any] | None = None,
    ) -> SearchAgentResult:
        """
        Execute search query and return aggregated result (non-streaming).

        Args:
            query: Natural language query string from user
            options: Optional parameters:
                - language: Language code (e.g., "en", "ja")
                - max_results: Maximum number of results (default: 5)
                - filters: Additional search filters
                - intent_timeout_ms: Timeout for intent extraction
                - search_timeout_ms: Timeout for search execution

        Returns:
            SearchAgentResult: Aggregated search results with metadata

        Raises:
            TimeoutError: If operation exceeds timeout
            RuntimeError: If search execution fails
        """
        ...

    def search_stream(
        self,
        query: str,
        options: dict[str, Any] | None = None,
    ) -> AsyncGenerator[SearchEvent]:
        """
        Execute search query with streaming progress updates.

        Args:
            query: Natural language query string from user
            options: Same as search() method

        Yields:
            SearchEvent: Progress events (intent, citations)

        Raises:
            TimeoutError: If operation exceeds timeout
            RuntimeError: If search execution fails
        """
        ...

    async def health(self) -> tuple[bool, dict[str, Any]]:
        """
        Check search agent health status.

        Returns:
            Tuple of (is_healthy, details_dict)
        """
        ...

    async def close(self) -> None:
        """
        Close search agent and release resources.
        """
        ...


class BaseSearchAgent:
    """
    Base implementation providing common functionality for search agents.

    Provides default implementation of search() using search_stream().
    Subclasses must implement search_stream().
    """

    def search_stream(
        self,
        query: str,
        options: dict[str, Any] | None = None,
    ) -> AsyncGenerator[SearchEvent]:
        """
        Abstract method: must be implemented by subclasses.

        Yields:
            SearchEvent: Progress events (intent, citations)
        """
        raise NotImplementedError("Subclasses must implement search_stream()")

    async def search(
        self,
        query: str,
        options: dict[str, Any] | None = None,
    ) -> SearchAgentResult:
        """
        Default implementation: collect all events from search_stream()
        and return final aggregated result.
        """
        intent_data: IntentEventData | None = None
        citations_data: CitationsEventData | None = None
        notice: Notice | None = None

        async for event in self.search_stream(query, options):
            if event.type == "intent":
                intent_data = event.intent_data
            elif event.type == "citations":
                citations_data = event.citations_data

        # Validate that we received all required events
        if not intent_data:
            raise RuntimeError("Intent extraction failed: no intent event received")
        if not citations_data:
            raise RuntimeError("Search execution failed: no citations event received")

        return SearchAgentResult(
            hits=citations_data.hits,
            total=citations_data.total,
            normalized_query=intent_data.normalized_query,
            original_query=query,
            followups=intent_data.followups,
            filters=intent_data.filters,
            timings=SearchAgentTimings(
                intent_ms=intent_data.timing_ms,
                search_ms=citations_data.timing_ms,
            ),
            notice=notice,
            ambiguity=intent_data.ambiguity,
        )

    async def close(self) -> None:
        """Default implementation: no-op. Override if cleanup is needed."""
        pass
