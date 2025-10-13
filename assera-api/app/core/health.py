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
Health check utilities for dependency services.
"""

import asyncio
import logging
import time

import httpx

from ..schemas.common import DependencyHealth

logger = logging.getLogger(__name__)


async def check_fess_health(base_url: str, timeout_ms: int = 5000) -> DependencyHealth:
    """
    Check Fess search service health.

    Args:
        base_url: Fess base URL
        timeout_ms: Timeout in milliseconds

    Returns:
        DependencyHealth: Health status of Fess
    """
    start_time = time.time()

    try:
        async with httpx.AsyncClient(timeout=timeout_ms / 1000) as client:
            # Use Fess OpenAPI v1 health endpoint
            response = await client.get(f"{base_url}/api/v1/health")

            response_time_ms = int((time.time() - start_time) * 1000)

            if response.status_code == 200:
                # Parse health response: {"data": {"status": "green", "timed_out": false}}
                data = response.json()
                health_data = data.get("data", {})
                status = health_data.get("status", "unknown")
                timed_out = health_data.get("timed_out", False)

                if status == "green" and not timed_out:
                    return DependencyHealth(
                        status="healthy",
                        response_time_ms=response_time_ms,
                    )
                else:
                    return DependencyHealth(
                        status="degraded",
                        response_time_ms=response_time_ms,
                        error=f"Fess status: {status}, timed_out: {timed_out}",
                    )
            else:
                return DependencyHealth(
                    status="degraded",
                    response_time_ms=response_time_ms,
                    error=f"HTTP {response.status_code}",
                )

    except httpx.TimeoutException:
        response_time_ms = int((time.time() - start_time) * 1000)
        return DependencyHealth(
            status="unhealthy",
            response_time_ms=response_time_ms,
            error="Request timeout",
        )
    except Exception as e:
        response_time_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Fess health check failed: {e}")
        return DependencyHealth(
            status="unhealthy",
            response_time_ms=response_time_ms,
            error=str(e),
        )


async def check_ollama_health(base_url: str, timeout_ms: int = 5000) -> DependencyHealth:
    """
    Check Ollama LLM service health.

    Args:
        base_url: Ollama base URL
        timeout_ms: Timeout in milliseconds

    Returns:
        DependencyHealth: Health status of Ollama
    """
    start_time = time.time()

    try:
        async with httpx.AsyncClient(timeout=timeout_ms / 1000) as client:
            # Use Ollama's API endpoint to list models (lightweight operation)
            response = await client.get(f"{base_url}/api/tags")

            response_time_ms = int((time.time() - start_time) * 1000)

            if response.status_code == 200:
                data = response.json()
                # Check if models are available
                if "models" in data and len(data["models"]) > 0:
                    return DependencyHealth(
                        status="healthy",
                        response_time_ms=response_time_ms,
                    )
                else:
                    return DependencyHealth(
                        status="degraded",
                        response_time_ms=response_time_ms,
                        error="No models available",
                    )
            else:
                return DependencyHealth(
                    status="degraded",
                    response_time_ms=response_time_ms,
                    error=f"HTTP {response.status_code}",
                )

    except httpx.TimeoutException:
        response_time_ms = int((time.time() - start_time) * 1000)
        return DependencyHealth(
            status="unhealthy",
            response_time_ms=response_time_ms,
            error="Request timeout",
        )
    except Exception as e:
        response_time_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Ollama health check failed: {e}")
        return DependencyHealth(
            status="unhealthy",
            response_time_ms=response_time_ms,
            error=str(e),
        )


async def check_all_dependencies(fess_url: str, ollama_url: str) -> dict[str, DependencyHealth]:
    """
    Check health of all dependency services in parallel.

    Args:
        fess_url: Fess base URL
        ollama_url: Ollama base URL

    Returns:
        dict: Health status of each dependency
    """
    # Run health checks in parallel
    fess_task = check_fess_health(fess_url)
    ollama_task = check_ollama_health(ollama_url)

    results: tuple[DependencyHealth | BaseException, DependencyHealth | BaseException] = (
        await asyncio.gather(fess_task, ollama_task, return_exceptions=True)
    )
    fess_health_result, ollama_health_result = results

    # Handle exceptions from gather with type narrowing
    if isinstance(fess_health_result, Exception):
        logger.error(f"Fess health check exception: {fess_health_result}")
        fess_health = DependencyHealth(
            status="unhealthy",
            error=str(fess_health_result),
        )
    elif isinstance(fess_health_result, DependencyHealth):
        fess_health = fess_health_result
    else:
        # Should never happen, but satisfy mypy
        fess_health = DependencyHealth(status="unhealthy", error="Unknown error")

    if isinstance(ollama_health_result, Exception):
        logger.error(f"Ollama health check exception: {ollama_health_result}")
        ollama_health = DependencyHealth(
            status="unhealthy",
            error=str(ollama_health_result),
        )
    elif isinstance(ollama_health_result, DependencyHealth):
        ollama_health = ollama_health_result
    else:
        # Should never happen, but satisfy mypy
        ollama_health = DependencyHealth(status="unhealthy", error="Unknown error")

    return {
        "fess": fess_health,
        "ollama": ollama_health,
    }


def determine_overall_status(dependencies: dict[str, DependencyHealth]) -> str:
    """
    Determine overall system status based on dependencies.

    Args:
        dependencies: Health status of each dependency

    Returns:
        str: Overall status (healthy, degraded, unhealthy)
    """
    statuses = [dep.status for dep in dependencies.values()]

    if all(status == "healthy" for status in statuses):
        return "healthy"
    elif any(status == "unhealthy" for status in statuses):
        return "unhealthy"
    else:
        return "degraded"
