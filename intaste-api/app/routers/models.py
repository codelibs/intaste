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
Model management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.config import settings
from ..core.security.auth import verify_api_token
from ..i18n import _
from ..schemas.models import ModelSelectRequest, ModelSelectResponse, ModelsResponse

router = APIRouter(prefix="/models", tags=["models"])

# In-memory model selection storage (TODO: Use Redis for production)
selected_models: dict[str, str] = {}  # session_id -> model_name


@router.get(
    "",
    response_model=ModelsResponse,
    summary="List available models",
    dependencies=[Depends(verify_api_token)],
)
async def list_models() -> ModelsResponse:
    """
    List available LLM models and current selection.

    Returns:
        ModelsResponse: Default model, available models, and per-session selections
    """
    # TODO: Query Ollama API for available models
    available = [settings.intaste_default_model, "mistral", "llama3"]

    return ModelsResponse(
        default=settings.intaste_default_model,
        available=available,
        selected_per_session=selected_models.copy(),
    )


@router.post(
    "/select",
    response_model=ModelSelectResponse,
    summary="Select a model",
    dependencies=[Depends(verify_api_token)],
)
async def select_model(request: ModelSelectRequest) -> ModelSelectResponse:
    """
    Select an LLM model for default or session scope.

    Args:
        request: Model selection request with model name, scope, and optional session ID

    Returns:
        ModelSelectResponse: Confirmation of model selection

    Raises:
        HTTPException: 400 if session_id is missing when scope=session
    """
    if request.scope == "session":
        if not request.session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "BAD_REQUEST",
                    "message": _("session_id is required when scope=session", language="en"),
                },
            )
        selected_models[request.session_id] = request.model
        effective_scope = "session"
    else:
        # Default scope (would require restart or global state in production)
        effective_scope = "default"

    return ModelSelectResponse(
        status="ok",
        effective_scope=effective_scope,
        model=request.model,
    )
