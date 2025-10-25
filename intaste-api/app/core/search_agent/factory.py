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
from .multi import MultiSearchAgent

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
        SearchAgent: Configured search agent instance (single or multi-agent)

    Note:
        If INTASTE_MULTI_AGENT_ENABLED=True and agents are configured,
        returns MultiSearchAgent. Otherwise, returns single FessSearchAgent.
    """
    # Check if multi-agent mode is enabled
    if settings.intaste_multi_agent_enabled and settings.intaste_search_agents:
        # Type assertion for mypy (validator ensures this is always list[SearchAgentConfig])
        agent_configs = settings.intaste_search_agents
        if not isinstance(agent_configs, str):
            # agent_configs is list[SearchAgentConfig]
            logger.info(f"Multi-agent mode enabled: {len(agent_configs)} agents configured")

            # Create individual agents based on configuration
            agents = []
            for agent_config in agent_configs:
                if not agent_config.enabled:
                    logger.info(f"Agent {agent_config.agent_id} is disabled, skipping")
                    continue

                if agent_config.agent_type == "fess":
                    agent = FessSearchAgent(
                        search_provider=search_provider,
                        llm_client=llm_client,
                        intent_timeout_ms=agent_config.timeout_ms,
                        search_timeout_ms=agent_config.timeout_ms,
                        agent_id=agent_config.agent_id,
                        agent_name=agent_config.agent_name,
                    )
                    agents.append((agent_config.agent_id, agent_config.agent_name, agent))
                    logger.info(f"Created FessSearchAgent: {agent_config.agent_id}")
                else:
                    logger.warning(
                        f"Unsupported agent type: {agent_config.agent_type} for agent {agent_config.agent_id}"
                    )

            if not agents:
                logger.warning(
                    "No enabled agents configured, falling back to single FessSearchAgent"
                )
            elif len(agents) == 1:
                logger.info("Only one agent configured, using single agent instead of multi-agent")
                return agents[0][2]  # Return the single agent instance
            else:
                # Create MultiSearchAgent
                logger.info(f"Creating MultiSearchAgent with {len(agents)} agents")
                return MultiSearchAgent(
                    agents=agents,
                    llm_client=llm_client,
                    merge_timeout_ms=5000,  # TODO: make configurable
                )
        else:
            # This should never happen due to validator, but satisfy mypy
            logger.warning("intaste_search_agents is unexpectedly a string, using single agent")

    # Default: single FessSearchAgent
    logger.info("Creating single FessSearchAgent (multi-agent disabled or not configured)")
    agent = FessSearchAgent(
        search_provider=search_provider,
        llm_client=llm_client,
        intent_timeout_ms=settings.intent_timeout_ms,
        search_timeout_ms=settings.search_timeout_ms,
        agent_id="fess",
        agent_name="FessSearchAgent",
    )

    logger.debug(
        f"FessSearchAgent created with intent_timeout={settings.intent_timeout_ms}ms, "
        f"search_timeout={settings.search_timeout_ms}ms"
    )

    return agent
