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
    assert "Intaste" in data["name"]
    assert "version" in data


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
