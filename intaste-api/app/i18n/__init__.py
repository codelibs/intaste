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
Internationalization (i18n) module for intaste-api.

Provides translation functionality using GNU gettext and Babel.
"""

import gettext
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Cache for loaded translations
_translations: dict[str, gettext.GNUTranslations] = {}

# Path to locales directory
_LOCALE_DIR = Path(__file__).parent.parent.parent / "locales"

# Supported languages
SUPPORTED_LANGUAGES = ["en", "ja", "zh_CN", "zh_TW", "de", "es", "fr"]


def setup_i18n(language: str = "en") -> gettext.GNUTranslations:
    """
    Load translation catalog for the given language.

    Args:
        language: Language code (e.g., "en", "ja", "zh_CN")

    Returns:
        GNUTranslations object for the language

    Note:
        If the language is not available, falls back to NullTranslations
        which returns the original messages unchanged.
    """
    global _translations

    if language in _translations:
        return _translations[language]

    try:
        # Normalize language code (zh-CN -> zh_CN)
        normalized_lang = language.replace("-", "_")

        logger.debug(f"Loading translations for language: {normalized_lang}")
        logger.debug(f"Locale directory: {_LOCALE_DIR}")

        translation = gettext.translation(
            domain="messages",
            localedir=str(_LOCALE_DIR),
            languages=[normalized_lang],
            fallback=False,  # Will raise if not found
        )

        _translations[language] = translation
        logger.debug(f"Successfully loaded translations for {normalized_lang}")
        return translation

    except FileNotFoundError:
        logger.warning(
            f"Translation file not found for language '{language}', "
            f"falling back to untranslated messages"
        )
        # Create a NullTranslations instance that returns original messages
        null_translation = gettext.NullTranslations()
        _translations[language] = null_translation  # type: ignore
        return null_translation  # type: ignore


def _(message: str, language: str = "en") -> str:
    """
    Get translated message for the given language.

    Args:
        message: Message to translate (in English)
        language: Target language code (default: "en")

    Returns:
        Translated message, or original message if translation not available

    Example:
        >>> _("Processing query...", language="ja")
        'クエリを処理中...'

        >>> _("Unknown message", language="ja")
        'Unknown message'  # Falls back to original
    """
    # Normalize language code
    normalized_lang = language.replace("-", "_")

    # Load translation if not cached
    if normalized_lang not in _translations:
        setup_i18n(normalized_lang)

    translation = _translations.get(normalized_lang)
    if translation:
        return translation.gettext(message)

    # Fallback to original message
    return message


__all__ = ["_", "setup_i18n", "SUPPORTED_LANGUAGES"]
