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

"""Tests for AssistService"""

import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from app.services.assist import AssistService
from app.core.search_provider.base import SearchResult, SearchHit
from app.core.llm.base import IntentOutput, ComposeOutput


@pytest.fixture
def assist_service(mock_search_provider, mock_llm_client):
    """Create AssistService with mocked dependencies"""
    return AssistService(
        search_provider=mock_search_provider,
        llm_client=mock_llm_client,
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_query_full_flow_success(assist_service, mock_search_provider, mock_llm_client):
    """Test successful query with full intent → search → compose flow"""
    result = await assist_service.query(
        query="What is the security policy?",
        options={"max_results": 5},
    )

    # Verify all stages were called
    mock_llm_client.intent.assert_called_once()
    mock_search_provider.search.assert_called_once()
    mock_llm_client.compose.assert_called_once()

    # Verify response structure
    assert result.answer.text is not None
    assert len(result.citations) == 2
    assert result.session.session_id is not None
    assert result.session.turn == 1
    assert result.timings.total_ms > 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_query_intent_fallback(assist_service, mock_search_provider, mock_llm_client):
    """Test query when intent extraction fails"""
    # Make intent fail
    mock_llm_client.intent.side_effect = Exception("LLM error")

    result = await assist_service.query(
        query="What is the security policy?",
        options={},
    )

    # Should still complete with fallback to original query
    assert result.answer.text is not None
    assert len(result.citations) == 2
    assert result.notice is not None
    assert "intent" in result.notice.type.lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_query_compose_fallback(assist_service, mock_search_provider, mock_llm_client):
    """Test query when answer composition fails"""
    # Make compose fail
    mock_llm_client.compose.side_effect = Exception("LLM error")

    result = await assist_service.query(
        query="What is the security policy?",
        options={},
    )

    # Should still return citations with generic answer
    assert result.answer.text is not None
    assert "found" in result.answer.text.lower()
    assert len(result.citations) == 2
    assert result.notice is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_query_no_search_results(assist_service, mock_search_provider, mock_llm_client):
    """Test query when search returns no results"""
    # Make search return empty results
    mock_search_provider.search.return_value = SearchResult(
        hits=[],
        total=0,
        took_ms=100,
    )

    result = await assist_service.query(
        query="nonexistent query",
        options={},
    )

    # Should return notice about no results
    assert len(result.citations) == 0
    assert result.notice is not None
    assert "no results" in result.notice.message.lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_query_session_continuation(assist_service):
    """Test query continuation in same session"""
    # First query
    result1 = await assist_service.query(
        query="First query",
        options={},
    )
    session_id = result1.session.session_id

    # Second query in same session
    result2 = await assist_service.query(
        query="Second query",
        session_id=session_id,
        options={},
    )

    # Should use same session with incremented turn
    assert result2.session.session_id == session_id
    assert result2.session.turn == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_query_with_options(assist_service, mock_search_provider, mock_llm_client):
    """Test query with custom options"""
    result = await assist_service.query(
        query="Test query",
        options={
            "max_results": 10,
            "site": "example.com",
            "filetype": "pdf",
        },
    )

    # Verify options were passed to search
    search_call = mock_search_provider.search.call_args[0][0]
    assert search_call.size == 10
    assert search_call.site == "example.com"
    assert search_call.filetype == "pdf"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_query_citation_numbering(assist_service, mock_search_provider, mock_llm_client):
    """Test that citations are properly numbered"""
    # Set up compose to use first 2 citations
    mock_llm_client.compose.return_value = ComposeOutput(
        answer_text="Test answer [1][2]",
        citations_used=[0, 1],
        suggested_followups=[],
        confidence=0.8,
    )

    result = await assist_service.query(
        query="Test query",
        options={},
    )

    # Verify citation IDs are sequential
    assert result.citations[0].id == "1"
    assert result.citations[1].id == "2"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_query_timing_budget(assist_service):
    """Test that timing information is tracked"""
    result = await assist_service.query(
        query="Test query",
        options={},
    )

    # Verify timing information exists
    assert result.timings.intent_ms >= 0
    assert result.timings.search_ms >= 0
    assert result.timings.compose_ms >= 0
    assert result.timings.total_ms > 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_feedback_new_session(assist_service):
    """Test feedback submission creates session if needed"""
    feedback_result = await assist_service.feedback(
        session_id=str(uuid4()),
        turn=1,
        rating=5,
        comment="Great response",
    )

    assert feedback_result.success is True
    assert feedback_result.session_id is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_feedback_existing_session(assist_service):
    """Test feedback for existing session"""
    # Create a session first
    query_result = await assist_service.query(
        query="Test query",
        options={},
    )
    session_id = query_result.session.session_id

    # Submit feedback
    feedback_result = await assist_service.feedback(
        session_id=session_id,
        turn=1,
        rating=4,
        comment="Good",
    )

    assert feedback_result.success is True
    assert feedback_result.session_id == session_id


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_or_create_session_new(assist_service):
    """Test creating a new session"""
    session = assist_service._get_or_create_session(None)

    assert session.session_id is not None
    assert session.turn == 0
    assert session.created_at is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_or_create_session_existing(assist_service):
    """Test retrieving existing session"""
    # Create session first
    result = await assist_service.query(
        query="Test query",
        options={},
    )
    session_id = result.session.session_id

    # Retrieve same session
    session = assist_service._get_or_create_session(session_id)

    assert session.session_id == session_id
    assert session.turn == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_failure_raises_error(assist_service, mock_search_provider):
    """Test that search failure raises an error (no fallback for search)"""
    # Make search fail
    mock_search_provider.search.side_effect = Exception("Search service down")

    with pytest.raises(Exception):
        await assist_service.query(
            query="Test query",
            options={},
        )
