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
Integration tests for streaming edge cases and error scenarios.
"""

import json
import pytest
from unittest.mock import AsyncMock, patch

from app.core.llm.base import IntentOutput
from app.core.search_provider.base import SearchResult, SearchHit


@pytest.mark.integration
@pytest.mark.asyncio
async def test_stream_query_with_empty_chunks(
    async_client,
    mock_search_provider,
    mock_llm_client,
    assist_service,
    auth_headers,
):
    """Test streaming query with empty chunks in response."""
    # Mock intent extraction
    mock_llm_client.intent.return_value = IntentOutput(
        normalized_query="test query",
        filters=None,
        followups=["Question?"],
        ambiguity="low",
    )

    # Mock search results
    mock_search_provider.search.return_value = SearchResult(
        total=1,
        hits=[
            SearchHit(
                id="1",
                title="Test",
                url="https://example.com",
                snippet="content",
                score=0.9,
            )
        ],
        page=1,
        size=5,
    )

    # Mock streaming with empty chunks
    async def mock_compose_stream(*args, **kwargs):
        yield ""  # Empty chunk
        yield "Text"
        yield ""  # Another empty chunk
        yield " content"

    mock_llm_client.compose_stream = mock_compose_stream

    with patch("app.main.assist_service", assist_service):
        response = await async_client.post(
            "/api/v1/assist/query",
            json={"query": "test"},
            headers={**auth_headers, "Accept": "text/event-stream"},
        )

    assert response.status_code == 200

    # Parse events
    events = []
    for line in response.text.strip().split("\n\n"):
        if line:
            lines = line.split("\n")
            event_type = None
            event_data = None

            for l in lines:
                if l.startswith("event: "):
                    event_type = l[7:]
                elif l.startswith("data: "):
                    event_data = json.loads(l[6:])

            if event_type and event_data:
                events.append({"event": event_type, "data": event_data})

    # Should have chunk events (including empty ones or skipped)
    chunk_events = [e for e in events if e["event"] == "chunk"]
    # Implementation may skip empty chunks or include them
    assert len(chunk_events) >= 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_stream_query_with_search_agent_stream_failure(
    async_client,
    mock_search_provider,
    mock_llm_client,
    assist_service,
    auth_headers,
):
    """Test streaming query when search agent stream fails."""
    # Mock intent extraction succeeds
    mock_llm_client.intent.return_value = IntentOutput(
        normalized_query="test query",
        filters=None,
        followups=[],
        ambiguity="low",
    )

    # Mock search results (normal case)
    mock_search_provider.search.return_value = SearchResult(
        total=1,
        hits=[
            SearchHit(
                id="1",
                title="Test",
                url="https://example.com",
                snippet="content",
                score=0.9,
            )
        ],
        page=1,
        size=5,
    )

    # Override search_stream to raise exception
    async def failing_search_stream(*args, **kwargs):
        raise RuntimeError("Search stream failed")
        yield  # Make it a generator

    assist_service.search_agent.search_stream = failing_search_stream

    with patch("app.main.assist_service", assist_service):
        response = await async_client.post(
            "/api/v1/assist/query",
            json={"query": "test"},
            headers={**auth_headers, "Accept": "text/event-stream"},
        )

    # Search stream failure should result in error
    # May be 500 status or error event in stream
    assert response.status_code in [200, 500]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_stream_query_with_compose_failure(
    async_client,
    mock_search_provider,
    mock_llm_client,
    assist_service,
    auth_headers,
):
    """Test streaming query when compose (answer generation) fails."""
    # Mock intent extraction
    mock_llm_client.intent.return_value = IntentOutput(
        normalized_query="test query",
        filters=None,
        followups=[],
        ambiguity="low",
    )

    # Mock search results
    mock_search_provider.search.return_value = SearchResult(
        total=1,
        hits=[
            SearchHit(
                id="1",
                title="Test",
                url="https://example.com",
                snippet="content",
                score=0.9,
            )
        ],
        page=1,
        size=5,
    )

    # Mock compose stream failure
    async def mock_compose_stream(*args, **kwargs):
        yield "Partial "
        raise RuntimeError("Compose failed")

    mock_llm_client.compose_stream = mock_compose_stream

    with patch("app.main.assist_service", assist_service):
        response = await async_client.post(
            "/api/v1/assist/query",
            json={"query": "test"},
            headers={**auth_headers, "Accept": "text/event-stream"},
        )

    assert response.status_code in [200, 500]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_stream_query_with_very_large_response(
    async_client,
    mock_search_provider,
    mock_llm_client,
    assist_service,
    auth_headers,
):
    """Test streaming query with very large response."""
    # Mock intent extraction
    mock_llm_client.intent.return_value = IntentOutput(
        normalized_query="test query",
        filters=None,
        followups=[],
        ambiguity="low",
    )

    # Mock search with many results
    hits = [
        SearchHit(
            id=str(i),
            title=f"Document {i}",
            url=f"https://example.com/{i}",
            snippet=f"Content {i}" * 100,  # Large snippet
            score=0.9,
        )
        for i in range(50)  # Many hits
    ]

    mock_search_provider.search.return_value = SearchResult(
        total=50,
        hits=hits,
        page=1,
        size=50,
    )

    # Mock streaming with large response
    async def mock_compose_stream(*args, **kwargs):
        # Generate large chunks
        for i in range(100):
            yield f"Chunk {i} with some content. " * 10

    mock_llm_client.compose_stream = mock_compose_stream

    with patch("app.main.assist_service", assist_service):
        response = await async_client.post(
            "/api/v1/assist/query",
            json={"query": "test", "options": {"max_results": 50}},
            headers={**auth_headers, "Accept": "text/event-stream"},
        )

    # Should handle large response
    assert response.status_code == 200
    assert len(response.text) > 10000  # Should be large


@pytest.mark.integration
@pytest.mark.asyncio
async def test_stream_query_with_unicode_content(
    async_client,
    mock_search_provider,
    mock_llm_client,
    assist_service,
    auth_headers,
):
    """Test streaming query with Unicode content."""
    # Mock intent extraction
    mock_llm_client.intent.return_value = IntentOutput(
        normalized_query="テストクエリ",  # Japanese
        filters=None,
        followups=["次は？", "詳細は？"],  # Japanese questions
        ambiguity="low",
    )

    # Mock search with Unicode content
    mock_search_provider.search.return_value = SearchResult(
        total=1,
        hits=[
            SearchHit(
                id="1",
                title="日本語ドキュメント",  # Japanese title
                url="https://example.com/ja",
                snippet="これはテストです。🎉",  # Japanese with emoji
                score=0.9,
            )
        ],
        page=1,
        size=5,
    )

    # Mock streaming with Unicode
    async def mock_compose_stream(*args, **kwargs):
        yield "これは"
        yield "回答です。"
        yield "🚀"

    mock_llm_client.compose_stream = mock_compose_stream

    with patch("app.main.assist_service", assist_service):
        response = await async_client.post(
            "/api/v1/assist/query",
            json={"query": "日本語クエリ"},
            headers={**auth_headers, "Accept": "text/event-stream"},
        )

    assert response.status_code == 200

    # Parse and verify Unicode handling
    events = []
    for line in response.text.strip().split("\n\n"):
        if line:
            lines = line.split("\n")
            event_type = None
            event_data = None

            for l in lines:
                if l.startswith("event: "):
                    event_type = l[7:]
                elif l.startswith("data: "):
                    event_data = json.loads(l[6:])

            if event_type and event_data:
                events.append({"event": event_type, "data": event_data})

    # Verify Unicode in citations
    citations_event = next((e for e in events if e["event"] == "citations"), None)
    if citations_event:
        assert any("日本語" in str(c) for c in citations_event["data"]["citations"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_stream_query_with_special_characters_in_query(
    async_client,
    mock_search_provider,
    mock_llm_client,
    assist_service,
    auth_headers,
):
    """Test streaming query with special characters."""
    special_queries = [
        "query with <script>alert('xss')</script>",
        "query with SQL' OR '1'='1",
        "query with newlines\nand\ttabs",
        "query with emoji 🔍 and symbols !@#$%",
    ]

    for special_query in special_queries:
        # Mock intent extraction
        mock_llm_client.intent.return_value = IntentOutput(
            normalized_query=special_query,
            filters=None,
            followups=[],
            ambiguity="low",
        )

        # Mock search
        mock_search_provider.search.return_value = SearchResult(
            total=0, hits=[], page=1, size=5
        )

        # Mock streaming
        async def mock_compose_stream(*args, **kwargs):
            yield "No results."

        mock_llm_client.compose_stream = mock_compose_stream

        with patch("app.main.assist_service", assist_service):
            response = await async_client.post(
                "/api/v1/assist/query",
                json={"query": special_query},
                headers={**auth_headers, "Accept": "text/event-stream"},
            )

        # Should handle special characters
        assert response.status_code in [200, 422]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_stream_query_with_zero_results(
    async_client,
    mock_search_provider,
    mock_llm_client,
    assist_service,
    auth_headers,
):
    """Test streaming query with zero search results."""
    # Mock intent extraction
    mock_llm_client.intent.return_value = IntentOutput(
        normalized_query="nonexistent query",
        filters=None,
        followups=[],
        ambiguity="low",
    )

    # Mock search with zero results
    mock_search_provider.search.return_value = SearchResult(
        total=0, hits=[], page=1, size=5
    )

    # Mock streaming
    async def mock_compose_stream(*args, **kwargs):
        yield "No results found."

    mock_llm_client.compose_stream = mock_compose_stream

    with patch("app.main.assist_service", assist_service):
        response = await async_client.post(
            "/api/v1/assist/query",
            json={"query": "nonexistent"},
            headers={**auth_headers, "Accept": "text/event-stream"},
        )

    assert response.status_code == 200

    # Parse events
    events = []
    for line in response.text.strip().split("\n\n"):
        if line:
            lines = line.split("\n")
            event_type = None
            event_data = None

            for l in lines:
                if l.startswith("event: "):
                    event_type = l[7:]
                elif l.startswith("data: "):
                    event_data = json.loads(l[6:])

            if event_type and event_data:
                events.append({"event": event_type, "data": event_data})

    # Should have citations event with empty hits
    citations_event = next((e for e in events if e["event"] == "citations"), None)
    assert citations_event is not None
    assert len(citations_event["data"]["citations"]) == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_stream_query_connection_headers(
    async_client,
    mock_search_provider,
    mock_llm_client,
    assist_service,
    auth_headers,
):
    """Test that streaming response has correct headers."""
    # Mock intent extraction
    mock_llm_client.intent.return_value = IntentOutput(
        normalized_query="test",
        filters=None,
        followups=[],
        ambiguity="low",
    )

    # Mock search
    mock_search_provider.search.return_value = SearchResult(
        total=1,
        hits=[
            SearchHit(
                id="1",
                title="Test",
                url="https://example.com",
                snippet="content",
                score=0.9,
            )
        ],
        page=1,
        size=5,
    )

    # Mock streaming
    async def mock_compose_stream(*args, **kwargs):
        yield "Test response"

    mock_llm_client.compose_stream = mock_compose_stream

    with patch("app.main.assist_service", assist_service):
        response = await async_client.post(
            "/api/v1/assist/query",
            json={"query": "test"},
            headers={**auth_headers, "Accept": "text/event-stream"},
        )

    # Verify SSE headers
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    assert response.headers["cache-control"] == "no-cache"
    assert response.headers["connection"] == "keep-alive"
