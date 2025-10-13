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
Factory for creating search provider instances based on configuration.
"""

from collections.abc import Callable
from typing import Any

from .base import SearchProvider
from .fess import FessSearchProvider

# Type alias for provider constructor
ProviderConstructor = Callable[[dict[str, Any]], SearchProvider]


class SearchProviderFactory:
    """
    Factory for creating search provider instances dynamically.

    This factory uses a registry pattern to allow easy addition of new
    search providers without modifying existing code.
    """

    _registry: dict[str, ProviderConstructor] = {}

    @classmethod
    def register(cls, name: str, constructor: ProviderConstructor) -> None:
        """
        Register a search provider constructor.

        Args:
            name: Provider name (e.g., 'fess', 'elasticsearch')
            constructor: Callable that takes config dict and returns SearchProvider instance
        """
        cls._registry[name] = constructor

    @classmethod
    def create(cls, provider_name: str, config: dict[str, Any]) -> SearchProvider:
        """
        Create a search provider instance.

        Args:
            provider_name: Name of the provider to create
            config: Configuration dictionary for the provider

        Returns:
            SearchProvider instance

        Raises:
            ValueError: If provider_name is not registered
        """
        if provider_name not in cls._registry:
            available = ", ".join(cls._registry.keys())
            raise ValueError(
                f"Unknown search provider: {provider_name}. " f"Available providers: {available}"
            )

        constructor = cls._registry[provider_name]
        return constructor(config)

    @classmethod
    def create_from_settings(cls, settings: Any) -> SearchProvider:
        """
        Create a search provider instance from Settings object.

        Args:
            settings: Settings object containing provider configuration

        Returns:
            SearchProvider instance configured from settings
        """
        provider_name = settings.assera_search_provider
        config = {
            "base_url": settings.fess_base_url,
            "timeout_ms": settings.fess_timeout_ms,
        }
        return cls.create(provider_name, config)


# Register built-in providers
def _create_fess_provider(config: dict[str, Any]) -> FessSearchProvider:
    """Create FessSearchProvider from config dict."""
    return FessSearchProvider(
        base_url=config["base_url"],
        timeout_ms=config["timeout_ms"],
    )


SearchProviderFactory.register("fess", _create_fess_provider)
