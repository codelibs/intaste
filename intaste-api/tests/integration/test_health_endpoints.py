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
Integration tests for health check endpoints.
"""

import pytest
from httpx import AsyncClient
from pytest_httpx import HTTPXMock


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_check_basic(async_client: AsyncClient):
    """Test basic health check endpoint."""
    response = await async_client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_liveness_probe(async_client: AsyncClient):
    """Test liveness probe endpoint."""
    response = await async_client.get("/api/v1/health/live")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_readiness_probe_healthy(
    async_client: AsyncClient,
    httpx_mock: HTTPXMock,
):
    """Test readiness probe when all dependencies are healthy."""
    # Mock Fess health check
    httpx_mock.add_response(
        url="http://fess:8080/api/v1/health",
        status_code=200,
        json={"data": {"status": "green", "timed_out": False}},
    )

    # Mock Ollama health check
    httpx_mock.add_response(
        url="http://ollama:11434/api/tags",
        status_code=200,
        json={"models": [{"name": "llama3"}]},
    )

    response = await async_client.get("/api/v1/health/ready")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_readiness_probe_not_ready(
    async_client: AsyncClient,
    httpx_mock: HTTPXMock,
):
    """Test readiness probe when dependencies are unhealthy."""
    import httpx

    # Mock Fess health check failure
    httpx_mock.add_exception(
        httpx.ConnectError("Connection refused"),
        url="http://fess:8080/api/v1/health",
    )

    # Mock Ollama health check failure
    httpx_mock.add_exception(
        httpx.ConnectError("Connection refused"),
        url="http://ollama:11434/api/tags",
    )

    response = await async_client.get("/api/v1/health/ready")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "not_ready"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_readiness_probe_degraded(
    async_client: AsyncClient,
    httpx_mock: HTTPXMock,
):
    """Test readiness probe when one dependency is degraded."""
    # Mock Fess health check - degraded
    httpx_mock.add_response(
        url="http://fess:8080/api/v1/health",
        status_code=503,
    )

    # Mock Ollama health check - healthy
    httpx_mock.add_response(
        url="http://ollama:11434/api/tags",
        status_code=200,
        json={"models": [{"name": "llama3"}]},
    )

    response = await async_client.get("/api/v1/health/ready")

    # Degraded still allows traffic (200), but not if unhealthy
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_detailed_health_all_healthy(
    async_client: AsyncClient,
    httpx_mock: HTTPXMock,
):
    """Test detailed health check when all dependencies are healthy."""
    # Mock Fess health check
    httpx_mock.add_response(
        url="http://fess:8080/api/v1/health",
        status_code=200,
        json={"data": {"status": "green", "timed_out": False}},
    )

    # Mock Ollama health check
    httpx_mock.add_response(
        url="http://ollama:11434/api/tags",
        status_code=200,
        json={"models": [{"name": "llama3"}]},
    )

    response = await async_client.get("/api/v1/health/detailed")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data
    assert "dependencies" in data

    # Check Fess dependency
    assert "fess" in data["dependencies"]
    assert data["dependencies"]["fess"]["status"] == "healthy"
    assert data["dependencies"]["fess"]["response_time_ms"] is not None

    # Check Ollama dependency
    assert "ollama" in data["dependencies"]
    assert data["dependencies"]["ollama"]["status"] == "healthy"
    assert data["dependencies"]["ollama"]["response_time_ms"] is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_detailed_health_degraded(
    async_client: AsyncClient,
    httpx_mock: HTTPXMock,
):
    """Test detailed health check when one dependency is degraded."""
    # Mock Fess health check - degraded
    httpx_mock.add_response(
        url="http://fess:8080/api/v1/health",
        status_code=503,
    )

    # Mock Ollama health check - healthy
    httpx_mock.add_response(
        url="http://ollama:11434/api/tags",
        status_code=200,
        json={"models": [{"name": "llama3"}]},
    )

    response = await async_client.get("/api/v1/health/detailed")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "degraded"
    assert data["dependencies"]["fess"]["status"] == "degraded"
    assert data["dependencies"]["fess"]["error"] == "HTTP 503"
    assert data["dependencies"]["ollama"]["status"] == "healthy"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_detailed_health_unhealthy(
    async_client: AsyncClient,
    httpx_mock: HTTPXMock,
):
    """Test detailed health check when dependencies are unhealthy."""
    import httpx

    # Mock Fess health check failure
    httpx_mock.add_exception(
        httpx.ConnectError("Connection refused"),
        url="http://fess:8080/api/v1/health",
    )

    # Mock Ollama health check failure
    httpx_mock.add_exception(
        httpx.ConnectError("Connection refused"),
        url="http://ollama:11434/api/tags",
    )

    response = await async_client.get("/api/v1/health/detailed")

    assert response.status_code == 503
    data = response.json()

    assert data["status"] == "unhealthy"
    assert data["dependencies"]["fess"]["status"] == "unhealthy"
    assert data["dependencies"]["fess"]["error"] is not None
    assert data["dependencies"]["ollama"]["status"] == "unhealthy"
    assert data["dependencies"]["ollama"]["error"] is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_endpoints_no_auth_required(async_client: AsyncClient):
    """Test that health endpoints don't require authentication."""
    # Test basic health - no auth needed
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200

    # Test liveness - no auth needed
    response = await async_client.get("/api/v1/health/live")
    assert response.status_code == 200

    # Note: readiness and detailed will fail without mocking dependencies,
    # but they should not return 401 (authentication error)
    # They should return 503 or 200 based on dependency health
