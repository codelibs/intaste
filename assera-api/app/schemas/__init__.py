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
Pydantic schemas for Assera API.
"""

from .assist import (
    Answer,
    AssistQueryRequest,
    AssistQueryResponse,
    Citation,
    FeedbackRequest,
    Notice,
    Session,
    Timings,
)
from .common import ErrorResponse, HealthResponse
from .models import ModelSelectRequest, ModelSelectResponse, ModelsResponse

__all__ = [
    "Answer",
    "AssistQueryRequest",
    "AssistQueryResponse",
    "Citation",
    "ErrorResponse",
    "FeedbackRequest",
    "HealthResponse",
    "ModelsResponse",
    "ModelSelectRequest",
    "ModelSelectResponse",
    "Notice",
    "Session",
    "Timings",
]
