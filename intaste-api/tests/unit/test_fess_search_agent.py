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
    from app.core.llm.base import RelevanceOutput

    # Mock intent extraction
    mock_llm_client.intent.return_value = IntentOutput(
        normalized_query="test query",
        filters={"site": "example.com"},
        followups=["related question?"],
        ambiguity="low",
    )

    # Mock relevance evaluation (high score to avoid retry)
    mock_llm_client.relevance.return_value = RelevanceOutput(
        score=0.9, reason="Highly relevant"
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

    # Verify events (now includes status and relevance events)
    # Expected: status(intent), intent, status(search), status(relevance), relevance, citations
    assert len(events) == 6
    assert events[0].type == "status"
    assert events[0].status_data.phase == "intent"
    assert events[1].type == "intent"
    assert events[1].intent_data.normalized_query == "test query"
    assert events[1].intent_data.filters == {"site": "example.com"}
    assert events[2].type == "status"
    assert events[2].status_data.phase == "search"
    assert events[3].type == "status"
    assert events[3].status_data.phase == "relevance"
    assert events[4].type == "relevance"
    assert events[4].relevance_data.max_score == 0.9
    assert events[5].type == "citations"
    assert len(events[5].citations_data.hits) == 1
    assert events[5].citations_data.total == 10


@pytest.mark.asyncio
async def test_search_stream_intent_fallback(search_agent, mock_llm_client, mock_search_provider):
    """Test search_stream with intent extraction failure (fallback)."""
    from app.core.llm.base import RelevanceOutput

    # Mock intent extraction failure
    mock_llm_client.intent.side_effect = TimeoutError("LLM timeout")

    # Mock relevance evaluation (high score to avoid retry)
    mock_llm_client.relevance.return_value = RelevanceOutput(
        score=0.8, reason="Relevant"
    )

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

    # Verify fallback behavior (now includes status and relevance events)
    # Expected: status(intent), intent, status(search), status(relevance), relevance, citations
    assert len(events) == 6
    assert events[0].type == "status"
    assert events[0].status_data.phase == "intent"
    assert events[1].type == "intent"
    assert events[1].intent_data.normalized_query == "user query"  # Original query used
    assert events[1].intent_data.ambiguity == "medium"
    assert events[2].type == "status"
    assert events[2].status_data.phase == "search"
    assert events[3].type == "status"
    assert events[3].status_data.phase == "relevance"
    assert events[4].type == "relevance"
    assert events[5].type == "citations"


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


@pytest.mark.asyncio
async def test_evaluate_relevance(search_agent, mock_llm_client):
    """Test _evaluate_relevance method."""
    from app.core.llm.base import RelevanceOutput

    # Mock relevance evaluation
    mock_llm_client.relevance.side_effect = [
        RelevanceOutput(score=0.9, reason="Highly relevant"),
        RelevanceOutput(score=0.6, reason="Moderately relevant"),
        RelevanceOutput(score=0.3, reason="Barely relevant"),
    ]

    hits = [
        SearchHit(
            id="1", title="Doc 1", url="https://example.com/1", snippet="snippet 1", score=0.95
        ),
        SearchHit(
            id="2", title="Doc 2", url="https://example.com/2", snippet="snippet 2", score=0.85
        ),
        SearchHit(
            id="3", title="Doc 3", url="https://example.com/3", snippet="snippet 3", score=0.75
        ),
    ]

    evaluated_hits = await search_agent._evaluate_relevance(
        query="test query",
        normalized_query="test query normalized",
        hits=hits,
        session_id="test-session",
        timeout_ms=3000,
    )

    # Verify results are sorted by relevance_score descending
    assert len(evaluated_hits) == 3
    assert evaluated_hits[0].relevance_score == 0.9
    assert evaluated_hits[1].relevance_score == 0.6
    assert evaluated_hits[2].relevance_score == 0.3
    assert mock_llm_client.relevance.call_count == 3


@pytest.mark.asyncio
async def test_evaluate_relevance_parallel(search_agent, mock_llm_client):
    """Test parallel relevance evaluation with multiple results."""
    import asyncio
    import time

    from app.core.llm.base import RelevanceOutput

    # Mock 10 relevance evaluations
    mock_llm_client.relevance.side_effect = [
        RelevanceOutput(score=0.9, reason=f"Reason {i}") for i in range(10)
    ]

    hits = [
        SearchHit(
            id=str(i),
            title=f"Doc {i}",
            url=f"https://example.com/{i}",
            snippet=f"snippet {i}",
            score=0.95 - i * 0.05,
        )
        for i in range(10)
    ]

    start = time.time()
    evaluated_hits = await search_agent._evaluate_relevance(
        query="test query",
        normalized_query="test query normalized",
        hits=hits,
        session_id="test-session",
        timeout_ms=45000,
    )
    elapsed = time.time() - start

    # Verify all hits evaluated
    assert len(evaluated_hits) == 10
    assert all(h.relevance_score is not None for h in evaluated_hits)
    assert mock_llm_client.relevance.call_count == 10

    # Verify results sorted by relevance_score (all are 0.9 in this mock)
    scores = [h.relevance_score for h in evaluated_hits]
    assert all(s == 0.9 for s in scores)


@pytest.mark.asyncio
async def test_evaluate_relevance_parallel_partial_failure(search_agent, mock_llm_client):
    """Test parallel evaluation with some failures."""
    from app.core.llm.base import RelevanceOutput

    # Mock mixed success/failure
    mock_llm_client.relevance.side_effect = [
        RelevanceOutput(score=0.9, reason="Success 1"),
        TimeoutError("LLM timeout"),
        RelevanceOutput(score=0.7, reason="Success 2"),
        RuntimeError("LLM error"),
        RelevanceOutput(score=0.6, reason="Success 3"),
    ]

    hits = [
        SearchHit(
            id=str(i),
            title=f"Doc {i}",
            url=f"https://example.com/{i}",
            snippet=f"snippet {i}",
            score=0.9,
        )
        for i in range(5)
    ]

    evaluated_hits = await search_agent._evaluate_relevance(
        query="test query",
        normalized_query="test query normalized",
        hits=hits,
        session_id="test-session",
        timeout_ms=10000,
    )

    # Should have 3 with scores, 2 without
    scored = [h for h in evaluated_hits if h.relevance_score is not None]
    unscored = [h for h in evaluated_hits if h.relevance_score is None]

    assert len(scored) == 3
    assert len(unscored) == 2
    assert len(evaluated_hits) == 5


@pytest.mark.asyncio
async def test_evaluate_relevance_timeout_budget(search_agent, mock_llm_client):
    """Test overall timeout is respected."""
    import asyncio
    import time

    from app.core.llm.base import RelevanceOutput

    async def slow_relevance(*args, **kwargs):
        await asyncio.sleep(2)
        return RelevanceOutput(score=0.5, reason="Slow")

    mock_llm_client.relevance.side_effect = slow_relevance

    hits = [
        SearchHit(
            id=str(i),
            title=f"Doc {i}",
            url=f"https://example.com/{i}",
            snippet="snippet",
            score=0.9,
        )
        for i in range(10)
    ]

    start = time.time()
    # Should timeout after 1 second
    evaluated_hits = await search_agent._evaluate_relevance(
        query="test query",
        normalized_query="test query normalized",
        hits=hits,
        session_id="test-session",
        timeout_ms=1000,
    )
    elapsed = time.time() - start

    # Should return original hits (no evaluation) due to timeout
    assert elapsed < 1.5  # Some overhead allowed
    assert len(evaluated_hits) == 10
    # All hits should have no relevance_score (timeout case returns original hits)
    assert all(h.relevance_score is None for h in evaluated_hits)


@pytest.mark.asyncio
async def test_should_retry():
    """Test _should_retry method."""
    agent = FessSearchAgent(
        search_provider=AsyncMock(),
        llm_client=AsyncMock(),
        intent_timeout_ms=2000,
        search_timeout_ms=2000,
    )

    # Test: should retry when max score below threshold
    hits = [
        SearchHit(
            id="1",
            title="Doc 1",
            url="https://example.com/1",
            snippet="snippet",
            relevance_score=0.2,
        )
    ]
    assert agent._should_retry(hits, threshold=0.3, retry_count=0, max_retries=2) is True

    # Test: should not retry when max score meets threshold
    hits[0].relevance_score = 0.5
    assert agent._should_retry(hits, threshold=0.3, retry_count=0, max_retries=2) is False

    # Test: should not retry when max retries reached
    hits[0].relevance_score = 0.2
    assert agent._should_retry(hits, threshold=0.3, retry_count=2, max_retries=2) is False

    # Test: should retry when no hits (0 results)
    assert agent._should_retry([], threshold=0.3, retry_count=0, max_retries=2) is True

    # Test: should not retry when no hits but max retries reached
    assert agent._should_retry([], threshold=0.3, retry_count=2, max_retries=2) is False


@pytest.mark.asyncio
async def test_extract_retry_intent(search_agent, mock_llm_client):
    """Test _extract_retry_intent method."""
    # Mock retry intent extraction
    mock_llm_client.intent.return_value = IntentOutput(
        normalized_query="improved test query",
        filters=None,
        followups=[],
        ambiguity="low",
    )

    hits = [
        SearchHit(
            id="1",
            title="Low relevance doc",
            url="https://example.com/1",
            snippet="snippet",
            relevance_score=0.2,
        )
    ]

    intent = await search_agent._extract_retry_intent(
        query="original query",
        previous_normalized_query="test query",
        hits=hits,
        language="en",
        session_id="test-session",
        timeout_ms=2000,
    )

    assert intent.normalized_query == "improved test query"
    mock_llm_client.intent.assert_called_once()


@pytest.mark.asyncio
async def test_extract_retry_intent_no_results(search_agent, mock_llm_client):
    """Test _extract_retry_intent method with 0 results."""
    # Mock retry intent extraction for no results
    mock_llm_client.intent.return_value = IntentOutput(
        normalized_query="broader search query",
        filters=None,
        followups=[],
        ambiguity="medium",
    )

    # Empty hits list (0 results)
    hits = []

    intent = await search_agent._extract_retry_intent(
        query="very specific query",
        previous_normalized_query="specific query",
        hits=hits,
        language="en",
        session_id="test-session",
        timeout_ms=2000,
    )

    assert intent.normalized_query == "broader search query"
    mock_llm_client.intent.assert_called_once()
    # Verify that the no-results template was used (check the prompt contains "0 results")
    call_args = mock_llm_client.intent.call_args
    assert "0 results" in call_args.kwargs["user_template"]
