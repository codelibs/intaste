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
Unit tests for SearchProviderFactory.
"""

from unittest.mock import MagicMock

import pytest

from app.core.search_provider.factory import SearchProviderFactory
from app.core.search_provider.fess import FessSearchProvider


@pytest.mark.unit
class TestSearchProviderFactory:
    """Test cases for SearchProviderFactory."""

    def test_create_fess_provider(self):
        """Test creating a Fess provider."""
        config = {
            "base_url": "http://localhost:8080",
            "timeout_ms": 3000,
        }

        provider = SearchProviderFactory.create("fess", config)

        assert isinstance(provider, FessSearchProvider)
        assert provider.base_url == "http://localhost:8080"
        assert provider.timeout_ms == 3000

    def test_create_unknown_provider(self):
        """Test creating an unknown provider raises ValueError."""
        config = {"base_url": "http://localhost:8080"}

        with pytest.raises(ValueError) as exc_info:
            SearchProviderFactory.create("unknown", config)

        assert "Unknown search provider: unknown" in str(exc_info.value)
        assert "Available providers:" in str(exc_info.value)

    def test_create_from_settings(self):
        """Test creating provider from settings object."""
        # Mock settings object
        settings = MagicMock()
        settings.intaste_search_provider = "fess"
        settings.fess_base_url = "http://test-fess:8080"
        settings.fess_timeout_ms = 2500

        provider = SearchProviderFactory.create_from_settings(settings)

        assert isinstance(provider, FessSearchProvider)
        assert provider.base_url == "http://test-fess:8080"
        assert provider.timeout_ms == 2500

    def test_register_custom_provider(self):
        """Test registering a custom provider."""

        class CustomSearchProvider:
            def __init__(self, base_url: str):
                self.base_url = base_url

        def custom_constructor(config):
            return CustomSearchProvider(base_url=config["base_url"])

        # Register custom provider
        SearchProviderFactory.register("custom", custom_constructor)

        # Create instance
        config = {"base_url": "http://custom:9000"}
        provider = SearchProviderFactory.create("custom", config)

        assert isinstance(provider, CustomSearchProvider)
        assert provider.base_url == "http://custom:9000"

    def test_fess_provider_registered_by_default(self):
        """Test that Fess provider is registered by default."""
        # Verify 'fess' is in the registry
        assert "fess" in SearchProviderFactory._registry
