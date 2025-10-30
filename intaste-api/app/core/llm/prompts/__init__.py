"""Prompt management package with type-safe templates and registry.

This package provides:
- Pydantic-based prompt parameter models
- Generic PromptTemplate class for type-safe formatting
- Centralized PromptRegistry for prompt management
- Pre-defined prompt templates for all LLM operations

Usage:
    from app.core.llm.prompts import get_registry, IntentParams, register_all_prompts

    # Initialize registry (do this at app startup)
    register_all_prompts()

    # Retrieve and use prompts
    registry = get_registry()
    template = registry.get("intent", IntentParams)
    params = IntentParams(query="test", language="en")
    user_prompt = template.format(params)
"""

from .definitions import register_all_prompts
from .models import (
    ComposeParams,
    IntentParams,
    MergeResultsParams,
    PromptParams,
    PromptTemplate,
    RelevanceParams,
    RetryIntentNoResultsParams,
    RetryIntentParams,
)
from .registry import PromptRegistry, get_registry, reset_registry

__all__ = [
    # Core classes
    "PromptTemplate",
    "PromptRegistry",
    # Parameter models
    "PromptParams",
    "IntentParams",
    "ComposeParams",
    "RelevanceParams",
    "RetryIntentParams",
    "RetryIntentNoResultsParams",
    "MergeResultsParams",
    # Registry functions
    "get_registry",
    "reset_registry",
    "register_all_prompts",
]
