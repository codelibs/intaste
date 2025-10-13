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

"""Integration tests for API endpoints"""

import pytest
from unittest.mock import patch


@pytest.mark.integration
def test_health_endpoint_no_auth(client):
    """Test health endpoint without authentication"""
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.integration
def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "Assera" in data["name"]
    assert "version" in data


@pytest.mark.integration
def test_assist_query_no_auth(client, sample_query_request, assist_service):
    """Test assist query without authentication returns 401"""
    with patch("app.main.assist_service", assist_service):
        response = client.post(
            "/api/v1/assist/query",
            json=sample_query_request,
        )

        assert response.status_code == 401


@pytest.mark.integration
def test_assist_query_invalid_token(client, sample_query_request):
    """Test assist query with invalid token returns 401"""
    response = client.post(
        "/api/v1/assist/query",
        json=sample_query_request,
        headers={"X-Assera-Token": "invalid-token"},
    )

    assert response.status_code == 401


@pytest.mark.integration
def test_assist_query_success(client, auth_headers, sample_query_request, mock_search_provider, mock_llm_client, assist_service):
    """Test successful assist query"""
    with patch("app.main.assist_service", assist_service):
        response = client.post(
            "/api/v1/assist/query",
            json=sample_query_request,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "answer" in data
        assert "citations" in data
        assert "session" in data
        assert "timings" in data

        # Verify answer structure
        assert "text" in data["answer"]
        assert "suggested_questions" in data["answer"]

        # Verify citations
        assert len(data["citations"]) > 0
        assert "id" in data["citations"][0]
        assert "title" in data["citations"][0]
        assert "url" in data["citations"][0]

        # Verify session
        assert "id" in data["session"]
        assert "turn" in data["session"]
        assert data["session"]["turn"] == 1


@pytest.mark.integration
def test_assist_query_with_session(client, auth_headers, assist_service):
    """Test assist query with session continuation"""
    with patch("app.main.assist_service", assist_service):
        # First query
        response1 = client.post(
            "/api/v1/assist/query",
            json={"query": "First query"},
            headers=auth_headers,
        )
        assert response1.status_code == 200
        session_id = response1.json()["session"]["id"]

        # Second query with session
        response2 = client.post(
            "/api/v1/assist/query",
            json={"query": "Second query", "session_id": session_id},
            headers=auth_headers,
        )
        assert response2.status_code == 200
        data = response2.json()

        assert data["session"]["id"] == session_id
        assert data["session"]["turn"] == 2


@pytest.mark.integration
def test_assist_query_validation_error(client, auth_headers, assist_service):
    """Test assist query with validation error"""
    with patch("app.main.assist_service", assist_service):
        response = client.post(
            "/api/v1/assist/query",
            json={"invalid": "field"},  # Missing required 'query' field
            headers=auth_headers,
        )

        assert response.status_code == 422


@pytest.mark.integration
def test_assist_feedback_success(client, auth_headers, sample_feedback_request):
    """Test successful feedback submission"""
    response = client.post(
        "/api/v1/assist/feedback",
        json=sample_feedback_request,
        headers=auth_headers,
    )

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "accepted"


@pytest.mark.integration
def test_assist_feedback_no_auth(client, sample_feedback_request):
    """Test feedback without authentication returns 401"""
    response = client.post(
        "/api/v1/assist/feedback",
        json=sample_feedback_request,
    )

    assert response.status_code == 401


@pytest.mark.integration
def test_models_list(client, auth_headers, mock_llm_client):
    """Test listing available models"""
    with patch("app.main.llm_client", mock_llm_client):
        response = client.get(
            "/api/v1/models",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "default" in data
        assert "available" in data
        assert isinstance(data["available"], list)


@pytest.mark.integration
def test_models_select_global(client, auth_headers):
    """Test selecting model globally"""
    response = client.post(
        "/api/v1/models/select",
        json={"model": "test-model", "scope": "default"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["model"] == "test-model"
    assert data["effective_scope"] == "default"


@pytest.mark.integration
def test_models_select_session(client, auth_headers):
    """Test selecting model for session"""
    response = client.post(
        "/api/v1/models/select",
        json={
            "model": "test-model",
            "scope": "session",
            "session_id": "test-session-id",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["model"] == "test-model"
    assert data["effective_scope"] == "session"


@pytest.mark.integration
def test_cors_headers(client):
    """Test CORS headers are present"""
    response = client.options(
        "/api/v1/health",
        headers={"Origin": "http://localhost:3000"},
    )

    # CORS headers should be present
    assert "access-control-allow-origin" in response.headers


@pytest.mark.integration
def test_request_id_header(client, auth_headers, sample_query_request, assist_service):
    """Test X-Request-ID header is returned"""
    with patch("app.main.assist_service", assist_service):
        response = client.post(
            "/api/v1/assist/query",
            json=sample_query_request,
            headers={**auth_headers, "X-Request-ID": "test-request-123"},
        )

        assert response.status_code == 200
        assert "x-request-id" in response.headers
        assert response.headers["x-request-id"] == "test-request-123"
