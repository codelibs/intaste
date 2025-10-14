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
Unit tests for health check utilities.
"""

import pytest
from pytest_httpx import HTTPXMock

from app.core.health import (
    check_all_dependencies,
    check_fess_health,
    check_ollama_health,
    determine_overall_status,
)
from app.schemas.common import DependencyHealth


@pytest.mark.unit
@pytest.mark.asyncio
async def test_check_fess_health_success(httpx_mock: HTTPXMock):
    """Test successful Fess health check."""
    httpx_mock.add_response(
        url="http://fess:8080/api/v1/health",
        status_code=200,
        json={"data": {"status": "green", "timed_out": False}},
    )

    health = await check_fess_health("http://fess:8080")

    assert health.status == "healthy"
    assert health.response_time_ms is not None
    assert health.response_time_ms >= 0
    assert health.error is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_check_fess_health_degraded(httpx_mock: HTTPXMock):
    """Test Fess health check with non-200 response."""
    httpx_mock.add_response(
        url="http://fess:8080/api/v1/health",
        status_code=503,
    )

    health = await check_fess_health("http://fess:8080")

    assert health.status == "degraded"
    assert health.response_time_ms is not None
    assert health.error == "HTTP 503"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_check_fess_health_timeout(httpx_mock: HTTPXMock):
    """Test Fess health check with timeout."""
    import httpx

    httpx_mock.add_exception(
        httpx.TimeoutException("Request timeout"),
        url="http://fess:8080/api/v1/health",
    )

    health = await check_fess_health("http://fess:8080", timeout_ms=100)

    assert health.status == "unhealthy"
    assert health.response_time_ms is not None
    assert "timeout" in health.error.lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_check_ollama_health_success(httpx_mock: HTTPXMock):
    """Test successful Ollama health check."""
    httpx_mock.add_response(
        url="http://ollama:11434/api/tags",
        status_code=200,
        json={"models": [{"name": "llama3", "size": 4661224728}]},
    )

    health = await check_ollama_health("http://ollama:11434")

    assert health.status == "healthy"
    assert health.response_time_ms is not None
    assert health.response_time_ms >= 0
    assert health.error is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_check_ollama_health_no_models(httpx_mock: HTTPXMock):
    """Test Ollama health check with no models available."""
    httpx_mock.add_response(
        url="http://ollama:11434/api/tags",
        status_code=200,
        json={"models": []},
    )

    health = await check_ollama_health("http://ollama:11434")

    assert health.status == "degraded"
    assert health.response_time_ms is not None
    assert health.error == "No models available"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_check_ollama_health_degraded(httpx_mock: HTTPXMock):
    """Test Ollama health check with non-200 response."""
    httpx_mock.add_response(
        url="http://ollama:11434/api/tags",
        status_code=500,
    )

    health = await check_ollama_health("http://ollama:11434")

    assert health.status == "degraded"
    assert health.response_time_ms is not None
    assert health.error == "HTTP 500"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_check_ollama_health_timeout(httpx_mock: HTTPXMock):
    """Test Ollama health check with timeout."""
    import httpx

    httpx_mock.add_exception(
        httpx.TimeoutException("Request timeout"),
        url="http://ollama:11434/api/tags",
    )

    health = await check_ollama_health("http://ollama:11434", timeout_ms=100)

    assert health.status == "unhealthy"
    assert health.response_time_ms is not None
    assert "timeout" in health.error.lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_check_all_dependencies_healthy(httpx_mock: HTTPXMock):
    """Test checking all dependencies when all are healthy."""
    httpx_mock.add_response(
        url="http://fess:8080/api/v1/health",
        status_code=200,
        json={"data": {"status": "green", "timed_out": False}},
    )
    httpx_mock.add_response(
        url="http://ollama:11434/api/tags",
        status_code=200,
        json={"models": [{"name": "llama3"}]},
    )

    dependencies = await check_all_dependencies(
        fess_url="http://fess:8080",
        ollama_url="http://ollama:11434",
    )

    assert "fess" in dependencies
    assert "ollama" in dependencies
    assert dependencies["fess"].status == "healthy"
    assert dependencies["ollama"].status == "healthy"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_check_all_dependencies_with_failures(httpx_mock: HTTPXMock):
    """Test checking all dependencies with some failures."""
    httpx_mock.add_response(
        url="http://fess:8080/api/v1/health",
        status_code=503,
    )
    httpx_mock.add_response(
        url="http://ollama:11434/api/tags",
        status_code=200,
        json={"models": [{"name": "llama3"}]},
    )

    dependencies = await check_all_dependencies(
        fess_url="http://fess:8080",
        ollama_url="http://ollama:11434",
    )

    assert dependencies["fess"].status == "degraded"
    assert dependencies["ollama"].status == "healthy"


@pytest.mark.unit
def test_determine_overall_status_all_healthy():
    """Test overall status when all dependencies are healthy."""
    dependencies = {
        "fess": DependencyHealth(status="healthy"),
        "ollama": DependencyHealth(status="healthy"),
    }

    status = determine_overall_status(dependencies)
    assert status == "healthy"


@pytest.mark.unit
def test_determine_overall_status_one_degraded():
    """Test overall status when one dependency is degraded."""
    dependencies = {
        "fess": DependencyHealth(status="healthy"),
        "ollama": DependencyHealth(status="degraded", error="No models"),
    }

    status = determine_overall_status(dependencies)
    assert status == "degraded"


@pytest.mark.unit
def test_determine_overall_status_one_unhealthy():
    """Test overall status when one dependency is unhealthy."""
    dependencies = {
        "fess": DependencyHealth(status="unhealthy", error="Connection refused"),
        "ollama": DependencyHealth(status="healthy"),
    }

    status = determine_overall_status(dependencies)
    assert status == "unhealthy"


@pytest.mark.unit
def test_determine_overall_status_all_unhealthy():
    """Test overall status when all dependencies are unhealthy."""
    dependencies = {
        "fess": DependencyHealth(status="unhealthy", error="Connection refused"),
        "ollama": DependencyHealth(status="unhealthy", error="Timeout"),
    }

    status = determine_overall_status(dependencies)
    assert status == "unhealthy"
