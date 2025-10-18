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
Unit tests for security features (authentication, middleware).
"""

import pytest
from fastapi import HTTPException, status
from unittest.mock import MagicMock

from app.core.security.auth import verify_api_token
from app.core.config import Settings


@pytest.mark.unit
class TestAuthenticationToken:
    """Test cases for API token authentication."""

    @pytest.mark.asyncio
    async def test_valid_token(self, test_settings: Settings):
        """Test authentication with valid token."""
        token = test_settings.intaste_api_token
        result = await verify_api_token(x_intaste_token=token)
        assert result == token

    @pytest.mark.asyncio
    async def test_missing_token(self):
        """Test authentication with missing token."""
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_token(x_intaste_token=None)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "UNAUTHORIZED" in str(exc_info.value.detail)
        assert "Invalid or missing API token" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_invalid_token(self):
        """Test authentication with invalid token."""
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_token(x_intaste_token="invalid-token")

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "UNAUTHORIZED" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_empty_token(self):
        """Test authentication with empty token."""
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_token(x_intaste_token="")

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_token_with_whitespace(self):
        """Test authentication with token containing whitespace."""
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_token(x_intaste_token="  invalid-token  ")

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_very_long_token(self):
        """Test authentication with very long invalid token."""
        long_token = "a" * 10000
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_token(x_intaste_token=long_token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_token_with_special_characters(self):
        """Test authentication with token containing special characters."""
        special_tokens = [
            "token-with-special-!@#$%",
            "token\nwith\nnewlines",
            "token\twith\ttabs",
            "token with spaces",
            "token<script>alert('xss')</script>",
        ]

        for token in special_tokens:
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_token(x_intaste_token=token)

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_case_sensitive_token(self, test_settings: Settings):
        """Test that token comparison is case-sensitive."""
        token = test_settings.intaste_api_token.upper()
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_token(x_intaste_token=token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.unit
class TestRequestIDMiddleware:
    """Test cases for RequestIDMiddleware."""

    def test_middleware_imports(self):
        """Test that middleware can be imported."""
        from app.core.security.middleware import RequestIDMiddleware, add_request_id_middleware

        assert RequestIDMiddleware is not None
        assert add_request_id_middleware is not None

    def test_middleware_generates_request_id(self):
        """Test that middleware generates request ID."""
        from app.core.security.middleware import RequestIDMiddleware
        from starlette.requests import Request
        from starlette.responses import Response
        import asyncio

        # Create mock request and call_next
        async def mock_call_next(request):
            return Response(content="test", status_code=200)

        async def test_middleware():
            middleware = RequestIDMiddleware(app=MagicMock())
            request = Request(scope={"type": "http", "method": "GET", "path": "/test", "headers": []})

            response = await middleware.dispatch(request, mock_call_next)

            # Verify request has request_id
            assert hasattr(request.state, "request_id")
            assert request.state.request_id is not None
            assert len(request.state.request_id) > 0

            # Verify response has X-Request-ID header
            assert "x-request-id" in response.headers
            assert response.headers["x-request-id"] == request.state.request_id

        asyncio.run(test_middleware())


@pytest.mark.unit
class TestCORSConfiguration:
    """Test cases for CORS configuration."""

    def test_cors_setup_imports(self):
        """Test that CORS setup function can be imported."""
        from app.core.security.middleware import setup_cors

        assert setup_cors is not None

    def test_cors_setup_with_app(self):
        """Test CORS setup with FastAPI app."""
        from fastapi import FastAPI
        from app.core.security.middleware import setup_cors
        from app.core.config import settings

        app = FastAPI()
        setup_cors(app)

        # Verify middleware is added (check user_middleware)
        assert len(app.user_middleware) > 0

        # Find CORSMiddleware
        cors_middleware = None
        for middleware in app.user_middleware:
            if "CORSMiddleware" in str(middleware.cls):
                cors_middleware = middleware
                break

        assert cors_middleware is not None, "CORSMiddleware should be added"
