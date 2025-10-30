"""Pydantic models for prompt templates and parameters.

This module provides type-safe prompt management with:
- Strongly-typed parameter models for each prompt type
- Generic PromptTemplate class with built-in formatting
- Automatic parameter validation via Pydantic
"""

from pydantic import BaseModel, Field


# Base class for all prompt parameters
class PromptParams(BaseModel):
    """Base class for prompt template parameters."""

    class Config:
        """Pydantic config."""

        extra = "forbid"  # Prevent extra parameters


# Intent extraction parameters
class IntentParams(PromptParams):
    """Parameters for intent extraction prompt."""

    query: str = Field(..., description="User's natural language query")
    language: str = Field(..., description="Target language code (e.g., 'en', 'ja')")
    query_history_text: str = Field(
        default="", description="Formatted query history or empty string"
    )
    filters_json: str = Field(default="{}", description="JSON string of filter configuration")


# Answer composition parameters
class ComposeParams(PromptParams):
    """Parameters for answer composition prompt."""

    query: str = Field(..., description="Original user query")
    normalized_query: str = Field(..., description="Normalized search query")
    language: str = Field(..., description="Target language code")
    citations_text: str = Field(..., description="Formatted citations from search results")


# Relevance evaluation parameters
class RelevanceParams(PromptParams):
    """Parameters for relevance evaluation prompt."""

    query: str = Field(..., description="Original user query")
    normalized_query: str = Field(..., description="Normalized search query")
    title: str = Field(..., description="Search result title")
    snippet: str = Field(..., description="Search result snippet/excerpt")


# Retry intent extraction parameters (with low-score results)
class RetryIntentParams(PromptParams):
    """Parameters for retry intent extraction with low-score results."""

    query: str = Field(..., description="Original user query")
    previous_normalized_query: str = Field(..., description="Previous search query that failed")
    language: str = Field(..., description="Target language code")
    low_score_results: str = Field(
        ..., description="Formatted low-score search results for analysis"
    )


# Retry intent extraction parameters (no results)
class RetryIntentNoResultsParams(PromptParams):
    """Parameters for retry intent extraction when no results found."""

    query: str = Field(..., description="Original user query")
    previous_normalized_query: str = Field(..., description="Previous search query that failed")
    language: str = Field(..., description="Target language code")


# Multi-agent result merging parameters
class MergeResultsParams(PromptParams):
    """Parameters for multi-agent result merging prompt."""

    query: str = Field(..., description="Original user query")
    agent_results_text: str = Field(..., description="Formatted results from multiple agents")


class PromptTemplate[P: PromptParams](BaseModel):
    """Generic prompt template with type-safe parameter formatting.

    This class encapsulates:
    - Prompt identification (id, version)
    - System and user templates
    - Type-safe parameter formatting
    - Metadata for documentation and debugging

    Type Parameters:
        P: The PromptParams subclass for this template

    Example:
        >>> params = IntentParams(query="test", language="en")
        >>> template = PromptTemplate[IntentParams](
        ...     prompt_id="intent",
        ...     version="1.0",
        ...     system_prompt="You are a helpful assistant.",
        ...     user_template="Query: {query}, Language: {language}",
        ... )
        >>> user_prompt = template.format(params)
    """

    prompt_id: str = Field(..., description="Unique identifier for this prompt")
    version: str = Field(default="1.0", description="Prompt version for tracking changes")
    system_prompt: str = Field(..., description="System-level instructions (static)")
    user_template: str = Field(..., description="User prompt template with placeholders")
    description: str = Field(default="", description="Human-readable description")
    metadata: dict[str, str] = Field(
        default_factory=dict, description="Additional metadata (tags, author, etc.)"
    )

    class Config:
        """Pydantic config."""

        frozen = True  # Make templates immutable

    def format(self, params: P) -> str:
        """Format the user template with validated parameters.

        Args:
            params: Validated parameter instance

        Returns:
            Formatted user prompt string

        Raises:
            KeyError: If template contains placeholders not in params
            ValueError: If parameter validation fails
        """
        # Pydantic already validated params, now format template
        return self.user_template.format(**params.model_dump())

    def __hash__(self) -> int:
        """Make PromptTemplate hashable for use in sets/dicts."""
        return hash((self.prompt_id, self.version))
