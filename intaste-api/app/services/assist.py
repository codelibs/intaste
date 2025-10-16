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
Assisted search service orchestrating SearchAgent → Compose flow.
"""

import logging
from typing import Any

from ..core.llm.base import LLMClient
from ..core.search_agent.base import SearchAgent

logger = logging.getLogger(__name__)


class AssistService:
    """
    Core service for assisted search combining SearchAgent and LLM.
    """

    def __init__(self, search_agent: SearchAgent, llm_client: LLMClient):
        self.search_agent = search_agent
        self.llm_client = llm_client
        # In-memory session storage (TODO: Use Redis/database for production)
        self.sessions: dict[str, dict[str, Any]] = {}

    async def warmup(self, timeout_ms: int = 30000) -> bool:
        """
        Warm up the LLM model by preloading it into memory.
        This improves response times for the first user request.

        Args:
            timeout_ms: Timeout for warmup request (default: 30000ms = 30s)

        Returns:
            True if warmup succeeded, False otherwise
        """
        logger.info("Starting AssistService warmup")
        try:
            result = await self.llm_client.warmup(timeout_ms=timeout_ms)
            if result:
                logger.info("AssistService warmup completed successfully")
            else:
                logger.warning("AssistService warmup failed")
            return result
        except Exception as e:
            logger.error(f"AssistService warmup error: {e}", exc_info=True)
            return False
