"""Prompt Registry for centralized prompt management.

This module provides:
- Centralized prompt registration and retrieval
- Version management
- A/B testing support (future)
- Environment-based overrides (future)
"""

import logging
from typing import Any

from .models import PromptParams, PromptTemplate

logger = logging.getLogger(__name__)


class PromptRegistry:
    """Centralized registry for managing prompt templates.

    This class provides:
    - Thread-safe prompt registration and retrieval
    - Version-based prompt management
    - Validation of prompt IDs and versions
    - Extensibility for A/B testing and dynamic switching

    Example:
        >>> registry = PromptRegistry()
        >>> template = PromptTemplate[IntentParams](...)
        >>> registry.register(template)
        >>> retrieved = registry.get("intent", IntentParams)
    """

    def __init__(self) -> None:
        """Initialize the prompt registry."""
        # Storage: {prompt_id: {version: PromptTemplate}}
        self._prompts: dict[str, dict[str, PromptTemplate[Any]]] = {}
        # Default versions: {prompt_id: version}
        self._default_versions: dict[str, str] = {}

    def register(
        self,
        template: PromptTemplate[Any],
        set_as_default: bool = True,
    ) -> None:
        """Register a prompt template.

        Args:
            template: The PromptTemplate instance to register
            set_as_default: If True, set this version as the default for this prompt_id

        Raises:
            ValueError: If a template with the same ID and version already exists
        """
        prompt_id = template.prompt_id
        version = template.version

        # Initialize prompt_id entry if needed
        if prompt_id not in self._prompts:
            self._prompts[prompt_id] = {}

        # Check for duplicate
        if version in self._prompts[prompt_id]:
            existing = self._prompts[prompt_id][version]
            if existing != template:
                raise ValueError(
                    f"Prompt '{prompt_id}' version '{version}' already registered "
                    "with different content"
                )
            logger.debug(f"Prompt '{prompt_id}' version '{version}' already registered (identical)")
            return

        # Register the template
        self._prompts[prompt_id][version] = template

        # Set as default if requested or if it's the first version
        if set_as_default or prompt_id not in self._default_versions:
            self._default_versions[prompt_id] = version

        logger.info(
            f"Registered prompt '{prompt_id}' version '{version}' "
            f"(default: {set_as_default or prompt_id not in self._default_versions})"
        )

    def get(
        self,
        prompt_id: str,
        params_type: type[PromptParams],
        version: str | None = None,
    ) -> PromptTemplate[Any]:
        """Retrieve a prompt template by ID and optional version.

        Args:
            prompt_id: The unique identifier of the prompt
            params_type: The expected parameter type (for type safety, not enforced at runtime)
            version: Specific version to retrieve, or None for default version

        Returns:
            The requested PromptTemplate instance

        Raises:
            KeyError: If the prompt_id or version is not found
        """
        if prompt_id not in self._prompts:
            raise KeyError(
                f"Prompt '{prompt_id}' not found. " f"Available: {list(self._prompts.keys())}"
            )

        # Determine version to use
        if version is None:
            if prompt_id not in self._default_versions:
                raise KeyError(f"No default version set for prompt '{prompt_id}'")
            version = self._default_versions[prompt_id]

        if version not in self._prompts[prompt_id]:
            available_versions = list(self._prompts[prompt_id].keys())
            raise KeyError(
                f"Prompt '{prompt_id}' version '{version}' not found. "
                f"Available versions: {available_versions}"
            )

        template = self._prompts[prompt_id][version]
        logger.debug(f"Retrieved prompt '{prompt_id}' version '{version}'")
        return template

    def list_prompts(self) -> dict[str, list[str]]:
        """List all registered prompts and their versions.

        Returns:
            Dictionary mapping prompt_id to list of versions
        """
        return {prompt_id: list(versions.keys()) for prompt_id, versions in self._prompts.items()}

    def get_default_version(self, prompt_id: str) -> str | None:
        """Get the default version for a prompt.

        Args:
            prompt_id: The prompt identifier

        Returns:
            Default version string, or None if not set
        """
        return self._default_versions.get(prompt_id)

    def set_default_version(self, prompt_id: str, version: str) -> None:
        """Set the default version for a prompt.

        Args:
            prompt_id: The prompt identifier
            version: The version to set as default

        Raises:
            KeyError: If the prompt_id or version doesn't exist
        """
        if prompt_id not in self._prompts:
            raise KeyError(f"Prompt '{prompt_id}' not found")

        if version not in self._prompts[prompt_id]:
            raise KeyError(f"Prompt '{prompt_id}' version '{version}' not found")

        old_version = self._default_versions.get(prompt_id)
        self._default_versions[prompt_id] = version
        logger.info(f"Changed default version for '{prompt_id}': " f"{old_version} -> {version}")

    def clear(self) -> None:
        """Clear all registered prompts (useful for testing)."""
        self._prompts.clear()
        self._default_versions.clear()
        logger.debug("Cleared all prompts from registry")


# Global singleton instance
_global_registry: PromptRegistry | None = None


def get_registry() -> PromptRegistry:
    """Get the global prompt registry instance.

    Returns:
        The global PromptRegistry singleton
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = PromptRegistry()
    return _global_registry


def reset_registry() -> None:
    """Reset the global registry (useful for testing)."""
    global _global_registry
    _global_registry = None
