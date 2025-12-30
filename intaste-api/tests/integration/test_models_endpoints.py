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
Integration tests for model management endpoints.
"""

import pytest
from uuid import uuid4


@pytest.mark.integration
class TestModelsListEndpoint:
    """Test cases for GET /api/v1/models endpoint."""

    def test_list_models_success(self, client, auth_headers):
        """Test listing available models."""
        response = client.get("/api/v1/models", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert "default" in data
        assert "available" in data
        assert "selected_per_session" in data
        assert isinstance(data["available"], list)
        assert len(data["available"]) > 0

    def test_list_models_without_auth(self, client):
        """Test listing models without authentication."""
        response = client.get("/api/v1/models")

        assert response.status_code == 401

    def test_list_models_with_invalid_token(self, client):
        """Test listing models with invalid token."""
        response = client.get(
            "/api/v1/models",
            headers={"X-Intaste-Token": "invalid-token"},
        )

        assert response.status_code == 401

    def test_list_models_contains_default(self, client, auth_headers):
        """Test that default model is in available list."""
        response = client.get("/api/v1/models", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Default model should be in available list
        assert data["default"] in data["available"]

    def test_list_models_selected_per_session_is_dict(self, client, auth_headers):
        """Test that selected_per_session is a dictionary."""
        response = client.get("/api/v1/models", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data["selected_per_session"], dict)


@pytest.mark.integration
class TestModelsSelectEndpoint:
    """Test cases for POST /api/v1/models/select endpoint."""

    def test_select_model_global_scope(self, client, auth_headers):
        """Test selecting model with global scope."""
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

    def test_select_model_session_scope(self, client, auth_headers):
        """Test selecting model with session scope."""
        session_id = str(uuid4())

        response = client.post(
            "/api/v1/models/select",
            json={
                "model": "session-model",
                "scope": "session",
                "session_id": session_id,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "ok"
        assert data["model"] == "session-model"
        assert data["effective_scope"] == "session"

    def test_select_model_session_scope_without_session_id(self, client, auth_headers):
        """Test selecting model with session scope but no session_id."""
        response = client.post(
            "/api/v1/models/select",
            json={"model": "test-model", "scope": "session"},
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.json()

        assert "BAD_REQUEST" in str(data["detail"])
        assert "session_id is required" in str(data["detail"])

    def test_select_model_without_auth(self, client):
        """Test selecting model without authentication."""
        response = client.post(
            "/api/v1/models/select",
            json={"model": "test-model", "scope": "default"},
        )

        assert response.status_code == 401

    def test_select_model_with_invalid_scope(self, client, auth_headers):
        """Test selecting model with invalid scope."""
        response = client.post(
            "/api/v1/models/select",
            json={"model": "test-model", "scope": "invalid"},
            headers=auth_headers,
        )

        # Pydantic validation error
        assert response.status_code == 422

    def test_select_model_missing_model_field(self, client, auth_headers):
        """Test selecting model without model field."""
        response = client.post(
            "/api/v1/models/select",
            json={"scope": "default"},
            headers=auth_headers,
        )

        # Pydantic validation error
        assert response.status_code == 422

    def test_select_model_empty_model_name(self, client, auth_headers):
        """Test selecting model with empty model name."""
        response = client.post(
            "/api/v1/models/select",
            json={"model": "", "scope": "default"},
            headers=auth_headers,
        )

        # Pydantic may allow empty string, but request should still process
        # (no validation on model name existence currently)
        assert response.status_code in [200, 422]

    def test_select_model_persistence_in_session(self, client, auth_headers):
        """Test that selected model persists in session."""
        session_id = str(uuid4())

        # Select model for session
        response1 = client.post(
            "/api/v1/models/select",
            json={
                "model": "persistent-model",
                "scope": "session",
                "session_id": session_id,
            },
            headers=auth_headers,
        )

        assert response1.status_code == 200

        # List models and check selected_per_session
        response2 = client.get("/api/v1/models", headers=auth_headers)

        assert response2.status_code == 200
        data = response2.json()

        assert session_id in data["selected_per_session"]
        assert data["selected_per_session"][session_id] == "persistent-model"

    def test_select_model_override_session(self, client, auth_headers):
        """Test overriding model selection for same session."""
        session_id = str(uuid4())

        # First selection
        response1 = client.post(
            "/api/v1/models/select",
            json={
                "model": "model-v1",
                "scope": "session",
                "session_id": session_id,
            },
            headers=auth_headers,
        )

        assert response1.status_code == 200

        # Override with second selection
        response2 = client.post(
            "/api/v1/models/select",
            json={
                "model": "model-v2",
                "scope": "session",
                "session_id": session_id,
            },
            headers=auth_headers,
        )

        assert response2.status_code == 200

        # Verify override
        response3 = client.get("/api/v1/models", headers=auth_headers)
        data = response3.json()

        assert data["selected_per_session"][session_id] == "model-v2"

    def test_select_model_multiple_sessions(self, client, auth_headers):
        """Test selecting different models for different sessions."""
        session_ids = [str(uuid4()) for _ in range(3)]
        models = ["model-1", "model-2", "model-3"]

        # Select different models for each session
        for session_id, model in zip(session_ids, models):
            response = client.post(
                "/api/v1/models/select",
                json={
                    "model": model,
                    "scope": "session",
                    "session_id": session_id,
                },
                headers=auth_headers,
            )

            assert response.status_code == 200

        # Verify all selections
        response = client.get("/api/v1/models", headers=auth_headers)
        data = response.json()

        for session_id, model in zip(session_ids, models):
            assert data["selected_per_session"][session_id] == model

    def test_select_model_with_special_characters(self, client, auth_headers):
        """Test selecting model with special characters in name."""
        special_models = [
            "model-with-dashes",
            "model_with_underscores",
            "model.with.dots",
            "model:v1.0",
        ]

        for model in special_models:
            response = client.post(
                "/api/v1/models/select",
                json={"model": model, "scope": "default"},
                headers=auth_headers,
            )

            # Should accept any string
            assert response.status_code == 200
            data = response.json()
            assert data["model"] == model

    def test_select_model_with_very_long_name(self, client, auth_headers):
        """Test selecting model with very long name."""
        long_model_name = "model-" + "x" * 1000

        response = client.post(
            "/api/v1/models/select",
            json={"model": long_model_name, "scope": "default"},
            headers=auth_headers,
        )

        # Should accept (no max length validation currently)
        assert response.status_code == 200
        data = response.json()
        assert data["model"] == long_model_name


@pytest.mark.integration
class TestModelsEndpointErrors:
    """Test cases for error handling in models endpoints."""

    def test_list_models_with_malformed_token(self, client):
        """Test listing models with malformed token header."""
        response = client.get(
            "/api/v1/models",
            headers={"X-Intaste-Token": "   "},  # Whitespace only
        )

        assert response.status_code == 401

    def test_select_model_with_malformed_json(self, client, auth_headers):
        """Test selecting model with malformed JSON."""
        response = client.post(
            "/api/v1/models/select",
            content="not-valid-json",
            headers={**auth_headers, "Content-Type": "application/json"},
        )

        assert response.status_code == 422

    def test_select_model_with_extra_fields(self, client, auth_headers):
        """Test selecting model with extra unknown fields."""
        response = client.post(
            "/api/v1/models/select",
            json={
                "model": "test-model",
                "scope": "default",
                "extra_field": "should_be_ignored",
            },
            headers=auth_headers,
        )

        # Should succeed, extra fields ignored
        assert response.status_code == 200

    def test_select_model_null_session_id(self, client, auth_headers):
        """Test selecting model with explicit null session_id for session scope."""
        response = client.post(
            "/api/v1/models/select",
            json={
                "model": "test-model",
                "scope": "session",
                "session_id": None,
            },
            headers=auth_headers,
        )

        # Should fail: session_id required for session scope
        assert response.status_code == 400
