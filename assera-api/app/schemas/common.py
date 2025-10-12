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
Common schemas used across the API.
"""

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"


class DependencyHealth(BaseModel):
    """Health status of a dependency service."""

    status: str = Field(..., description="Health status: healthy, degraded, unhealthy")
    response_time_ms: int | None = Field(None, description="Response time in milliseconds")
    error: str | None = Field(None, description="Error message if unhealthy")


class DetailedHealthResponse(BaseModel):
    """Detailed health check response with dependencies."""

    status: str = Field(..., description="Overall status: healthy, degraded, unhealthy")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    version: str = Field(..., description="Application version")
    dependencies: dict[str, DependencyHealth] = Field(
        ..., description="Health status of each dependency"
    )


class ErrorResponse(BaseModel):
    """
    Common error response format.
    """

    code: str
    message: str
    details: dict[str, Any] | None = None
    request_id: str | None = None
