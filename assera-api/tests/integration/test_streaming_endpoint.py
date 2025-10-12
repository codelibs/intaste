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

from app.models.api import IntentOutput, SearchOutput


@pytest.mark.integration
@pytest.mark.asyncio
async def test_stream_query_success(
    async_client: AsyncClient,
    mock_search_provider: AsyncMock,
    mock_llm_client: AsyncMock,
    auth_headers: dict,
):
    """Test successful streaming query."""
    # Mock intent extraction
    mock_llm_client.intent.return_value = IntentOutput(
        optimized_query="test query",
        keywords=["test"],
        fallback=False,
        reason=None,
    )

    # Mock search results
    mock_search_provider.search.return_value = SearchOutput(
        citations=[
            {
                "id": 1,
                "title": "Test Document",
                "url": "https://example.com/doc",
                "content": "Test content",
                "score": 0.95,
            }
        ],
        metadata={"total": 1, "page": 1},
    )

    # Mock streaming response
    async def mock_compose_stream(*args, **kwargs):
        yield "This "
        yield "is "
        yield "a "
        yield "test."

    mock_llm_client.compose_stream = mock_compose_stream

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
async def test_stream_query_no_auth(async_client: AsyncClient):
    """Test streaming query without authentication."""
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
    auth_headers: dict,
):
    """Test streaming query with empty query string."""
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
    auth_headers: dict,
):
    """Test streaming with intent extraction fallback."""
    # Mock intent fallback
    mock_llm_client.intent.return_value = IntentOutput(
        optimized_query="fallback query",
        keywords=["fallback"],
        fallback=True,
        reason="JSON parsing error",
    )

    # Mock search results
    mock_search_provider.search.return_value = SearchOutput(
        citations=[],
        metadata={"total": 0, "page": 1},
    )

    # Mock streaming response
    async def mock_compose_stream(*args, **kwargs):
        yield "Fallback response"

    mock_llm_client.compose_stream = mock_compose_stream

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

    # Verify intent event contains fallback info
    intent_event = next(e for e in events if e["event"] == "intent")
    assert intent_event["data"]["fallback"] is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_stream_query_with_session(
    async_client: AsyncClient,
    mock_search_provider: AsyncMock,
    mock_llm_client: AsyncMock,
    auth_headers: dict,
):
    """Test streaming query with session continuation."""
    # Mock responses
    mock_llm_client.intent.return_value = IntentOutput(
        optimized_query="test",
        keywords=["test"],
        fallback=False,
        reason=None,
    )

    mock_search_provider.search.return_value = SearchOutput(
        citations=[],
        metadata={"total": 0, "page": 1},
    )

    async def mock_compose_stream(*args, **kwargs):
        yield "Response"

    mock_llm_client.compose_stream = mock_compose_stream

    # First request
    response1 = await async_client.post(
        "/api/v1/assist/query/stream",
        json={"query": "first question"},
        headers={**auth_headers, "Accept": "text/event-stream"},
    )

    assert response1.status_code == 200

    # Extract session ID from complete event
    events = []
    for line in response1.text.strip().split("\n\n"):
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

    complete_event = next(e for e in events if e["event"] == "complete")
    session_id = complete_event["data"]["session"]["id"]
    assert session_id is not None

    # Second request with session
    response2 = await async_client.post(
        "/api/v1/assist/query/stream",
        json={"query": "follow-up question", "session_id": session_id},
        headers={**auth_headers, "Accept": "text/event-stream"},
    )

    assert response2.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_stream_query_error_handling(
    async_client: AsyncClient,
    mock_search_provider: AsyncMock,
    mock_llm_client: AsyncMock,
    auth_headers: dict,
):
    """Test streaming query with service error."""
    # Mock intent to raise error
    mock_llm_client.intent.side_effect = Exception("Service error")

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

    # Should include error event
    assert any(e["event"] == "error" for e in events)
    error_event = next(e for e in events if e["event"] == "error")
    assert "message" in error_event["data"]
