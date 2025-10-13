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

"""Tests for Ollama LLM client"""

import pytest
from unittest.mock import AsyncMock, patch
import json

from app.core.llm.ollama import OllamaClient
from app.core.llm.base import IntentOutput, ComposeOutput


@pytest.fixture
def ollama_client():
    """Create OllamaClient instance for testing"""
    return OllamaClient(
        base_url="http://test-ollama:11434",
        model="test-model",
        timeout_ms=3000,
        temperature=0.2,
        top_p=0.9,
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_intent_success(ollama_client):
    """Test successful intent extraction"""
    mock_response = {
        "normalized_query": "company security policy latest version",
        "filters": {"site": "example.com"},
        "followups": ["How do I access it?", "When was it updated?"],
        "ambiguity": "low",
    }

    with patch.object(
        ollama_client, "_complete", return_value=json.dumps(mock_response)
    ):
        result = await ollama_client.intent("What is the company security policy?")

        assert isinstance(result, IntentOutput)
        assert result.normalized_query == "company security policy latest version"
        assert result.filters == {"site": "example.com"}
        assert len(result.followups) == 2
        assert result.ambiguity == "low"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_intent_fallback_on_json_error(ollama_client):
    """Test intent fallback when JSON parsing fails"""
    with patch.object(ollama_client, "_complete", return_value="invalid json"):
        result = await ollama_client.intent("test query")

        # Should fallback to original query
        assert result.normalized_query == "test query"
        assert result.ambiguity == "medium"  # Fallback uses "medium" ambiguity


@pytest.mark.unit
@pytest.mark.asyncio
async def test_intent_retry_on_validation_error(ollama_client):
    """Test intent retry with lower temperature on validation error"""
    # First call returns invalid structure, second call succeeds
    valid_response = {
        "normalized_query": "test query",
        "filters": None,
        "followups": ["Next question?"],
        "ambiguity": "low",
    }

    with patch.object(
        ollama_client,
        "_complete",
        side_effect=[
            '{"invalid": "structure"}',  # First attempt fails validation
            json.dumps(valid_response),  # Retry succeeds
        ],
    ):
        result = await ollama_client.intent("test query")

        assert result.normalized_query == "test query"
        assert result.ambiguity == "low"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_compose_success(ollama_client):
    """Test successful answer composition"""
    mock_response = {
        "text": "The company security policy [1] requires strong passwords [2].",
        "suggested_questions": [
            "What are the password requirements?",
            "How often should passwords be changed?",
        ],
    }

    with patch.object(
        ollama_client, "_complete", return_value=json.dumps(mock_response)
    ):
        result = await ollama_client.compose(
            query="What is the password policy?",
            normalized_query="password policy",
            citations_data=[
                {"title": "Policy 1", "snippet": "Strong passwords required", "url": "http://example.com/1"},
                {"title": "Policy 2", "snippet": "Change every 90 days", "url": "http://example.com/2"},
            ],
        )

        assert isinstance(result, ComposeOutput)
        assert "[1]" in result.text or "[2]" in result.text
        assert len(result.suggested_questions) == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_compose_fallback_on_error(ollama_client):
    """Test compose fallback when LLM fails"""
    with patch.object(ollama_client, "_complete", side_effect=Exception("LLM error")):
        result = await ollama_client.compose(
            query="test query",
            normalized_query="test query",
            citations_data=[{"title": "Doc", "snippet": "content", "url": "http://example.com"}],
        )

        # Should return generic fallback message
        assert "results are displayed" in result.text.lower() or "review the sources" in result.text.lower()
        assert result.suggested_questions == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_check_success(ollama_client):
    """Test health check when Ollama is healthy"""
    mock_tags_response = {
        "models": [{"name": "test-model", "size": 1000000}]
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_tags_response

        is_healthy, details = await ollama_client.health()

        assert is_healthy is True
        assert details["status"] == "ok"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_check_failure(ollama_client):
    """Test health check when Ollama is unreachable"""
    with patch("httpx.AsyncClient.get", side_effect=Exception("Connection error")):
        is_healthy, details = await ollama_client.health()

        assert is_healthy is False
        assert "error" in details


@pytest.mark.unit
@pytest.mark.asyncio
async def test_complete_timeout(ollama_client):
    """Test timeout handling in _complete"""
    import asyncio

    with patch("httpx.AsyncClient.post", side_effect=asyncio.TimeoutError()):
        with pytest.raises(Exception):
            await ollama_client._complete("test prompt", timeout_ms=100)
