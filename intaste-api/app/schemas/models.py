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
Schemas for /models endpoints.
"""

from typing import Literal

from pydantic import BaseModel, Field


class ModelsResponse(BaseModel):
    """
    Response listing available models.
    """

    default: str
    available: list[str]
    selected_per_session: dict[str, str] = Field(default_factory=dict)


class ModelSelectRequest(BaseModel):
    """
    Request to select a model.
    """

    model: str
    scope: Literal["default", "session"]
    session_id: str | None = Field(None, description="Required when scope=session")


class ModelSelectResponse(BaseModel):
    """
    Response after model selection.
    """

    status: str = "ok"
    effective_scope: str
    model: str
