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
Base protocol for search providers.
"""

from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field


class SearchHit(BaseModel):
    """
    A single search result.
    """

    id: str
    title: str
    url: str
    snippet: str | None = None
    score: float | None = None
    meta: dict[str, Any] | None = None


class SearchResult(BaseModel):
    """
    Search results with metadata.
    """

    total: int = Field(..., ge=0)
    hits: list[SearchHit]
    took_ms: int | None = None
    page: int = Field(..., ge=1)
    size: int = Field(..., ge=1)


class SearchQuery(BaseModel):
    """
    Normalized search query.
    """

    q: str
    page: int = Field(default=1, ge=1)
    size: int = Field(default=5, ge=1, le=50)
    sort: Literal["score", "date_desc", "date_asc"] = "score"
    language: str | None = None
    filters: dict[str, Any] | None = None
    timeout_ms: int | None = None


class SearchProvider(Protocol):
    """
    Protocol for search providers (e.g., Fess, Elasticsearch).
    """

    async def search(self, query: SearchQuery) -> SearchResult:
        """Execute search query and return normalized results."""
        ...

    async def health(self) -> tuple[bool, dict[str, Any]]:
        """Check provider health status."""
        ...
