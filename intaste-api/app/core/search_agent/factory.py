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
Factory for creating search agent instances.
"""

import logging

from ..config import Settings
from ..llm.base import LLMClient
from ..search_provider.base import SearchProvider
from .base import SearchAgent
from .fess import FessSearchAgent

logger = logging.getLogger(__name__)


def create_search_agent(
    search_provider: SearchProvider,
    llm_client: LLMClient,
    settings: Settings,
) -> SearchAgent:
    """
    Create a search agent instance based on configuration.

    Args:
        search_provider: Search provider instance (e.g., FessSearchProvider)
        llm_client: LLM client instance (e.g., OllamaClient)
        settings: Application settings

    Returns:
        SearchAgent: Configured search agent instance

    Note:
        Currently only supports Fess search agent. Future implementations
        may support additional agent types (MCP, Elasticsearch, etc.)
    """
    # Currently only Fess agent is supported
    # In the future, this could be configurable via settings
    agent_type = getattr(settings, "search_agent_type", "fess")

    if agent_type != "fess":
        logger.warning(f"Unsupported search agent type: {agent_type}. Falling back to 'fess'")

    logger.info("Creating FessSearchAgent")
    agent = FessSearchAgent(
        search_provider=search_provider,
        llm_client=llm_client,
        intent_timeout_ms=settings.intent_timeout_ms,
        search_timeout_ms=settings.search_timeout_ms,
    )

    logger.debug(
        f"FessSearchAgent created with intent_timeout={settings.intent_timeout_ms}ms, "
        f"search_timeout={settings.search_timeout_ms}ms"
    )

    return agent
