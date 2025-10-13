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
Factory for creating LLM client instances based on configuration.
"""

from collections.abc import Callable
from typing import Any

from .base import LLMClient
from .ollama import OllamaClient

# Type alias for client constructor
ClientConstructor = Callable[[dict[str, Any]], LLMClient]


class LLMClientFactory:
    """
    Factory for creating LLM client instances dynamically.

    This factory uses a registry pattern to allow easy addition of new
    LLM providers without modifying existing code.
    """

    _registry: dict[str, ClientConstructor] = {}

    @classmethod
    def register(cls, name: str, constructor: ClientConstructor) -> None:
        """
        Register an LLM client constructor.

        Args:
            name: Client name (e.g., 'ollama', 'openai', 'anthropic')
            constructor: Callable that takes config dict and returns LLMClient instance
        """
        cls._registry[name] = constructor

    @classmethod
    def create(cls, client_name: str, config: dict[str, Any]) -> LLMClient:
        """
        Create an LLM client instance.

        Args:
            client_name: Name of the client to create
            config: Configuration dictionary for the client

        Returns:
            LLMClient instance

        Raises:
            ValueError: If client_name is not registered
        """
        if client_name not in cls._registry:
            available = ", ".join(cls._registry.keys())
            raise ValueError(f"Unknown LLM client: {client_name}. Available clients: {available}")

        constructor = cls._registry[client_name]
        return constructor(config)

    @classmethod
    def create_from_settings(cls, settings: Any) -> LLMClient:
        """
        Create an LLM client instance from Settings object.

        Args:
            settings: Settings object containing client configuration

        Returns:
            LLMClient instance configured from settings
        """
        client_name = settings.assera_llm_provider
        config = {
            "base_url": settings.ollama_base_url,
            "model": settings.assera_default_model,
            "timeout_ms": settings.assera_llm_timeout_ms,
            "temperature": settings.assera_llm_temperature,
            "top_p": settings.assera_llm_top_p,
        }
        return cls.create(client_name, config)


# Register built-in clients
def _create_ollama_client(config: dict[str, Any]) -> LLMClient:
    """Create OllamaClient from config dict."""
    return OllamaClient(
        base_url=config["base_url"],
        model=config["model"],
        timeout_ms=config["timeout_ms"],
        temperature=config["temperature"],
        top_p=config["top_p"],
    )


LLMClientFactory.register("ollama", _create_ollama_client)
