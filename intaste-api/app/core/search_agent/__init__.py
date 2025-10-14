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
Search agent abstraction layer.

A search agent encapsulates the complete search workflow:
- Intent extraction via LLM
- Search execution via search provider
- Result aggregation

This allows for multiple search agent implementations with different
query processing strategies.
"""

from .base import (
    BaseSearchAgent,
    CitationsEventData,
    IntentEventData,
    SearchAgent,
    SearchAgentResult,
    SearchAgentTimings,
    SearchEvent,
)
from .factory import create_search_agent
from .fess import FessSearchAgent

__all__ = [
    # Base classes and protocols
    "SearchAgent",
    "BaseSearchAgent",
    # Models
    "SearchAgentResult",
    "SearchAgentTimings",
    "SearchEvent",
    "IntentEventData",
    "CitationsEventData",
    # Implementations
    "FessSearchAgent",
    # Factory
    "create_search_agent",
]
