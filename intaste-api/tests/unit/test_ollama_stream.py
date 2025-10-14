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
Unit tests for Ollama streaming functionality.
"""

import json

import httpx
import pytest
from httpx import Response

from app.core.llm.ollama import OllamaClient


@pytest.fixture
def ollama_client(httpx_mock):
    """Create an Ollama client for testing."""
    return OllamaClient(
        base_url="http://localhost:11434",
        model="llama3",
        timeout_ms=30000,
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_compose_stream_success(ollama_client, httpx_mock):
    """Test successful streaming composition."""
    # Mock streaming response with NDJSON lines
    stream_data = [
        {"message": {"content": "This "}, "done": False},
        {"message": {"content": "is "}, "done": False},
        {"message": {"content": "a "}, "done": False},
        {"message": {"content": "test."}, "done": False},
        {"done": True},
    ]

    # Convert to NDJSON format
    ndjson_content = "\n".join(json.dumps(item) for item in stream_data)

    httpx_mock.add_response(
        url="http://localhost:11434/api/chat",
        method="POST",
        status_code=200,
        content=ndjson_content.encode("utf-8"),
    )

    # Collect streamed chunks
    chunks = []
    async for chunk in ollama_client.compose_stream(
        query="What is the test?",
        normalized_query="test",
        citations_data=[{"id": 1, "title": "Test Doc", "content": "Test content"}],
    ):
        chunks.append(chunk)

    # Verify all chunks received
    assert chunks == ["This ", "is ", "a ", "test."]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_compose_stream_empty_chunks(ollama_client, httpx_mock):
    """Test streaming with empty content chunks."""
    stream_data = [
        {"message": {"content": ""}, "done": False},  # Empty chunk
        {"message": {"content": "Hello"}, "done": False},
        {"message": {"content": ""}, "done": False},  # Empty chunk
        {"message": {"content": " world"}, "done": False},
        {"done": True},
    ]

    ndjson_content = "\n".join(json.dumps(item) for item in stream_data)

    httpx_mock.add_response(
        url="http://localhost:11434/api/chat",
        method="POST",
        status_code=200,
        content=ndjson_content.encode("utf-8"),
    )

    chunks = []
    async for chunk in ollama_client.compose_stream(
        query="Test",
        normalized_query="test",
        citations_data=[],
    ):
        chunks.append(chunk)

    # Empty chunks should be filtered out
    assert chunks == ["Hello", " world"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_compose_stream_malformed_json(ollama_client, httpx_mock):
    """Test handling of malformed JSON in stream."""
    # Mix valid and invalid JSON
    ndjson_content = (
        '{"message": {"content": "Valid"}, "done": false}\n'
        'invalid json line\n'
        '{"message": {"content": " chunk"}, "done": false}\n'
        '{"done": true}\n'
    )

    httpx_mock.add_response(
        url="http://localhost:11434/api/chat",
        method="POST",
        status_code=200,
        content=ndjson_content.encode("utf-8"),
    )

    chunks = []
    async for chunk in ollama_client.compose_stream(
        query="Test",
        normalized_query="test",
        citations_data=[],
    ):
        chunks.append(chunk)

    # Should continue processing valid chunks
    assert "Valid" in chunks
    assert " chunk" in chunks


@pytest.mark.unit
@pytest.mark.asyncio
async def test_compose_stream_http_error(ollama_client, httpx_mock):
    """Test streaming with HTTP error response."""
    httpx_mock.add_response(
        url="http://localhost:11434/api/chat",
        method="POST",
        status_code=500,
        content=b'{"error": "Internal server error"}',
    )

    chunks = []
    async for chunk in ollama_client.compose_stream(
        query="Test",
        normalized_query="test",
        citations_data=[],
    ):
        chunks.append(chunk)

    # Should yield fallback message on error
    assert len(chunks) > 0
    assert any("error" in chunk.lower() or "unable" in chunk.lower() for chunk in chunks)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_compose_stream_timeout(ollama_client, httpx_mock):
    """Test streaming with timeout."""
    httpx_mock.add_exception(
        httpx.TimeoutException("Request timeout"),
        url="http://localhost:11434/api/chat",
        method="POST",
    )

    chunks = []
    async for chunk in ollama_client.compose_stream(
        query="Test",
        normalized_query="test",
        citations_data=[],
        timeout_ms=1000,
    ):
        chunks.append(chunk)

    # Should yield fallback message on timeout
    assert len(chunks) > 0
    assert any("error" in chunk.lower() or "unable" in chunk.lower() for chunk in chunks)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_compose_stream_with_followups(ollama_client, httpx_mock):
    """Test streaming with follow-up suggestions."""
    stream_data = [
        {"message": {"content": "Answer text"}, "done": False},
        {"done": True},
    ]

    ndjson_content = "\n".join(json.dumps(item) for item in stream_data)

    httpx_mock.add_response(
        url="http://localhost:11434/api/chat",
        method="POST",
        status_code=200,
        content=ndjson_content.encode("utf-8"),
    )

    chunks = []
    async for chunk in ollama_client.compose_stream(
        query="Test",
        normalized_query="test",
        citations_data=[{"id": 1, "title": "Doc", "content": "Content"}],
        followups=["Follow-up 1", "Follow-up 2"],
    ):
        chunks.append(chunk)

    assert "Answer text" in chunks


@pytest.mark.unit
@pytest.mark.asyncio
async def test_compose_stream_unicode(ollama_client, httpx_mock):
    """Test streaming with Unicode characters."""
    stream_data = [
        {"message": {"content": "日本語 "}, "done": False},
        {"message": {"content": "テスト "}, "done": False},
        {"message": {"content": "🚀"}, "done": False},
        {"done": True},
    ]

    ndjson_content = "\n".join(json.dumps(item, ensure_ascii=False) for item in stream_data)

    httpx_mock.add_response(
        url="http://localhost:11434/api/chat",
        method="POST",
        status_code=200,
        content=ndjson_content.encode("utf-8"),
    )

    chunks = []
    async for chunk in ollama_client.compose_stream(
        query="Test",
        normalized_query="test",
        citations_data=[],
    ):
        chunks.append(chunk)

    assert chunks == ["日本語 ", "テスト ", "🚀"]
