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
Tests for i18n module.
"""

from app.i18n import _, SUPPORTED_LANGUAGES


def test_supported_languages():
    """Test that all expected languages are supported."""
    assert "en" in SUPPORTED_LANGUAGES
    assert "ja" in SUPPORTED_LANGUAGES
    assert "zh_CN" in SUPPORTED_LANGUAGES
    assert "zh_TW" in SUPPORTED_LANGUAGES
    assert "de" in SUPPORTED_LANGUAGES
    assert "es" in SUPPORTED_LANGUAGES
    assert "fr" in SUPPORTED_LANGUAGES


def test_translation_japanese():
    """Test Japanese translation."""
    message = "Results are displayed. Please review the sources for details."
    translated = _(message, language="ja")
    assert translated == "検索結果が表示されています。詳細は各ソースをご確認ください。"


def test_translation_english():
    """Test English translation (should be same as original)."""
    message = "Results are displayed. Please review the sources for details."
    translated = _(message, language="en")
    assert translated == message


def test_translation_chinese_simplified():
    """Test Chinese (Simplified) translation."""
    message = "Results are displayed. Please review the sources for details."
    translated = _(message, language="zh_CN")
    assert translated == "搜索结果已显示。请查看各来源以获取详细信息。"


def test_translation_chinese_simplified_with_hyphen():
    """Test Chinese (Simplified) translation with hyphen in language code."""
    message = "Results are displayed. Please review the sources for details."
    translated = _(message, language="zh-CN")  # Hyphen instead of underscore
    assert translated == "搜索结果已显示。请查看各来源以获取详细信息。"


def test_translation_fallback():
    """Test fallback to original message when translation not found."""
    message = "This message does not exist in translations"
    translated = _(message, language="ja")
    assert translated == message  # Should return original


def test_translation_unsupported_language():
    """Test fallback to original for unsupported language."""
    message = "Processing query..."
    translated = _(message, language="ko")  # Korean not supported
    assert translated == message  # Should return original


def test_translation_default_language():
    """Test that default language is English."""
    message = "Processing query..."
    translated = _(message)  # No language specified
    assert translated == message  # Should use English (same as original)
