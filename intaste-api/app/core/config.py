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
Configuration management for Intaste API.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SearchAgentConfig(BaseModel):
    """
    Configuration for a single search agent.

    Used for multi-agent scenarios where multiple search agents
    can be configured and executed in parallel.
    """

    enabled: bool = True
    agent_type: Literal["fess", "mcp", "external_api", "vector"] = "fess"
    agent_id: str
    agent_name: str
    priority: int = 1  # Lower priority = executed first
    timeout_ms: int = 5000
    config: dict[str, Any] = Field(default_factory=dict)  # Agent-specific configuration


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # API Configuration
    api_version: str = "1.0.0"
    api_title: str = "Intaste Assisted API"
    api_description: str = "LLM-enhanced search API for Fess"
    debug: bool = Field(default=False, validation_alias="DEBUG")

    # Authentication
    intaste_api_token: str = Field(..., min_length=32, validation_alias="INTASTE_API_TOKEN")

    # Search Provider
    intaste_search_provider: Literal["fess"] = Field(
        default="fess", validation_alias="INTASTE_SEARCH_PROVIDER"
    )
    fess_base_url: str = Field(default="http://fess:8080", validation_alias="FESS_BASE_URL")
    fess_timeout_ms: int = Field(default=2000, validation_alias="FESS_TIMEOUT_MS")

    # LLM Provider
    intaste_llm_provider: Literal["ollama"] = Field(
        default="ollama", validation_alias="INTASTE_LLM_PROVIDER"
    )
    intaste_default_model: str = Field(default="gpt-oss", validation_alias="INTASTE_DEFAULT_MODEL")
    ollama_base_url: str = Field(default="http://ollama:11434", validation_alias="OLLAMA_BASE_URL")
    intaste_llm_timeout_ms: int = Field(default=3000, validation_alias="INTASTE_LLM_TIMEOUT_MS")
    intaste_llm_max_tokens: int = Field(default=512, validation_alias="INTASTE_LLM_MAX_TOKENS")
    intaste_llm_temperature: float = Field(default=0.2, validation_alias="INTASTE_LLM_TEMPERATURE")
    intaste_llm_top_p: float = Field(default=0.9, validation_alias="INTASTE_LLM_TOP_P")

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, validation_alias="INTASTE_RATE_LIMIT_PER_MINUTE")

    # Request Timeout Budget (ms)
    req_timeout_ms: int = Field(default=15000, validation_alias="REQ_TIMEOUT_MS")

    # Relevance Evaluation
    intaste_relevance_threshold: float = Field(
        default=0.3, ge=0.0, le=1.0, validation_alias="INTASTE_RELEVANCE_THRESHOLD"
    )
    intaste_max_retry_count: int = Field(
        default=2, ge=0, le=5, validation_alias="INTASTE_MAX_RETRY_COUNT"
    )

    # Search Results Configuration
    intaste_max_search_results: int = Field(
        default=100, ge=1, le=500, validation_alias="INTASTE_MAX_SEARCH_RESULTS"
    )
    intaste_relevance_evaluation_count: int = Field(
        default=10, ge=1, le=100, validation_alias="INTASTE_RELEVANCE_EVALUATION_COUNT"
    )
    intaste_selected_relevance_threshold: float = Field(
        default=0.8, ge=0.0, le=1.0, validation_alias="INTASTE_SELECTED_RELEVANCE_THRESHOLD"
    )
    intaste_relevance_max_concurrent: int = Field(
        default=5, ge=1, le=20, validation_alias="INTASTE_RELEVANCE_MAX_CONCURRENT"
    )

    # LLM Warmup
    intaste_llm_warmup_enabled: bool = Field(
        default=True, validation_alias="INTASTE_LLM_WARMUP_ENABLED"
    )
    intaste_llm_warmup_timeout_ms: int = Field(
        default=30000, validation_alias="INTASTE_LLM_WARMUP_TIMEOUT_MS"
    )

    # Multi-Agent Configuration
    intaste_multi_agent_enabled: bool = Field(
        default=False, validation_alias="INTASTE_MULTI_AGENT_ENABLED"
    )
    intaste_search_agents: str | list[SearchAgentConfig] = Field(
        default="[]", validation_alias="INTASTE_SEARCH_AGENTS"
    )

    # CORS
    cors_origins: str | list[str] = Field(
        default=["http://localhost:3000"], validation_alias="CORS_ORIGINS"
    )

    # Logging
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    log_pii_masking: bool = Field(default=True, validation_alias="LOG_PII_MASKING")
    log_format: Literal["text", "json"] = Field(default="text", validation_alias="LOG_FORMAT")
    log_max_prompt_chars: int = Field(default=1000, validation_alias="LOG_MAX_PROMPT_CHARS")
    log_max_response_chars: int = Field(default=1000, validation_alias="LOG_MAX_RESPONSE_CHARS")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """
        Parse CORS_ORIGINS from environment variable.
        Accepts both comma-separated strings and JSON arrays.
        """
        if isinstance(v, str):
            # Handle comma-separated string
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("intaste_search_agents", mode="before")
    @classmethod
    def parse_search_agents(cls, v: str | list[SearchAgentConfig]) -> list[SearchAgentConfig]:
        """
        Parse INTASTE_SEARCH_AGENTS from environment variable.
        Accepts JSON string or list of SearchAgentConfig objects.
        """
        import json

        if isinstance(v, str):
            # Parse JSON string
            if not v or v == "[]":
                return []
            try:
                agents_data = json.loads(v)
                return [SearchAgentConfig(**agent) for agent in agents_data]
            except (json.JSONDecodeError, ValueError) as e:
                raise ValueError(f"Invalid INTASTE_SEARCH_AGENTS format: {e}") from e
        return v

    @property
    def intent_timeout_ms(self) -> int:
        """Timeout for intent extraction (20% of total budget)."""
        return int(self.req_timeout_ms * 0.2)

    @property
    def search_timeout_ms(self) -> int:
        """Timeout for search execution (15% of total budget)."""
        return int(self.req_timeout_ms * 0.15)

    @property
    def relevance_timeout_ms(self) -> int:
        """Timeout for relevance evaluation (25% of total budget, increased for detailed reasoning)."""
        return int(self.req_timeout_ms * 0.25)

    @property
    def retry_budget_ms(self) -> int:
        """Total budget for retry attempts (20% of total budget)."""
        return int(self.req_timeout_ms * 0.20)

    @property
    def retry_intent_timeout_ms(self) -> int:
        """Timeout for intent extraction during retry (40% of retry budget)."""
        return int(self.retry_budget_ms * 0.4)

    @property
    def retry_search_timeout_ms(self) -> int:
        """Timeout for search execution during retry (40% of retry budget)."""
        return int(self.retry_budget_ms * 0.4)

    @property
    def retry_relevance_timeout_ms(self) -> int:
        """Timeout for relevance evaluation during retry (20% of retry budget)."""
        return int(self.retry_budget_ms * 0.2)

    @property
    def compose_timeout_ms(self) -> int:
        """Timeout for answer composition (15% of total budget, increased for detailed explanations)."""
        return int(self.req_timeout_ms * 0.15)


# Global settings instance
settings = Settings()
