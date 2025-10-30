"""Unit tests for prompt models and registry."""

import pytest
from pydantic import ValidationError

from app.core.llm.prompts import (
    ComposeParams,
    IntentParams,
    MergeResultsParams,
    PromptTemplate,
    RelevanceParams,
    RetryIntentNoResultsParams,
    RetryIntentParams,
    get_registry,
    register_all_prompts,
    reset_registry,
)


class TestPromptParams:
    """Test Pydantic parameter models."""

    def test_intent_params_valid(self):
        """Test IntentParams with valid data."""
        params = IntentParams(
            query="test query",
            language="en",
            query_history_text="history",
            filters_json="{}",
        )
        assert params.query == "test query"
        assert params.language == "en"

    def test_intent_params_defaults(self):
        """Test IntentParams default values."""
        params = IntentParams(query="test", language="en")
        assert params.query_history_text == ""
        assert params.filters_json == "{}"

    def test_intent_params_extra_field_rejected(self):
        """Test that extra fields are rejected."""
        with pytest.raises(ValidationError):
            IntentParams(
                query="test",
                language="en",
                extra_field="not allowed",  # type: ignore
            )

    def test_compose_params_valid(self):
        """Test ComposeParams with valid data."""
        params = ComposeParams(
            query="test",
            normalized_query="normalized",
            language="en",
            citations_text="citations",
        )
        assert params.query == "test"
        assert params.citations_text == "citations"

    def test_relevance_params_valid(self):
        """Test RelevanceParams with valid data."""
        params = RelevanceParams(
            query="test",
            normalized_query="normalized",
            title="Test Title",
            snippet="Test snippet",
        )
        assert params.title == "Test Title"
        assert params.snippet == "Test snippet"

    def test_retry_intent_params_valid(self):
        """Test RetryIntentParams with valid data."""
        params = RetryIntentParams(
            query="test",
            previous_normalized_query="prev",
            language="en",
            low_score_results="results",
        )
        assert params.previous_normalized_query == "prev"
        assert params.low_score_results == "results"

    def test_retry_intent_no_results_params_valid(self):
        """Test RetryIntentNoResultsParams with valid data."""
        params = RetryIntentNoResultsParams(
            query="test",
            previous_normalized_query="prev",
            language="en",
        )
        assert params.previous_normalized_query == "prev"

    def test_merge_results_params_valid(self):
        """Test MergeResultsParams with valid data."""
        params = MergeResultsParams(
            query="test",
            agent_results_text="results",
        )
        assert params.agent_results_text == "results"


class TestPromptTemplate:
    """Test PromptTemplate class."""

    def test_template_creation(self):
        """Test creating a PromptTemplate."""
        template = PromptTemplate[IntentParams](
            prompt_id="test",
            version="1.0",
            system_prompt="System",
            user_template="Query: {query}, Lang: {language}",
            description="Test template",
        )
        assert template.prompt_id == "test"
        assert template.version == "1.0"

    def test_template_format(self):
        """Test formatting a template with parameters."""
        template = PromptTemplate[IntentParams](
            prompt_id="test",
            version="1.0",
            system_prompt="System",
            user_template="Query: {query}, Lang: {language}",
        )
        params = IntentParams(query="hello", language="en")
        result = template.format(params)
        assert "Query: hello" in result
        assert "Lang: en" in result

    def test_template_format_missing_placeholder(self):
        """Test that formatting fails with missing placeholders."""
        template = PromptTemplate[IntentParams](
            prompt_id="test",
            version="1.0",
            system_prompt="System",
            user_template="Query: {query}, Missing: {missing_field}",
        )
        params = IntentParams(query="hello", language="en")
        with pytest.raises(KeyError):
            template.format(params)

    def test_template_immutable(self):
        """Test that PromptTemplate is frozen/immutable."""
        template = PromptTemplate[IntentParams](
            prompt_id="test",
            version="1.0",
            system_prompt="System",
            user_template="Template",
        )
        with pytest.raises(ValidationError):
            template.prompt_id = "modified"  # type: ignore


class TestPromptRegistry:
    """Test PromptRegistry functionality."""

    def setup_method(self):
        """Reset registry before each test."""
        reset_registry()

    def test_register_and_get_prompt(self):
        """Test registering and retrieving a prompt."""
        registry = get_registry()
        template = PromptTemplate[IntentParams](
            prompt_id="test",
            version="1.0",
            system_prompt="System",
            user_template="Template",
        )
        registry.register(template)

        retrieved = registry.get("test", IntentParams)
        assert retrieved.prompt_id == "test"
        assert retrieved.version == "1.0"

    def test_get_nonexistent_prompt(self):
        """Test that getting nonexistent prompt raises KeyError."""
        registry = get_registry()
        with pytest.raises(KeyError, match="Prompt 'nonexistent' not found"):
            registry.get("nonexistent", IntentParams)

    def test_register_duplicate_identical(self):
        """Test that registering identical prompt twice is allowed."""
        registry = get_registry()
        template = PromptTemplate[IntentParams](
            prompt_id="test",
            version="1.0",
            system_prompt="System",
            user_template="Template",
        )
        registry.register(template)
        registry.register(template)  # Should not raise

    def test_register_duplicate_different_content(self):
        """Test that registering same id/version with different content raises."""
        registry = get_registry()
        template1 = PromptTemplate[IntentParams](
            prompt_id="test",
            version="1.0",
            system_prompt="System1",
            user_template="Template1",
        )
        template2 = PromptTemplate[IntentParams](
            prompt_id="test",
            version="1.0",
            system_prompt="System2",  # Different content
            user_template="Template2",
        )
        registry.register(template1)
        with pytest.raises(ValueError, match="already registered"):
            registry.register(template2)

    def test_register_multiple_versions(self):
        """Test registering multiple versions of same prompt."""
        registry = get_registry()
        v1 = PromptTemplate[IntentParams](
            prompt_id="test",
            version="1.0",
            system_prompt="System",
            user_template="V1",
        )
        v2 = PromptTemplate[IntentParams](
            prompt_id="test",
            version="2.0",
            system_prompt="System",
            user_template="V2",
        )
        registry.register(v1)
        registry.register(v2, set_as_default=True)

        # Default should be v2
        default = registry.get("test", IntentParams)
        assert default.version == "2.0"

        # Can still get v1 explicitly
        specific = registry.get("test", IntentParams, version="1.0")
        assert specific.version == "1.0"

    def test_list_prompts(self):
        """Test listing all prompts."""
        registry = get_registry()
        t1 = PromptTemplate[IntentParams](
            prompt_id="prompt1",
            version="1.0",
            system_prompt="S",
            user_template="T",
        )
        t2 = PromptTemplate[IntentParams](
            prompt_id="prompt2",
            version="1.0",
            system_prompt="S",
            user_template="T",
        )
        registry.register(t1)
        registry.register(t2)

        prompts = registry.list_prompts()
        assert "prompt1" in prompts
        assert "prompt2" in prompts
        assert prompts["prompt1"] == ["1.0"]

    def test_set_default_version(self):
        """Test changing default version."""
        registry = get_registry()
        v1 = PromptTemplate[IntentParams](
            prompt_id="test",
            version="1.0",
            system_prompt="S",
            user_template="V1",
        )
        v2 = PromptTemplate[IntentParams](
            prompt_id="test",
            version="2.0",
            system_prompt="S",
            user_template="V2",
        )
        registry.register(v1)
        registry.register(v2, set_as_default=False)

        # Default is v1
        assert registry.get_default_version("test") == "1.0"

        # Change to v2
        registry.set_default_version("test", "2.0")
        assert registry.get_default_version("test") == "2.0"

        # Retrieve without version should get v2
        default = registry.get("test", IntentParams)
        assert default.version == "2.0"


class TestPromptDefinitions:
    """Test that all standard prompts are registered correctly."""

    def setup_method(self):
        """Reset and register all prompts."""
        reset_registry()
        register_all_prompts()

    def test_all_prompts_registered(self):
        """Test that all expected prompts are registered."""
        registry = get_registry()
        expected_prompts = [
            "intent",
            "compose",
            "relevance",
            "retry_intent",
            "retry_intent_no_results",
            "merge_results",
        ]
        prompts = registry.list_prompts()
        for expected in expected_prompts:
            assert expected in prompts, f"Prompt '{expected}' not registered"

    def test_intent_prompt_format(self):
        """Test that intent prompt can be formatted."""
        registry = get_registry()
        template = registry.get("intent", IntentParams)
        params = IntentParams(
            query="test query",
            language="en",
            query_history_text="history",
            filters_json="{}",
        )
        user_prompt = template.format(params)
        assert "test query" in user_prompt
        assert "en" in user_prompt

    def test_compose_prompt_format(self):
        """Test that compose prompt can be formatted."""
        registry = get_registry()
        template = registry.get("compose", ComposeParams)
        params = ComposeParams(
            query="test",
            normalized_query="normalized",
            language="en",
            citations_text="citations",
        )
        user_prompt = template.format(params)
        assert "test" in user_prompt
        assert "citations" in user_prompt

    def test_relevance_prompt_format(self):
        """Test that relevance prompt can be formatted."""
        registry = get_registry()
        template = registry.get("relevance", RelevanceParams)
        params = RelevanceParams(
            query="test",
            normalized_query="normalized",
            title="Title",
            snippet="Snippet",
        )
        user_prompt = template.format(params)
        assert "Title" in user_prompt
        assert "Snippet" in user_prompt

    def test_retry_intent_prompt_format(self):
        """Test that retry intent prompt can be formatted."""
        registry = get_registry()
        template = registry.get("retry_intent", RetryIntentParams)
        params = RetryIntentParams(
            query="test",
            previous_normalized_query="prev",
            language="en",
            low_score_results="results",
        )
        user_prompt = template.format(params)
        assert "prev" in user_prompt
        assert "results" in user_prompt

    def test_retry_intent_no_results_prompt_format(self):
        """Test that retry intent (no results) prompt can be formatted."""
        registry = get_registry()
        template = registry.get("retry_intent_no_results", RetryIntentNoResultsParams)
        params = RetryIntentNoResultsParams(
            query="test",
            previous_normalized_query="prev",
            language="en",
        )
        user_prompt = template.format(params)
        assert "prev" in user_prompt
        assert "0 results" in user_prompt or "no results" in user_prompt.lower()

    def test_merge_results_prompt_format(self):
        """Test that merge results prompt can be formatted."""
        registry = get_registry()
        template = registry.get("merge_results", MergeResultsParams)
        params = MergeResultsParams(
            query="test",
            agent_results_text="results",
        )
        user_prompt = template.format(params)
        assert "test" in user_prompt
        assert "results" in user_prompt
