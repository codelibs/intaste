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
Unit tests for configuration management.
"""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


@pytest.fixture
def clean_env(monkeypatch):
    """Provide a clean environment for Settings tests."""
    # Set only the required token
    monkeypatch.setenv("INTASTE_API_TOKEN", "test-token-32-characters-long-secure")
    # Clear other potentially interfering env vars
    for key in [
        "FESS_BASE_URL",
        "OLLAMA_BASE_URL",
        "CORS_ORIGINS",
        "REQ_TIMEOUT_MS",
        "FESS_TIMEOUT_MS",
        "INTASTE_LLM_TIMEOUT_MS",
        "INTASTE_SEARCH_PROVIDER",
        "INTASTE_LLM_PROVIDER",
        "LOG_LEVEL",
        "LOG_FORMAT",
        "DEBUG",
    ]:
        monkeypatch.delenv(key, raising=False)


@pytest.mark.unit
class TestSettingsValidation:
    """Test cases for Settings validation."""

    def test_valid_settings(self, clean_env):
        """Test Settings with valid configuration."""
        settings = Settings()

        assert settings.intaste_api_token == "test-token-32-characters-long-secure"
        assert settings.api_version == "1.0.0"
        assert settings.debug is False

    def test_api_token_required(self, monkeypatch):
        """Test that INTASTE_API_TOKEN is required."""
        # Clear environment variable
        monkeypatch.delenv("INTASTE_API_TOKEN", raising=False)

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        errors = exc_info.value.errors()
        # Check that INTASTE_API_TOKEN (env var) or intaste_api_token (field) is in the error
        assert any(
            "INTASTE_API_TOKEN" in [str(item) for item in error.get("loc", [])]
            or "intaste_api_token" in [str(item) for item in error.get("loc", [])]
            for error in errors
        ), f"Should fail on missing INTASTE_API_TOKEN, got errors: {errors}"

    def test_api_token_min_length(self, monkeypatch):
        """Test INTASTE_API_TOKEN minimum length (min_length=32)."""
        # Clear env first
        monkeypatch.delenv("INTASTE_API_TOKEN", raising=False)

        # Valid: exactly 32 characters
        monkeypatch.setenv("INTASTE_API_TOKEN", "a" * 32)
        settings = Settings()
        assert len(settings.intaste_api_token) == 32

        # Invalid: 31 characters
        monkeypatch.setenv("INTASTE_API_TOKEN", "a" * 31)
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        errors = exc_info.value.errors()
        assert any("string_too_short" in error["type"] for error in errors)


@pytest.mark.unit
class TestSettingsDefaults:
    """Test cases for Settings default values."""

    def test_default_values(self, clean_env):
        """Test Settings default values."""
        settings = Settings()

        # API defaults
        assert settings.api_version == "1.0.0"
        assert settings.api_title == "Intaste Assisted API"

        # Search provider defaults
        assert settings.intaste_search_provider == "fess"
        assert settings.fess_base_url == "http://fess:8080"
        assert settings.fess_timeout_ms == 2000

        # LLM provider defaults
        assert settings.intaste_llm_provider == "ollama"
        assert settings.intaste_default_model == "gpt-oss"
        assert settings.ollama_base_url == "http://ollama:11434"
        assert settings.intaste_llm_timeout_ms == 3000

    def test_timeout_budget_properties(self, monkeypatch):
        """Test timeout budget calculation properties."""
        monkeypatch.setenv("INTASTE_API_TOKEN", "test-token-32-characters-long-secure")
        monkeypatch.setenv("REQ_TIMEOUT_MS", "15000")

        settings = Settings()

        # Intent: 20% of total
        assert settings.intent_timeout_ms == 3000

        # Search: 15% of total
        assert settings.search_timeout_ms == 2250

        # Relevance: 25% of total (increased for detailed reasoning)
        assert settings.relevance_timeout_ms == 3750

        # Retry budget: 20% of total (reduced to accommodate relevance increase)
        assert settings.retry_budget_ms == 3000

        # Compose: 15% of total (increased for detailed explanations)
        assert settings.compose_timeout_ms == 2250

    def test_timeout_budget_custom_total(self, monkeypatch):
        """Test timeout budget with custom total."""
        monkeypatch.setenv("INTASTE_API_TOKEN", "test-token-32-characters-long-secure")
        monkeypatch.setenv("REQ_TIMEOUT_MS", "30000")

        settings = Settings()

        assert settings.intent_timeout_ms == 6000  # 20%
        assert settings.search_timeout_ms == 4500  # 15%
        assert settings.relevance_timeout_ms == 7500  # 25%
        assert settings.retry_budget_ms == 6000  # 20%
        assert settings.compose_timeout_ms == 4500  # 15%


@pytest.mark.unit
class TestCORSOriginsValidation:
    """Test cases for CORS origins validation."""

    def test_cors_origins_as_list(self, monkeypatch):
        """Test CORS origins as list."""
        monkeypatch.setenv("INTASTE_API_TOKEN", "test-token-32-characters-long-secure")
        monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001")

        settings = Settings()

        assert settings.cors_origins == ["http://localhost:3000", "http://localhost:3001"]

    def test_cors_origins_as_comma_separated_string(self, monkeypatch):
        """Test CORS origins as comma-separated string."""
        monkeypatch.setenv("INTASTE_API_TOKEN", "test-token-32-characters-long-secure")
        monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001")

        settings = Settings()

        assert settings.cors_origins == ["http://localhost:3000", "http://localhost:3001"]

    def test_cors_origins_with_whitespace(self, monkeypatch):
        """Test CORS origins with whitespace are trimmed."""
        monkeypatch.setenv("INTASTE_API_TOKEN", "test-token-32-characters-long-secure")
        monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000 , http://localhost:3001 ")

        settings = Settings()

        assert settings.cors_origins == ["http://localhost:3000", "http://localhost:3001"]

    def test_cors_origins_empty_string(self, monkeypatch):
        """Test CORS origins with empty string."""
        monkeypatch.setenv("INTASTE_API_TOKEN", "test-token-32-characters-long-secure")
        monkeypatch.setenv("CORS_ORIGINS", "")

        settings = Settings()

        assert settings.cors_origins == []

    def test_cors_origins_single_value(self, monkeypatch):
        """Test CORS origins with single value."""
        monkeypatch.setenv("INTASTE_API_TOKEN", "test-token-32-characters-long-secure")
        monkeypatch.setenv("CORS_ORIGINS", "http://example.com")

        settings = Settings()

        assert settings.cors_origins == ["http://example.com"]


@pytest.mark.unit
class TestSettingsEnvironmentVariables:
    """Test cases for Settings from environment variables."""

    def test_settings_from_env_vars(self, monkeypatch):
        """Test Settings loaded from environment variables."""
        monkeypatch.setenv("INTASTE_API_TOKEN", "env-token-32-characters-long-secure")
        monkeypatch.setenv("FESS_BASE_URL", "http://custom-fess:9000")
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://custom-ollama:12345")
        monkeypatch.setenv("REQ_TIMEOUT_MS", "20000")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")

        settings = Settings()

        assert settings.intaste_api_token == "env-token-32-characters-long-secure"
        assert settings.fess_base_url == "http://custom-fess:9000"
        assert settings.ollama_base_url == "http://custom-ollama:12345"
        assert settings.req_timeout_ms == 20000
        assert settings.log_level == "DEBUG"


@pytest.mark.unit
class TestSettingsLiteralFields:
    """Test cases for Literal field validation."""

    def test_search_provider_literal(self, monkeypatch):
        """Test intaste_search_provider Literal validation."""
        # Valid: "fess"
        monkeypatch.setenv("INTASTE_API_TOKEN", "test-token-32-characters-long-secure")
        monkeypatch.setenv("INTASTE_SEARCH_PROVIDER", "fess")

        settings = Settings()
        assert settings.intaste_search_provider == "fess"

        # Invalid: other value
        monkeypatch.setenv("INTASTE_SEARCH_PROVIDER", "elasticsearch")
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        errors = exc_info.value.errors()
        assert any("literal_error" in error["type"] or "enum" in error["type"] for error in errors)

    def test_llm_provider_literal(self, monkeypatch):
        """Test intaste_llm_provider Literal validation."""
        # Valid: "ollama"
        monkeypatch.setenv("INTASTE_API_TOKEN", "test-token-32-characters-long-secure")
        monkeypatch.setenv("INTASTE_LLM_PROVIDER", "ollama")

        settings = Settings()
        assert settings.intaste_llm_provider == "ollama"

        # Invalid: other value
        monkeypatch.setenv("INTASTE_LLM_PROVIDER", "openai")
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        errors = exc_info.value.errors()
        assert any("literal_error" in error["type"] or "enum" in error["type"] for error in errors)

    def test_log_format_literal(self, monkeypatch):
        """Test log_format Literal validation."""
        # Valid: "text"
        monkeypatch.setenv("INTASTE_API_TOKEN", "test-token-32-characters-long-secure")
        monkeypatch.setenv("LOG_FORMAT", "text")

        settings = Settings()
        assert settings.log_format == "text"

        # Valid: "json"
        monkeypatch.setenv("LOG_FORMAT", "json")
        settings = Settings()
        assert settings.log_format == "json"

        # Invalid: other value
        monkeypatch.setenv("LOG_FORMAT", "xml")
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        errors = exc_info.value.errors()
        assert any("literal_error" in error["type"] or "enum" in error["type"] for error in errors)


@pytest.mark.unit
class TestSettingsNumericValidation:
    """Test cases for numeric field validation."""

    def test_explicit_timeout_values(self, monkeypatch):
        """Test that explicit timeout values are accepted."""
        monkeypatch.setenv("INTASTE_API_TOKEN", "test-token-32-characters-long-secure")
        monkeypatch.setenv("FESS_TIMEOUT_MS", "5000")
        monkeypatch.setenv("INTASTE_LLM_TIMEOUT_MS", "10000")
        monkeypatch.setenv("REQ_TIMEOUT_MS", "30000")

        settings = Settings()

        # Values are accepted as provided
        assert settings.fess_timeout_ms == 5000
        assert settings.intaste_llm_timeout_ms == 10000
        assert settings.req_timeout_ms == 30000

    def test_temperature_range(self, monkeypatch):
        """Test LLM temperature value range."""
        monkeypatch.setenv("INTASTE_API_TOKEN", "test-token-32-characters-long-secure")

        # Common range: 0.0 to 2.0 (OpenAI/Ollama)
        monkeypatch.setenv("INTASTE_LLM_TEMPERATURE", "0.0")
        settings = Settings()
        assert settings.intaste_llm_temperature == 0.0

        monkeypatch.setenv("INTASTE_LLM_TEMPERATURE", "2.0")
        settings = Settings()
        assert settings.intaste_llm_temperature == 2.0

        # Note: No validation for out-of-range values currently
        monkeypatch.setenv("INTASTE_LLM_TEMPERATURE", "5.0")
        settings = Settings()
        assert settings.intaste_llm_temperature == 5.0

    def test_top_p_range(self, monkeypatch):
        """Test LLM top_p value range."""
        monkeypatch.setenv("INTASTE_API_TOKEN", "test-token-32-characters-long-secure")

        # Common range: 0.0 to 1.0
        monkeypatch.setenv("INTASTE_LLM_TOP_P", "0.0")
        settings = Settings()
        assert settings.intaste_llm_top_p == 0.0

        monkeypatch.setenv("INTASTE_LLM_TOP_P", "1.0")
        settings = Settings()
        assert settings.intaste_llm_top_p == 1.0


@pytest.mark.unit
class TestSettingsBooleanFields:
    """Test cases for boolean field validation."""

    def test_debug_mode(self, monkeypatch):
        """Test debug mode flag."""
        monkeypatch.setenv("INTASTE_API_TOKEN", "test-token-32-characters-long-secure")

        monkeypatch.setenv("DEBUG", "true")
        settings = Settings()
        assert settings.debug is True

        monkeypatch.setenv("DEBUG", "false")
        settings = Settings()
        assert settings.debug is False

    def test_llm_warmup_enabled(self, monkeypatch):
        """Test LLM warmup enabled flag."""
        monkeypatch.setenv("INTASTE_API_TOKEN", "test-token-32-characters-long-secure")

        monkeypatch.setenv("INTASTE_LLM_WARMUP_ENABLED", "false")
        settings = Settings()
        assert settings.intaste_llm_warmup_enabled is False

        monkeypatch.setenv("INTASTE_LLM_WARMUP_ENABLED", "true")
        settings = Settings()
        assert settings.intaste_llm_warmup_enabled is True

    def test_log_pii_masking(self, monkeypatch):
        """Test PII masking flag."""
        monkeypatch.setenv("INTASTE_API_TOKEN", "test-token-32-characters-long-secure")

        monkeypatch.setenv("LOG_PII_MASKING", "false")
        settings = Settings()
        assert settings.log_pii_masking is False

        monkeypatch.setenv("LOG_PII_MASKING", "true")
        settings = Settings()
        assert settings.log_pii_masking is True
