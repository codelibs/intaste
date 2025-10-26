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
from app.core.llm.prompts import INTENT_SYSTEM_PROMPT, INTENT_USER_TEMPLATE


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
        result = await ollama_client.intent(
            "What is the company security policy?",
            INTENT_SYSTEM_PROMPT,
            INTENT_USER_TEMPLATE,
        )

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
        result = await ollama_client.intent(
            "test query",
            INTENT_SYSTEM_PROMPT,
            INTENT_USER_TEMPLATE,
        )

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
        result = await ollama_client.intent(
            "test query",
            INTENT_SYSTEM_PROMPT,
            INTENT_USER_TEMPLATE,
        )

        assert result.normalized_query == "test query"
        assert result.ambiguity == "low"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_intent_with_query_history(ollama_client):
    """Test intent extraction with query history"""
    mock_response = {
        "normalized_query": "security policy version 2",
        "filters": {},
        "followups": ["What changed?"],
        "ambiguity": "low",
    }

    query_history = [
        "What is the security policy?",
        "Where can I find it?",
    ]

    with patch.object(
        ollama_client, "_complete", return_value=json.dumps(mock_response)
    ) as mock_complete:
        result = await ollama_client.intent(
            "Show me version 2",
            INTENT_SYSTEM_PROMPT,
            INTENT_USER_TEMPLATE,
            query_history=query_history,
        )

        assert isinstance(result, IntentOutput)
        assert result.normalized_query == "security policy version 2"

        # Verify that query history was included in the prompt
        call_args = mock_complete.call_args
        user_prompt = call_args.kwargs['user']  # user keyword argument
        assert "Previous queries" in user_prompt
        assert "What is the security policy?" in user_prompt
        assert "Where can I find it?" in user_prompt


@pytest.mark.unit
@pytest.mark.asyncio
async def test_intent_without_query_history(ollama_client):
    """Test intent extraction without query history"""
    mock_response = {
        "normalized_query": "test query",
        "filters": {},
        "followups": [],
        "ambiguity": "low",
    }

    with patch.object(
        ollama_client, "_complete", return_value=json.dumps(mock_response)
    ) as mock_complete:
        result = await ollama_client.intent(
            "test query",
            INTENT_SYSTEM_PROMPT,
            INTENT_USER_TEMPLATE,
            query_history=None,
        )

        assert isinstance(result, IntentOutput)

        # Verify that "No previous queries" message was included
        call_args = mock_complete.call_args
        user_prompt = call_args.kwargs['user']  # user keyword argument
        assert "No previous queries" in user_prompt


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
async def test_compose_with_language(ollama_client):
    """Test compose with language parameter"""
    mock_response_ja = {
        "text": "検索結果が表示されています。詳細は各ソースをご確認ください。",
        "suggested_questions": ["パスワードの要件は何ですか？", "パスワードの変更頻度は？"],
    }

    with patch.object(
        ollama_client, "_complete", return_value=json.dumps(mock_response_ja)
    ) as mock_complete:
        result = await ollama_client.compose(
            query="パスワードポリシーは何ですか？",
            normalized_query="パスワードポリシー",
            citations_data=[
                {"title": "Policy 1", "snippet": "強力なパスワードが必要", "url": "http://example.com/1"},
            ],
            language="ja",
        )

        # Verify _complete was called
        assert mock_complete.called
        # Verify the user prompt includes the language
        call_args = mock_complete.call_args
        assert "ja" in call_args.kwargs["user"].lower()

        assert isinstance(result, ComposeOutput)
        assert "検索結果" in result.text or "ソース" in result.text


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


@pytest.mark.unit
@pytest.mark.asyncio
async def test_relevance_success(ollama_client):
    """Test successful relevance evaluation"""
    from app.core.llm.base import RelevanceOutput
    from app.core.llm.prompts import RELEVANCE_SYSTEM_PROMPT, RELEVANCE_USER_TEMPLATE

    mock_response = {
        "score": 0.85,
        "reason": "The search result closely matches the user's query intent.",
    }

    search_result = {
        "title": "Security Policy Document",
        "snippet": "Our company's security policy covers all aspects...",
        "url": "https://example.com/security-policy",
    }

    with patch.object(
        ollama_client, "_complete", return_value=json.dumps(mock_response)
    ):
        result = await ollama_client.relevance(
            query="What is the company security policy?",
            normalized_query="company security policy",
            search_result=search_result,
            system_prompt=RELEVANCE_SYSTEM_PROMPT,
            user_template=RELEVANCE_USER_TEMPLATE,
        )

        assert isinstance(result, RelevanceOutput)
        assert result.score == 0.85
        assert "closely matches" in result.reason


@pytest.mark.unit
@pytest.mark.asyncio
async def test_relevance_fallback_on_error(ollama_client):
    """Test relevance fallback when evaluation fails"""
    from app.core.llm.base import RelevanceOutput
    from app.core.llm.prompts import RELEVANCE_SYSTEM_PROMPT, RELEVANCE_USER_TEMPLATE

    search_result = {
        "title": "Test Document",
        "snippet": "Test content",
        "url": "https://example.com/test",
    }

    # Both attempts fail
    with patch.object(ollama_client, "_complete", side_effect=Exception("LLM error")):
        result = await ollama_client.relevance(
            query="test query",
            normalized_query="test query",
            search_result=search_result,
            system_prompt=RELEVANCE_SYSTEM_PROMPT,
            user_template=RELEVANCE_USER_TEMPLATE,
        )

        # Should fallback to neutral score
        assert isinstance(result, RelevanceOutput)
        assert result.score == 0.5
        assert "Unable to evaluate" in result.reason


@pytest.mark.unit
@pytest.mark.asyncio
async def test_relevance_retry_on_json_error(ollama_client):
    """Test relevance retry with lower temperature on JSON error"""
    from app.core.llm.base import RelevanceOutput
    from app.core.llm.prompts import RELEVANCE_SYSTEM_PROMPT, RELEVANCE_USER_TEMPLATE

    search_result = {
        "title": "Test Document",
        "snippet": "Test content",
        "url": "https://example.com/test",
    }

    valid_response = {"score": 0.7, "reason": "Moderately relevant"}

    # First call returns invalid JSON, second call succeeds
    with patch.object(
        ollama_client,
        "_complete",
        side_effect=[
            "invalid json",  # First attempt fails
            json.dumps(valid_response),  # Retry succeeds
        ],
    ):
        result = await ollama_client.relevance(
            query="test query",
            normalized_query="test query",
            search_result=search_result,
            system_prompt=RELEVANCE_SYSTEM_PROMPT,
            user_template=RELEVANCE_USER_TEMPLATE,
        )

        assert isinstance(result, RelevanceOutput)
        assert result.score == 0.7
        assert result.reason == "Moderately relevant"
