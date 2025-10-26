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
Base protocol and models for LLM clients.
"""

from collections.abc import AsyncGenerator
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field


class IntentOutput(BaseModel):
    """
    Output from intent extraction (query normalization).
    """

    normalized_query: str = Field(..., min_length=1)
    filters: dict[str, Any] | None = None
    followups: list[str] = Field(default_factory=list, max_length=3)
    ambiguity: Literal["low", "medium", "high"] = "low"


class ComposeOutput(BaseModel):
    """
    Output from answer composition.
    """

    text: str = Field(..., max_length=300)
    suggested_questions: list[str] = Field(default_factory=list, max_length=3)


class RelevanceOutput(BaseModel):
    """
    Output from relevance evaluation.
    Evaluates how well a search result matches the user's intent.
    """

    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score from 0.0 to 1.0")
    reason: str = Field(..., min_length=1, max_length=500, description="Explanation for the score")


class MergeOutput(BaseModel):
    """
    Output from merging multiple search agent results.
    LLM evaluates and selects/merges the best results from multiple agents.
    """

    selected_agent_ids: list[str] = Field(
        ...,
        min_length=1,
        description="IDs of agents whose results were selected (in priority order)",
    )
    reason: str = Field(
        ..., min_length=1, max_length=500, description="Explanation for the selection"
    )
    merge_strategy: str = Field(
        default="single",
        description="Strategy used: 'single' (one agent) or 'merge' (combined results)",
    )


class LLMClient(Protocol):
    """
    Protocol for LLM clients (e.g., Ollama, OpenAI).
    """

    async def intent(
        self,
        query: str,
        system_prompt: str,
        user_template: str,
        language: str | None = None,
        filters: dict[str, Any] | None = None,
        query_history: list[str] | None = None,
        timeout_ms: int | None = None,
    ) -> IntentOutput:
        """Extract search intent from user query with optional query history context."""
        ...

    async def compose(
        self,
        query: str,
        normalized_query: str,
        citations_data: list[dict[str, Any]],
        followups: list[str] | None = None,
        language: str | None = None,
        timeout_ms: int | None = None,
    ) -> ComposeOutput:
        """Compose brief answer from search results."""
        ...

    def compose_stream(
        self,
        query: str,
        normalized_query: str,
        citations_data: list[dict[str, Any]],
        followups: list[str] | None = None,
        language: str | None = None,
        timeout_ms: int | None = None,
    ) -> AsyncGenerator[str]:
        """Compose answer with streaming response. Yields text chunks."""
        ...

    async def relevance(
        self,
        query: str,
        normalized_query: str,
        search_result: dict[str, Any],
        system_prompt: str,
        user_template: str,
        timeout_ms: int | None = None,
    ) -> RelevanceOutput:
        """
        Evaluate relevance of a single search result to the user's query intent.

        Args:
            query: Original user query
            normalized_query: Normalized search query
            search_result: Search result to evaluate (title, snippet, url)
            system_prompt: System prompt for relevance evaluation
            user_template: User prompt template for relevance evaluation
            timeout_ms: Optional timeout in milliseconds

        Returns:
            RelevanceOutput with score (0.0-1.0) and reason
        """
        ...

    async def merge_results(
        self,
        query: str,
        agent_results: list[tuple[str, str, list[dict[str, Any]], float]],
        system_prompt: str,
        user_template: str,
        timeout_ms: int | None = None,
    ) -> MergeOutput:
        """
        Merge and select best results from multiple search agents using LLM evaluation.

        Args:
            query: Original user query
            agent_results: List of (agent_id, agent_name, citations, max_relevance_score)
            system_prompt: System prompt for merge evaluation
            user_template: User prompt template for merge evaluation
            timeout_ms: Optional timeout in milliseconds

        Returns:
            MergeOutput with selected agent IDs, reason, and merge strategy
        """
        ...

    async def warmup(self, timeout_ms: int = 30000) -> bool:
        """
        Warm up the LLM model by preloading it into memory.

        Args:
            timeout_ms: Timeout for warmup request (default: 30000ms = 30s)

        Returns:
            True if warmup succeeded, False otherwise
        """
        ...

    async def health(self) -> tuple[bool, dict[str, Any]]:
        """Check LLM client health status."""
        ...

    async def close(self) -> None:
        """Close the LLM client and release resources."""
        ...
