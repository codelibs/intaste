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

from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    req_timeout_ms: int = Field(default=5000, validation_alias="REQ_TIMEOUT_MS")

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

    @property
    def intent_timeout_ms(self) -> int:
        """Timeout for intent extraction (40% of total budget)."""
        return int(self.req_timeout_ms * 0.4)

    @property
    def search_timeout_ms(self) -> int:
        """Timeout for search (40% of total budget)."""
        return int(self.req_timeout_ms * 0.4)

    @property
    def compose_timeout_ms(self) -> int:
        """Timeout for answer composition (20% of total budget)."""
        return int(self.req_timeout_ms * 0.2)


# Global settings instance
settings = Settings()
