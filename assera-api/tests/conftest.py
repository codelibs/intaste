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

"""Pytest fixtures and configuration"""

# Set required environment variables before importing app modules
# This prevents ValidationError when Settings() is instantiated globally in app.main
import os
os.environ.setdefault("ASSERA_API_TOKEN", "test-token-32-characters-long-secure")

import pytest
from typing import AsyncGenerator
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.core.config import Settings
from app.core.search_agent.base import SearchAgent, SearchAgentResult, SearchAgentTimings
from app.core.search_provider.base import SearchProvider, SearchResult, SearchQuery, SearchHit
from app.core.llm.base import LLMClient, IntentOutput, ComposeOutput


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings with safe defaults"""
    return Settings(
        assera_api_token="test-token-32-characters-long-secure",
        fess_base_url="http://test-fess:8080",
        ollama_base_url="http://test-ollama:11434",
        req_timeout_ms=5000,
        assera_default_model="test-model",
        cors_origins=["http://localhost:3000"],
        log_level="DEBUG",
    )


@pytest.fixture
def mock_search_provider() -> AsyncMock:
    """Mock SearchProvider for testing"""
    provider = AsyncMock(spec=SearchProvider)

    # Default search response
    provider.search.return_value = SearchResult(
        hits=[
            SearchHit(
                id="doc1",
                title="Test Document 1",
                snippet="This is a <em>test</em> document snippet",
                url="http://example.com/doc1",
                score=0.95,
                meta={"site": "example.com", "type": "html"},
            ),
            SearchHit(
                id="doc2",
                title="Test Document 2",
                snippet="Another test document with relevant information",
                url="http://example.com/doc2",
                score=0.85,
                meta={"site": "example.com", "type": "pdf"},
            ),
        ],
        total=2,
        page=1,
        size=5,
        took_ms=150,
    )

    # Default health response
    provider.health.return_value = (True, {"status": "healthy"})

    return provider


@pytest.fixture
def mock_llm_client() -> AsyncMock:
    """Mock LLMClient for testing"""
    client = AsyncMock(spec=LLMClient)

    # Default intent response
    client.intent.return_value = IntentOutput(
        normalized_query="test query optimized",
        filters=None,
        followups=["What else?", "Tell me more"],
        ambiguity="low",
    )

    # Default compose response
    client.compose.return_value = ComposeOutput(
        text="This is a test answer based on the search results [1][2].",
        suggested_questions=["How can I learn more?", "What are the benefits?"],
    )

    # Default health response
    client.health.return_value = (True, {"status": "healthy", "model": "test-model"})

    return client


@pytest.fixture
def mock_search_agent(mock_search_provider: AsyncMock, mock_llm_client: AsyncMock) -> AsyncMock:
    """Mock SearchAgent for testing"""
    from app.core.search_agent.base import SearchEvent, IntentEventData, CitationsEventData

    agent = AsyncMock(spec=SearchAgent)

    # Default search result
    agent.search.return_value = SearchAgentResult(
        hits=[
            SearchHit(
                id="doc1",
                title="Test Document 1",
                snippet="This is a <em>test</em> document snippet",
                url="http://example.com/doc1",
                score=0.95,
                meta={"site": "example.com", "type": "html"},
            ),
            SearchHit(
                id="doc2",
                title="Test Document 2",
                snippet="Another test document with relevant information",
                url="http://example.com/doc2",
                score=0.85,
                meta={"site": "example.com", "type": "pdf"},
            ),
        ],
        total=2,
        normalized_query="test query optimized",
        original_query="test query",
        followups=["What else?", "Tell me more"],
        filters=None,
        timings=SearchAgentTimings(intent_ms=100, search_ms=150),
        notice=None,
        ambiguity="low",
    )

    # Default search_stream async generator
    async def mock_search_stream(query: str, options: dict | None = None):
        # Get intent output from mock_llm_client if available
        intent_output = None
        # Check for side_effect first (e.g., exceptions)
        if hasattr(mock_llm_client.intent, 'side_effect') and mock_llm_client.intent.side_effect is not None:
            # If side_effect is set (e.g., exception), use fallback
            try:
                intent_output = await mock_llm_client.intent(query=query)
            except Exception:
                # Fallback intent
                intent_output = IntentOutput(
                    normalized_query=query.strip(),
                    filters=None,
                    followups=[],
                    ambiguity="medium",
                )
        elif hasattr(mock_llm_client.intent, 'return_value') and mock_llm_client.intent.return_value is not None:
            intent_output = mock_llm_client.intent.return_value
        else:
            # Default intent
            intent_output = IntentOutput(
                normalized_query="test query optimized",
                filters=None,
                followups=["What else?", "Tell me more"],
                ambiguity="low",
            )

        # Yield intent event
        yield SearchEvent(
            type="intent",
            data=IntentEventData(
                normalized_query=intent_output.normalized_query,
                filters=intent_output.filters,
                followups=intent_output.followups,
                ambiguity=intent_output.ambiguity,
                timing_ms=100,
            ),
        )

        # Get search result from mock_search_provider if available
        search_result = None
        if hasattr(mock_search_provider.search, 'return_value'):
            search_result = mock_search_provider.search.return_value
        else:
            # Default search result
            search_result = SearchResult(
                hits=[
                    SearchHit(
                        id="doc1",
                        title="Test Document 1",
                        snippet="This is a <em>test</em> document snippet",
                        url="http://example.com/doc1",
                        score=0.95,
                        meta={"site": "example.com", "type": "html"},
                    ),
                ],
                total=1,
                page=1,
                size=5,
                took_ms=150,
            )

        # Yield citations event
        yield SearchEvent(
            type="citations",
            data=CitationsEventData(
                hits=search_result.hits,
                total=search_result.total,
                timing_ms=150,
            ),
        )

    agent.search_stream = mock_search_stream

    # Default health response
    agent.health.return_value = (True, {"status": "healthy"})

    return agent


@pytest.fixture
def assist_service(mock_search_agent: AsyncMock, mock_llm_client: AsyncMock):
    """Create AssistService with mocked dependencies"""
    from app.services.assist import AssistService

    return AssistService(
        search_agent=mock_search_agent,
        llm_client=mock_llm_client,
    )


@pytest.fixture
def client() -> TestClient:
    """Create FastAPI test client"""
    return TestClient(app)


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for testing"""
    from httpx import ASGITransport
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture
def auth_headers(test_settings: Settings) -> dict[str, str]:
    """Create authentication headers for testing"""
    return {
        "X-Assera-Token": test_settings.assera_api_token,
        "Content-Type": "application/json",
    }


@pytest.fixture
def sample_query_request() -> dict:
    """Sample query request payload"""
    return {
        "query": "What is the company security policy?",
        "options": {
            "max_results": 5,
        },
    }


@pytest.fixture
def sample_feedback_request() -> dict:
    """Sample feedback request payload"""
    return {
        "session_id": "00000000-0000-0000-0000-000000000001",
        "turn": 1,
        "rating": "up",
        "comment": "Very helpful response",
    }
