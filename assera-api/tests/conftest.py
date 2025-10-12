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

import pytest
from typing import AsyncGenerator
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.core.config import Settings
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
                metadata={"site": "example.com", "type": "html"},
            ),
            SearchHit(
                id="doc2",
                title="Test Document 2",
                snippet="Another test document with relevant information",
                url="http://example.com/doc2",
                score=0.85,
                metadata={"site": "example.com", "type": "pdf"},
            ),
        ],
        total=2,
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
        optimized_query="test query optimized",
        intent_tags=["search", "information"],
        confidence=0.9,
    )

    # Default compose response
    client.compose.return_value = ComposeOutput(
        answer_text="This is a test answer based on the search results [1][2].",
        citations_used=[0, 1],
        suggested_followups=["How can I learn more?", "What are the benefits?"],
        confidence=0.85,
    )

    # Default health response
    client.health.return_value = (True, {"status": "healthy", "model": "test-model"})

    return client


@pytest.fixture
def client() -> TestClient:
    """Create FastAPI test client"""
    return TestClient(app)


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for testing"""
    async with AsyncClient(app=app, base_url="http://test") as client:
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
        "rating": 5,
        "comment": "Very helpful response",
    }
