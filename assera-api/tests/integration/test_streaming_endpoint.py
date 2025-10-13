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
Integration tests for streaming API endpoint.
"""

import json
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from app.core.llm.base import IntentOutput
from app.core.search_provider.base import SearchResult, SearchHit


@pytest.mark.integration
@pytest.mark.asyncio
async def test_stream_query_success(
    async_client: AsyncClient,
    mock_search_provider: AsyncMock,
    mock_llm_client: AsyncMock,
    assist_service,
    auth_headers: dict,
):
    """Test successful streaming query."""
    # Mock intent extraction
    mock_llm_client.intent.return_value = IntentOutput(
        normalized_query="test query",
        filters=None,
        followups=["How can I test more?"],
        ambiguity="low",
    )

    # Mock search results
    mock_search_provider.search.return_value = SearchResult(
        total=1,
        hits=[
            SearchHit(
                id="1",
                title="Test Document",
                url="https://example.com/doc",
                snippet="Test content",
                score=0.95,
            )
        ],
        page=1,
        size=5,
    )

    # Mock streaming response
    async def mock_compose_stream(*args, **kwargs):
        yield "This "
        yield "is "
        yield "a "
        yield "test."

    mock_llm_client.compose_stream = mock_compose_stream

    # Patch the assist service
    from unittest.mock import patch
    with patch("app.main.assist_service", assist_service):
        # Make streaming request
        response = await async_client.post(
            "/api/v1/assist/query/stream",
            json={"query": "What is a test?"},
            headers={
                **auth_headers,
                "Accept": "text/event-stream",
            },
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    assert response.headers["cache-control"] == "no-cache"
    assert response.headers["connection"] == "keep-alive"

    # Parse SSE events
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

    # Verify event sequence
    event_types = [e["event"] for e in events]
    assert "start" in event_types
    assert "intent" in event_types
    assert "citations" in event_types
    assert "chunk" in event_types
    assert "complete" in event_types

    # Verify chunk events contain text
    chunks = [e["data"]["text"] for e in events if e["event"] == "chunk"]
    assert chunks == ["This ", "is ", "a ", "test."]

    # Verify citations event
    citations_event = next(e for e in events if e["event"] == "citations")
    assert len(citations_event["data"]["citations"]) == 1
    assert citations_event["data"]["citations"][0]["title"] == "Test Document"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_stream_query_no_auth(
    async_client: AsyncClient,
    assist_service,
):
    """Test streaming query without authentication."""
    from unittest.mock import patch

    with patch("app.main.assist_service", assist_service):
        response = await async_client.post(
            "/api/v1/assist/query/stream",
            json={"query": "test"},
            headers={"Accept": "text/event-stream"},
        )

    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_stream_query_empty_query(
    async_client: AsyncClient,
    assist_service,
    auth_headers: dict,
):
    """Test streaming query with empty query string."""
    from unittest.mock import patch

    with patch("app.main.assist_service", assist_service):
        response = await async_client.post(
            "/api/v1/assist/query/stream",
            json={"query": ""},
            headers={**auth_headers, "Accept": "text/event-stream"},
        )

    assert response.status_code == 422  # Validation error


@pytest.mark.integration
@pytest.mark.asyncio
async def test_stream_query_intent_fallback(
    async_client: AsyncClient,
    mock_search_provider: AsyncMock,
    mock_llm_client: AsyncMock,
    assist_service,
    auth_headers: dict,
):
    """Test streaming query with intent extraction fallback."""
    # Mock intent extraction to fail
    mock_llm_client.intent.side_effect = Exception("Intent failed")

    # Mock search results
    mock_search_provider.search.return_value = SearchResult(
        total=1,
        hits=[
            SearchHit(
                id="1",
                title="Fallback Document",
                url="https://example.com/fallback",
                snippet="Fallback content",
                score=0.8,
            )
        ],
        page=1,
        size=5,
    )

    # Mock streaming response
    async def mock_compose_stream(*args, **kwargs):
        yield "Fallback answer."

    mock_llm_client.compose_stream = mock_compose_stream

    # Patch the assist service
    from unittest.mock import patch
    with patch("app.main.assist_service", assist_service):
        # Make streaming request
        response = await async_client.post(
            "/api/v1/assist/query/stream",
            json={"query": "test fallback"},
            headers={
                **auth_headers,
                "Accept": "text/event-stream",
            },
        )

    assert response.status_code == 200

    # Parse SSE events
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

    # Intent event should NOT be present due to fallback
    event_types = [e["event"] for e in events]
    assert "start" in event_types
    assert "intent" not in event_types  # Intent failed, so no intent event
    assert "citations" in event_types
    assert "complete" in event_types

    # Verify complete event has empty followups due to intent failure
    complete_event = next(e for e in events if e["event"] == "complete")
    assert complete_event["data"]["answer"]["suggested_questions"] == []


@pytest.mark.integration
@pytest.mark.asyncio
async def test_stream_query_with_session(
    async_client: AsyncClient,
    mock_search_provider: AsyncMock,
    mock_llm_client: AsyncMock,
    assist_service,
    auth_headers: dict,
):
    """Test streaming query with session context."""
    session_id = "00000000-0000-0000-0000-000000000001"

    # Mock intent extraction
    mock_llm_client.intent.return_value = IntentOutput(
        normalized_query="session query",
        filters=None,
        followups=["What's next?"],
        ambiguity="low",
    )

    # Mock search results
    mock_search_provider.search.return_value = SearchResult(
        total=1,
        hits=[
            SearchHit(
                id="1",
                title="Session Document",
                url="https://example.com/session",
                snippet="Session content",
                score=0.9,
            )
        ],
        page=1,
        size=5,
    )

    # Mock streaming response
    async def mock_compose_stream(*args, **kwargs):
        yield "Session answer."

    mock_llm_client.compose_stream = mock_compose_stream

    # Patch the assist service
    from unittest.mock import patch
    with patch("app.main.assist_service", assist_service):
        # Make streaming request
        response = await async_client.post(
            "/api/v1/assist/query/stream",
            json={"query": "test with session", "session_id": session_id},
            headers={
                **auth_headers,
                "Accept": "text/event-stream",
            },
        )

    assert response.status_code == 200

    # Parse SSE events
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

    # Verify complete event contains session info
    complete_event = next(e for e in events if e["event"] == "complete")
    assert complete_event["data"]["session"]["id"] == session_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_stream_query_error_handling(
    async_client: AsyncClient,
    mock_search_provider: AsyncMock,
    mock_llm_client: AsyncMock,
    assist_service,
    auth_headers: dict,
):
    """Test streaming query with intent extraction error (fallback behavior)."""
    # Mock intent to raise error
    mock_llm_client.intent.side_effect = Exception("Service error")

    # Mock search results for fallback
    mock_search_provider.search.return_value = SearchResult(
        total=1,
        hits=[
            SearchHit(
                id="1",
                title="Fallback Document",
                url="https://example.com/fallback",
                snippet="Fallback content",
                score=0.8,
            )
        ],
        page=1,
        size=5,
    )

    # Mock streaming response for fallback
    async def mock_compose_stream(*args, **kwargs):
        yield "Fallback answer."

    mock_llm_client.compose_stream = mock_compose_stream

    from unittest.mock import patch

    with patch("app.main.assist_service", assist_service):
        response = await async_client.post(
            "/api/v1/assist/query/stream",
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

    # Intent extraction error should not produce error event, but use fallback
    event_types = [e["event"] for e in events]
    assert "start" in event_types
    assert "intent" not in event_types  # Intent failed, so no intent event
    assert "citations" in event_types  # Fallback continues with search
    assert "complete" in event_types
    assert "error" not in event_types  # No error event - fallback used instead

    # Verify complete event has empty followups due to intent failure
    complete_event = next(e for e in events if e["event"] == "complete")
    assert complete_event["data"]["answer"]["suggested_questions"] == []
