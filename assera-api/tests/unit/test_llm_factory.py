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
Unit tests for LLMClientFactory.
"""

from unittest.mock import MagicMock

import pytest

from app.core.llm.factory import LLMClientFactory
from app.core.llm.ollama import OllamaClient


@pytest.mark.unit
class TestLLMClientFactory:
    """Test cases for LLMClientFactory."""

    def test_create_ollama_client(self):
        """Test creating an Ollama client."""
        config = {
            "base_url": "http://localhost:11434",
            "model": "llama3",
            "timeout_ms": 5000,
            "temperature": 0.3,
            "top_p": 0.95,
        }

        client = LLMClientFactory.create("ollama", config)

        assert isinstance(client, OllamaClient)
        assert client.base_url == "http://localhost:11434"
        assert client.model == "llama3"
        assert client.timeout_ms == 5000
        assert client.temperature == 0.3
        assert client.top_p == 0.95

    def test_create_unknown_client(self):
        """Test creating an unknown client raises ValueError."""
        config = {"base_url": "http://localhost:11434"}

        with pytest.raises(ValueError) as exc_info:
            LLMClientFactory.create("unknown", config)

        assert "Unknown LLM client: unknown" in str(exc_info.value)
        assert "Available clients:" in str(exc_info.value)

    def test_create_from_settings(self):
        """Test creating client from settings object."""
        # Mock settings object
        settings = MagicMock()
        settings.assera_llm_provider = "ollama"
        settings.ollama_base_url = "http://test-ollama:11434"
        settings.assera_default_model = "gpt-oss"
        settings.assera_llm_timeout_ms = 4000
        settings.assera_llm_temperature = 0.25
        settings.assera_llm_top_p = 0.85

        client = LLMClientFactory.create_from_settings(settings)

        assert isinstance(client, OllamaClient)
        assert client.base_url == "http://test-ollama:11434"
        assert client.model == "gpt-oss"
        assert client.timeout_ms == 4000
        assert client.temperature == 0.25
        assert client.top_p == 0.85

    def test_register_custom_client(self):
        """Test registering a custom LLM client."""

        class CustomLLMClient:
            def __init__(self, base_url: str, model: str):
                self.base_url = base_url
                self.model = model

        def custom_constructor(config):
            return CustomLLMClient(base_url=config["base_url"], model=config["model"])

        # Register custom client
        LLMClientFactory.register("custom", custom_constructor)

        # Create instance
        config = {"base_url": "http://custom:9000", "model": "custom-model"}
        client = LLMClientFactory.create("custom", config)

        assert isinstance(client, CustomLLMClient)
        assert client.base_url == "http://custom:9000"
        assert client.model == "custom-model"

    def test_ollama_client_registered_by_default(self):
        """Test that Ollama client is registered by default."""
        # Verify 'ollama' is in the registry
        assert "ollama" in LLMClientFactory._registry
