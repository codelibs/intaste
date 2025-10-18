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
Unit tests for FessSearchAgent.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.llm.base import IntentOutput
from app.core.search_agent.fess import FessSearchAgent
from app.core.search_provider.base import SearchHit, SearchResult


@pytest.fixture
def mock_search_provider():
    """Create mock search provider."""
    provider = AsyncMock()
    provider.health = AsyncMock(return_value=(True, {"status": "healthy"}))
    provider.close = AsyncMock()
    return provider


@pytest.fixture
def mock_llm_client():
    """Create mock LLM client."""
    client = AsyncMock()
    client.health = AsyncMock(return_value=(True, {"status": "healthy"}))
    client.close = AsyncMock()
    return client


@pytest.fixture
def search_agent(mock_search_provider, mock_llm_client):
    """Create FessSearchAgent with mocked dependencies."""
    return FessSearchAgent(
        search_provider=mock_search_provider,
        llm_client=mock_llm_client,
        intent_timeout_ms=2000,
        search_timeout_ms=2000,
    )


@pytest.mark.asyncio
async def test_search_stream_success(search_agent, mock_llm_client, mock_search_provider):
    """Test successful search_stream execution."""
    # Mock intent extraction
    mock_llm_client.intent.return_value = IntentOutput(
        normalized_query="test query",
        filters={"site": "example.com"},
        followups=["related question?"],
        ambiguity="low",
    )

    # Mock search results
    mock_search_provider.search.return_value = SearchResult(
        total=10,
        hits=[
            SearchHit(
                id="1",
                title="Test Document",
                url="https://example.com/doc1",
                snippet="Test snippet",
                score=0.95,
                meta={"site": "example.com"},
            )
        ],
        took_ms=50,
        page=1,
        size=5,
    )

    # Execute search_stream
    events = []
    async for event in search_agent.search_stream("user query", {"session_id": "test"}):
        events.append(event)

    # Verify events (now includes status events)
    assert len(events) == 4
    assert events[0].type == "status"
    assert events[0].status_data.phase == "intent"
    assert events[1].type == "intent"
    assert events[1].intent_data.normalized_query == "test query"
    assert events[1].intent_data.filters == {"site": "example.com"}
    assert events[2].type == "status"
    assert events[2].status_data.phase == "search"
    assert events[3].type == "citations"
    assert len(events[3].citations_data.hits) == 1
    assert events[3].citations_data.total == 10


@pytest.mark.asyncio
async def test_search_stream_intent_fallback(search_agent, mock_llm_client, mock_search_provider):
    """Test search_stream with intent extraction failure (fallback)."""
    # Mock intent extraction failure
    mock_llm_client.intent.side_effect = TimeoutError("LLM timeout")

    # Mock search results
    mock_search_provider.search.return_value = SearchResult(
        total=5,
        hits=[
            SearchHit(
                id="1",
                title="Fallback Document",
                url="https://example.com/doc1",
                snippet="Fallback snippet",
                score=0.8,
            )
        ],
        took_ms=40,
        page=1,
        size=5,
    )

    # Execute search_stream
    events = []
    async for event in search_agent.search_stream("user query", {"session_id": "test"}):
        events.append(event)

    # Verify fallback behavior (now includes status events)
    assert len(events) == 4
    assert events[0].type == "status"
    assert events[0].status_data.phase == "intent"
    assert events[1].type == "intent"
    assert events[1].intent_data.normalized_query == "user query"  # Original query used
    assert events[1].intent_data.ambiguity == "medium"
    assert events[2].type == "status"
    assert events[2].status_data.phase == "search"
    assert events[3].type == "citations"


@pytest.mark.asyncio
async def test_search_stream_search_failure(search_agent, mock_llm_client, mock_search_provider):
    """Test search_stream with search failure (critical error)."""
    # Mock intent extraction
    mock_llm_client.intent.return_value = IntentOutput(
        normalized_query="test query",
        filters=None,
        followups=[],
        ambiguity="low",
    )

    # Mock search failure
    mock_search_provider.search.side_effect = RuntimeError("Search provider error")

    # Execute search_stream and expect exception
    with pytest.raises(RuntimeError, match="Search provider error"):
        async for event in search_agent.search_stream("user query", {"session_id": "test"}):
            pass


@pytest.mark.asyncio
async def test_search_non_streaming(search_agent, mock_llm_client, mock_search_provider):
    """Test non-streaming search() method."""
    # Mock intent extraction
    mock_llm_client.intent.return_value = IntentOutput(
        normalized_query="optimized query",
        filters={"mimetype": "text/html"},
        followups=["follow up 1", "follow up 2"],
        ambiguity="low",
    )

    # Mock search results
    mock_search_provider.search.return_value = SearchResult(
        total=3,
        hits=[
            SearchHit(
                id="1",
                title="Doc 1",
                url="https://example.com/1",
                snippet="Snippet 1",
                score=0.9,
            ),
            SearchHit(
                id="2",
                title="Doc 2",
                url="https://example.com/2",
                snippet="Snippet 2",
                score=0.8,
            ),
        ],
        took_ms=60,
        page=1,
        size=5,
    )

    # Execute search
    result = await search_agent.search("user query", {"session_id": "test"})

    # Verify result
    assert result.original_query == "user query"
    assert result.normalized_query == "optimized query"
    assert result.total == 3
    assert len(result.hits) == 2
    assert result.followups == ["follow up 1", "follow up 2"]
    assert result.filters == {"mimetype": "text/html"}
    assert result.ambiguity == "low"
    assert result.timings.intent_ms >= 0  # Changed from > 0 to >= 0 since mock execution is instant
    assert result.timings.search_ms >= 0  # Changed from > 0 to >= 0 since mock execution is instant


@pytest.mark.asyncio
async def test_health_check(search_agent, mock_search_provider, mock_llm_client):
    """Test health check aggregation."""
    mock_search_provider.health.return_value = (True, {"status": "green"})
    mock_llm_client.health.return_value = (True, {"model": "gpt-oss"})

    is_healthy, details = await search_agent.health()

    assert is_healthy is True
    assert "search_provider" in details
    assert "llm_client" in details
    assert details["search_provider"]["status"] == "green"
    assert details["llm_client"]["model"] == "gpt-oss"


@pytest.mark.asyncio
async def test_health_check_unhealthy(search_agent, mock_search_provider, mock_llm_client):
    """Test health check with unhealthy component."""
    mock_search_provider.health.return_value = (False, {"error": "connection failed"})
    mock_llm_client.health.return_value = (True, {"model": "gpt-oss"})

    is_healthy, details = await search_agent.health()

    assert is_healthy is False
    assert details["search_provider"]["error"] == "connection failed"


@pytest.mark.asyncio
async def test_close(search_agent, mock_search_provider, mock_llm_client):
    """Test close method."""
    await search_agent.close()

    mock_search_provider.close.assert_called_once()
    mock_llm_client.close.assert_called_once()
