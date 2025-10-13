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
Health check endpoints with liveness and readiness probes.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Response, status

from ..core.config import settings
from ..core.health import check_all_dependencies, determine_overall_status
from ..schemas.common import DetailedHealthResponse, HealthResponse

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Basic health check",
    description="Simple health check endpoint that returns OK if the service is running. "
    "No authentication required.",
)
async def health_check() -> HealthResponse:
    """
    Basic health check endpoint (no authentication required).

    Returns:
        HealthResponse: Status OK if service is running
    """
    return HealthResponse(status="ok")


@router.get(
    "/health/live",
    response_model=HealthResponse,
    summary="Liveness probe",
    description="Liveness probe for Kubernetes. Returns OK if the application process is alive. "
    "Does not check dependencies. No authentication required.",
)
async def liveness_check() -> HealthResponse:
    """
    Liveness probe endpoint for Kubernetes.

    This endpoint checks if the application process is alive and responsive.
    It does not check dependency health, only that the process can handle requests.

    Use this for Kubernetes liveness probe to determine if the pod should be restarted.

    Returns:
        HealthResponse: Status OK if process is alive
    """
    return HealthResponse(status="ok")


@router.get(
    "/health/ready",
    summary="Readiness probe",
    description="Readiness probe for Kubernetes. Returns 200 if the service is ready to accept traffic, "
    "503 if dependencies are unhealthy. Checks Fess and Ollama health. No authentication required.",
)
async def readiness_check(response: Response) -> HealthResponse:
    """
    Readiness probe endpoint for Kubernetes.

    This endpoint checks if the application is ready to accept traffic by verifying
    that all critical dependencies (Fess, Ollama) are healthy.

    Use this for Kubernetes readiness probe to determine if the pod should receive traffic.

    Returns:
        HealthResponse: Status OK if ready, with HTTP 503 if not ready
    """
    # Check all dependencies
    dependencies = await check_all_dependencies(
        fess_url=settings.fess_base_url,
        ollama_url=settings.ollama_base_url,
    )

    # Determine overall status
    overall_status = determine_overall_status(dependencies)

    if overall_status == "unhealthy":
        # Return 503 Service Unavailable if not ready
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(status="not_ready")

    return HealthResponse(status="ready")


@router.get(
    "/health/detailed",
    response_model=DetailedHealthResponse,
    summary="Detailed health check",
    description="Detailed health check with dependency status. Returns health information for "
    "Fess and Ollama services including response times. No authentication required.",
)
async def detailed_health_check(response: Response) -> DetailedHealthResponse:
    """
    Detailed health check endpoint with dependency information.

    This endpoint provides comprehensive health information including:
    - Overall system status
    - Health status of each dependency (Fess, Ollama)
    - Response times for each dependency
    - Error messages for unhealthy services

    No authentication required for monitoring purposes.

    Returns:
        DetailedHealthResponse: Detailed health status with dependencies
    """
    # Check all dependencies
    dependencies = await check_all_dependencies(
        fess_url=settings.fess_base_url,
        ollama_url=settings.ollama_base_url,
    )

    # Determine overall status
    overall_status = determine_overall_status(dependencies)

    # Set HTTP status code based on overall health
    if overall_status == "unhealthy":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif overall_status == "degraded":
        response.status_code = status.HTTP_200_OK  # Still accepting requests

    return DetailedHealthResponse(
        status=overall_status,
        timestamp=datetime.now(UTC).isoformat(),
        version=settings.api_version,
        dependencies=dependencies,
    )
