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
Unit tests for AssistService.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.services.assist import AssistService
from app.core.search_agent.base import SearchAgent
from app.core.llm.base import LLMClient


@pytest.mark.unit
class TestAssistServiceInitialization:
    """Test cases for AssistService initialization."""

    def test_init_with_dependencies(
        self, mock_search_agent: AsyncMock, mock_llm_client: AsyncMock
    ):
        """Test AssistService initialization with dependencies."""
        service = AssistService(
            search_agent=mock_search_agent,
            llm_client=mock_llm_client,
        )

        assert service.search_agent == mock_search_agent
        assert service.llm_client == mock_llm_client
        assert isinstance(service.sessions, dict)
        assert len(service.sessions) == 0

    def test_init_creates_empty_sessions(
        self, mock_search_agent: AsyncMock, mock_llm_client: AsyncMock
    ):
        """Test that sessions dict is initialized as empty."""
        service = AssistService(
            search_agent=mock_search_agent,
            llm_client=mock_llm_client,
        )

        assert service.sessions == {}


@pytest.mark.unit
class TestAssistServiceWarmup:
    """Test cases for AssistService warmup functionality."""

    @pytest.mark.asyncio
    async def test_warmup_success(
        self, mock_search_agent: AsyncMock, mock_llm_client: AsyncMock
    ):
        """Test successful warmup."""
        mock_llm_client.warmup = AsyncMock(return_value=True)

        service = AssistService(
            search_agent=mock_search_agent,
            llm_client=mock_llm_client,
        )

        result = await service.warmup()

        assert result is True
        mock_llm_client.warmup.assert_called_once_with(timeout_ms=30000)

    @pytest.mark.asyncio
    async def test_warmup_failure(
        self, mock_search_agent: AsyncMock, mock_llm_client: AsyncMock
    ):
        """Test warmup failure."""
        mock_llm_client.warmup = AsyncMock(return_value=False)

        service = AssistService(
            search_agent=mock_search_agent,
            llm_client=mock_llm_client,
        )

        result = await service.warmup()

        assert result is False
        mock_llm_client.warmup.assert_called_once()

    @pytest.mark.asyncio
    async def test_warmup_with_custom_timeout(
        self, mock_search_agent: AsyncMock, mock_llm_client: AsyncMock
    ):
        """Test warmup with custom timeout."""
        mock_llm_client.warmup = AsyncMock(return_value=True)

        service = AssistService(
            search_agent=mock_search_agent,
            llm_client=mock_llm_client,
        )

        result = await service.warmup(timeout_ms=60000)

        assert result is True
        mock_llm_client.warmup.assert_called_once_with(timeout_ms=60000)

    @pytest.mark.asyncio
    async def test_warmup_exception_handling(
        self, mock_search_agent: AsyncMock, mock_llm_client: AsyncMock
    ):
        """Test warmup handles exceptions gracefully."""
        mock_llm_client.warmup = AsyncMock(side_effect=Exception("Warmup failed"))

        service = AssistService(
            search_agent=mock_search_agent,
            llm_client=mock_llm_client,
        )

        result = await service.warmup()

        assert result is False
        mock_llm_client.warmup.assert_called_once()


@pytest.mark.unit
class TestAssistServiceSessionManagement:
    """Test cases for AssistService session management."""

    def test_sessions_storage_isolation(
        self, mock_search_agent: AsyncMock, mock_llm_client: AsyncMock
    ):
        """Test that each service instance has isolated session storage."""
        service1 = AssistService(
            search_agent=mock_search_agent,
            llm_client=mock_llm_client,
        )
        service2 = AssistService(
            search_agent=mock_search_agent,
            llm_client=mock_llm_client,
        )

        # Modify service1 sessions
        session_id = str(uuid4())
        service1.sessions[session_id] = {"turn": 1}

        # Verify service2 is unaffected
        assert session_id not in service2.sessions
        assert len(service2.sessions) == 0

    def test_sessions_can_store_arbitrary_data(
        self, mock_search_agent: AsyncMock, mock_llm_client: AsyncMock
    ):
        """Test that sessions can store arbitrary data."""
        service = AssistService(
            search_agent=mock_search_agent,
            llm_client=mock_llm_client,
        )

        session_id = str(uuid4())
        service.sessions[session_id] = {
            "turn": 1,
            "queries": ["query1", "query2"],
            "metadata": {"user_id": "test-user", "started_at": "2025-01-01T00:00:00Z"},
        }

        assert service.sessions[session_id]["turn"] == 1
        assert len(service.sessions[session_id]["queries"]) == 2
        assert service.sessions[session_id]["metadata"]["user_id"] == "test-user"

    def test_multiple_sessions_management(
        self, mock_search_agent: AsyncMock, mock_llm_client: AsyncMock
    ):
        """Test managing multiple sessions simultaneously."""
        service = AssistService(
            search_agent=mock_search_agent,
            llm_client=mock_llm_client,
        )

        # Create multiple sessions
        session_ids = [str(uuid4()) for _ in range(5)]
        for idx, session_id in enumerate(session_ids):
            service.sessions[session_id] = {"turn": idx + 1}

        # Verify all sessions exist
        assert len(service.sessions) == 5
        for idx, session_id in enumerate(session_ids):
            assert service.sessions[session_id]["turn"] == idx + 1

    def test_session_update(
        self, mock_search_agent: AsyncMock, mock_llm_client: AsyncMock
    ):
        """Test updating existing session."""
        service = AssistService(
            search_agent=mock_search_agent,
            llm_client=mock_llm_client,
        )

        session_id = str(uuid4())
        service.sessions[session_id] = {"turn": 1, "queries": ["query1"]}

        # Update session
        service.sessions[session_id]["turn"] = 2
        service.sessions[session_id]["queries"].append("query2")

        assert service.sessions[session_id]["turn"] == 2
        assert len(service.sessions[session_id]["queries"]) == 2

    def test_session_deletion(
        self, mock_search_agent: AsyncMock, mock_llm_client: AsyncMock
    ):
        """Test deleting a session."""
        service = AssistService(
            search_agent=mock_search_agent,
            llm_client=mock_llm_client,
        )

        session_id = str(uuid4())
        service.sessions[session_id] = {"turn": 1}

        # Verify session exists
        assert session_id in service.sessions

        # Delete session
        del service.sessions[session_id]

        # Verify session is deleted
        assert session_id not in service.sessions

    def test_session_retrieval_nonexistent(
        self, mock_search_agent: AsyncMock, mock_llm_client: AsyncMock
    ):
        """Test retrieving non-existent session."""
        service = AssistService(
            search_agent=mock_search_agent,
            llm_client=mock_llm_client,
        )

        session_id = str(uuid4())

        # Should not raise error, just return None
        result = service.sessions.get(session_id)
        assert result is None

    def test_session_id_uniqueness(
        self, mock_search_agent: AsyncMock, mock_llm_client: AsyncMock
    ):
        """Test that session IDs are unique."""
        service = AssistService(
            search_agent=mock_search_agent,
            llm_client=mock_llm_client,
        )

        # Generate multiple session IDs
        session_ids = [str(uuid4()) for _ in range(100)]

        # Verify all are unique
        assert len(session_ids) == len(set(session_ids))

        # Store all sessions
        for session_id in session_ids:
            service.sessions[session_id] = {"turn": 1}

        # Verify all are stored
        assert len(service.sessions) == 100


@pytest.mark.unit
class TestAssistServiceConcurrency:
    """Test cases for concurrent session access."""

    @pytest.mark.asyncio
    async def test_concurrent_warmup_calls(
        self, mock_search_agent: AsyncMock, mock_llm_client: AsyncMock
    ):
        """Test multiple concurrent warmup calls."""
        import asyncio

        mock_llm_client.warmup = AsyncMock(return_value=True)

        service = AssistService(
            search_agent=mock_search_agent,
            llm_client=mock_llm_client,
        )

        # Call warmup concurrently
        tasks = [service.warmup() for _ in range(5)]
        results = await asyncio.gather(*tasks)

        # All should succeed
        assert all(result is True for result in results)

        # Warmup should be called 5 times
        assert mock_llm_client.warmup.call_count == 5

    def test_concurrent_session_modifications(
        self, mock_search_agent: AsyncMock, mock_llm_client: AsyncMock
    ):
        """Test concurrent modifications to different sessions (thread-safe at dict level)."""
        service = AssistService(
            search_agent=mock_search_agent,
            llm_client=mock_llm_client,
        )

        # Create multiple sessions concurrently (simulated)
        session_ids = [str(uuid4()) for _ in range(10)]
        for session_id in session_ids:
            service.sessions[session_id] = {"turn": 1}

        # Verify all sessions are created
        assert len(service.sessions) == 10
        for session_id in session_ids:
            assert session_id in service.sessions


@pytest.mark.unit
class TestAssistServiceIntegration:
    """Test cases for AssistService integration with dependencies."""

    def test_service_has_search_agent_access(
        self, mock_search_agent: AsyncMock, mock_llm_client: AsyncMock
    ):
        """Test that service can access search agent."""
        service = AssistService(
            search_agent=mock_search_agent,
            llm_client=mock_llm_client,
        )

        assert service.search_agent is not None
        assert isinstance(service.search_agent, (AsyncMock, SearchAgent))

    def test_service_has_llm_client_access(
        self, mock_search_agent: AsyncMock, mock_llm_client: AsyncMock
    ):
        """Test that service can access LLM client."""
        service = AssistService(
            search_agent=mock_search_agent,
            llm_client=mock_llm_client,
        )

        assert service.llm_client is not None
        assert isinstance(service.llm_client, (AsyncMock, LLMClient))
