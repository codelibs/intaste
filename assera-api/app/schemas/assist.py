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
Schemas for /assist endpoints.
"""

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class Citation(BaseModel):
    """
    A single citation/search result reference.
    """

    id: int = Field(..., ge=1, description="Citation ID (1-indexed)")
    title: str
    snippet: str | None = Field(None, description="HTML snippet (must be sanitized in UI)")
    url: str
    score: float | None = None
    meta: dict[str, Any] | None = None


class Answer(BaseModel):
    """
    Generated answer with citations and follow-up questions.
    """

    text: str = Field(..., max_length=300, description="Brief guidance text")
    suggested_questions: list[str] = Field(
        default_factory=list, max_length=3, description="Follow-up question suggestions"
    )


class Session(BaseModel):
    """
    Session tracking information.
    """

    id: str
    turn: int = Field(..., ge=1)


class Timings(BaseModel):
    """
    Performance timings for request processing.
    """

    llm_ms: int = Field(..., ge=0)
    search_ms: int = Field(..., ge=0)
    total_ms: int = Field(..., ge=0)


class Notice(BaseModel):
    """
    Notice about fallback or degraded functionality.
    """

    fallback: bool = False
    reason: str | None = Field(
        None, description="Reason: LLM_TIMEOUT|BAD_LLM_OUTPUT|LLM_UNAVAILABLE"
    )


class AssistQueryRequest(BaseModel):
    """
    Request for assisted search query.
    """

    query: str = Field(..., min_length=1, max_length=4096, description="Natural language query")
    session_id: str | None = Field(None, description="Session ID (UUID v4)")
    options: dict[str, Any] | None = Field(
        None,
        description="Optional parameters: max_results, language, filters, timeout_ms",
    )


class AssistQueryResponse(BaseModel):
    """
    Response from assisted search query.
    """

    answer: Answer
    citations: list[Citation]
    session: Session
    timings: Timings
    notice: Notice | None = None


class FeedbackRequest(BaseModel):
    """
    User feedback on an assist response.
    """

    session_id: UUID
    turn: int = Field(..., ge=1)
    rating: Literal["up", "down"]
    comment: str | None = Field(None, max_length=500)
