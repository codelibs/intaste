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
Middleware for request tracking, CORS, and security headers.
"""

import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from ..config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        # Content-Security-Policy for API responses
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; frame-ancestors 'none'"
        )

        # Cache control for API responses
        if "Cache-Control" not in response.headers:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"

        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Add X-Request-ID to all requests and responses for tracing.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        # Track timing
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Add headers to response
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"

        return response


def add_security_headers_middleware(app: FastAPI) -> None:
    """
    Add security headers middleware to the app.
    """
    app.add_middleware(SecurityHeadersMiddleware)


def add_request_id_middleware(app: FastAPI) -> None:
    """
    Add request ID tracking middleware to the app.
    """
    app.add_middleware(RequestIDMiddleware)


def setup_cors(app: FastAPI) -> None:
    """
    Configure CORS for the API.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,  # No cookies
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Intaste-Token", "X-Request-ID"],
        expose_headers=["X-Request-ID", "X-Process-Time", "X-RateLimit-*"],
    )
