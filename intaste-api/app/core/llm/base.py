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
        timeout_ms: int | None = None,
    ) -> AsyncGenerator[str]:
        """Compose answer with streaming response. Yields text chunks."""
        ...

    async def health(self) -> tuple[bool, dict[str, Any]]:
        """Check LLM client health status."""
        ...

    async def close(self) -> None:
        """Close the LLM client and release resources."""
        ...
