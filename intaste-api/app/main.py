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
Intaste API - FastAPI application entry point.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .core.config import settings
from .core.llm.base import LLMClient
from .core.llm.factory import LLMClientFactory
from .core.search_agent.base import SearchAgent
from .core.search_agent.factory import create_search_agent
from .core.search_provider.base import SearchProvider
from .core.search_provider.factory import SearchProviderFactory
from .core.security.middleware import add_request_id_middleware, setup_cors
from .routers import assist_stream, health, models
from .services.assist import AssistService

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global instances
search_provider: SearchProvider | None = None
llm_client: LLMClient | None = None
search_agent: SearchAgent | None = None
assist_service: AssistService | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """
    Application lifespan manager for startup and shutdown.
    """
    global search_provider, llm_client, search_agent, assist_service

    # Startup
    logger.info("Starting Intaste API...")
    logger.info(f"Log Level: {settings.log_level}")
    logger.info(f"Debug Mode: {settings.debug}")
    logger.info(f"Search Provider: {settings.intaste_search_provider}")
    logger.info(f"Fess URL: {settings.fess_base_url}")
    logger.info(f"LLM Provider: {settings.intaste_llm_provider}")
    logger.info(f"Ollama URL: {settings.ollama_base_url}")
    logger.info(f"Default model: {settings.intaste_default_model}")

    # Debug: Print detailed configuration
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("=== Detailed Configuration ===")
        logger.debug(f"API Version: {settings.api_version}")
        logger.debug(f"CORS Origins: {settings.cors_origins}")
        logger.debug(f"Rate Limit: {settings.rate_limit_per_minute}/min")
        logger.debug(f"Request Timeout: {settings.req_timeout_ms}ms")
        logger.debug(f"  - Intent Timeout: {settings.intent_timeout_ms}ms (40%)")
        logger.debug(f"  - Search Timeout: {settings.search_timeout_ms}ms (40%)")
        logger.debug(f"  - Compose Timeout: {settings.compose_timeout_ms}ms (20%)")
        logger.debug(f"Fess Timeout: {settings.fess_timeout_ms}ms")
        logger.debug(f"LLM Timeout: {settings.intaste_llm_timeout_ms}ms")
        logger.debug(f"LLM Max Tokens: {settings.intaste_llm_max_tokens}")
        logger.debug(f"LLM Temperature: {settings.intaste_llm_temperature}")
        logger.debug(f"LLM Top-P: {settings.intaste_llm_top_p}")
        logger.debug(f"Log Format: {settings.log_format}")
        logger.debug(f"Log PII Masking: {settings.log_pii_masking}")
        logger.debug(f"Log Max Prompt Chars: {settings.log_max_prompt_chars}")
        logger.debug(f"Log Max Response Chars: {settings.log_max_response_chars}")
        logger.debug("==============================")

    # Initialize providers using factories
    logger.debug("Initializing search provider...")
    search_provider = SearchProviderFactory.create_from_settings(settings)
    logger.debug(f"Search provider initialized: {type(search_provider).__name__}")

    logger.debug("Initializing LLM client...")
    llm_client = LLMClientFactory.create_from_settings(settings)
    logger.debug(f"LLM client initialized: {type(llm_client).__name__}")

    # Initialize search agent
    logger.debug("Initializing search agent...")
    search_agent = create_search_agent(
        search_provider=search_provider,
        llm_client=llm_client,
        settings=settings,
    )
    logger.debug(f"Search agent initialized: {type(search_agent).__name__}")

    logger.debug("Initializing assist service...")
    assist_service = AssistService(
        search_agent=search_agent,
        llm_client=llm_client,
    )
    logger.debug("Assist service initialized")

    # Warm up LLM model if enabled
    if settings.intaste_llm_warmup_enabled:
        logger.info("LLM warmup enabled, preloading model...")
        try:
            warmup_success = await assist_service.warmup(
                timeout_ms=settings.intaste_llm_warmup_timeout_ms
            )
            if warmup_success:
                logger.info("LLM warmup completed successfully")
            else:
                logger.warning(
                    "LLM warmup failed, but continuing startup. "
                    "First requests may be slower while model loads."
                )
        except Exception as e:
            logger.error(
                f"LLM warmup error: {e}. Continuing startup, but first requests may be slower.",
                exc_info=True,
            )
    else:
        logger.info("LLM warmup disabled (INTASTE_LLM_WARMUP_ENABLED=false)")

    logger.info("Intaste API started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Intaste API...")
    if search_agent:
        logger.debug("Closing search agent...")
        await search_agent.close()
        logger.debug("Search agent closed")
    # Note: search_provider and llm_client are closed via search_agent.close()
    logger.info("Intaste API shut down complete")


# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Add middleware
setup_cors(app)
add_request_id_middleware(app)

# Include routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(assist_stream.router, prefix="/api/v1")
app.include_router(models.router, prefix="/api/v1")


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for unhandled errors.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"[{request_id}] Unhandled exception: {exc}", exc_info=True)

    # Debug: Log request details
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"[{request_id}] Request method: {request.method}")
        logger.debug(f"[{request_id}] Request URL: {request.url}")
        logger.debug(f"[{request_id}] Request headers: {dict(request.headers)}")

    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL",
            "message": "Internal server error",
            "request_id": request_id,
        },
    )


@app.get("/")
async def root() -> dict[str, str | None]:
    """
    Root endpoint with API information.
    """
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "status": "running",
        "docs": "/docs" if settings.debug else None,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
