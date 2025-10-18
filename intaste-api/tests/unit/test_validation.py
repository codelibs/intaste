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
Unit tests for schema validation and input sanitization.
"""

import pytest
from pydantic import ValidationError

from app.schemas.assist import (
    AssistQueryRequest,
    Citation,
    Answer,
    Session,
    Timings,
    Notice,
    FeedbackRequest,
)
from uuid import uuid4


@pytest.mark.unit
class TestAssistQueryRequestValidation:
    """Test cases for AssistQueryRequest schema validation."""

    def test_valid_query(self):
        """Test validation with valid query."""
        request = AssistQueryRequest(query="What is the security policy?")
        assert request.query == "What is the security policy?"

    def test_empty_query_fails(self):
        """Test that empty query fails validation (min_length=1)."""
        with pytest.raises(ValidationError) as exc_info:
            AssistQueryRequest(query="")

        errors = exc_info.value.errors()
        assert any(
            error["type"] == "string_too_short" for error in errors
        ), "Should fail with string_too_short"

    def test_query_max_length(self):
        """Test query maximum length (max_length=4096)."""
        # Valid: exactly 4096 characters
        long_query = "a" * 4096
        request = AssistQueryRequest(query=long_query)
        assert len(request.query) == 4096

        # Invalid: 4097 characters
        with pytest.raises(ValidationError) as exc_info:
            AssistQueryRequest(query="a" * 4097)

        errors = exc_info.value.errors()
        assert any(error["type"] == "string_too_long" for error in errors)

    def test_query_with_special_characters(self):
        """Test query with special characters (emoji, HTML, etc)."""
        special_queries = [
            "What is the 🔒 security policy?",  # Emoji
            "How to use <script>alert('xss')</script>?",  # HTML/XSS
            "SELECT * FROM users WHERE name='admin'--",  # SQL-like
            "Query with\nnewlines\nand\ttabs",  # Whitespace
            "Query with 日本語",  # Unicode
            "Query with 한글",  # Korean
            "Query with العربية",  # Arabic
        ]

        for query in special_queries:
            request = AssistQueryRequest(query=query)
            assert request.query == query

    def test_session_id_validation(self):
        """Test session_id validation (UUID v4 format expected in docs)."""
        # Valid: proper UUID format
        valid_uuid = str(uuid4())
        request = AssistQueryRequest(query="test", session_id=valid_uuid)
        assert request.session_id == valid_uuid

        # Valid: None is allowed
        request = AssistQueryRequest(query="test", session_id=None)
        assert request.session_id is None

        # Note: The schema uses str | None, not UUID type,
        # so any string is technically valid at schema level
        # But we should document that UUID v4 is expected
        request = AssistQueryRequest(query="test", session_id="not-a-uuid")
        assert request.session_id == "not-a-uuid"

    def test_query_history_validation(self):
        """Test query_history validation (max_length=10)."""
        # Valid: exactly 10 items
        history = [f"query {i}" for i in range(10)]
        request = AssistQueryRequest(query="test", query_history=history)
        assert len(request.query_history) == 10

        # Invalid: 11 items
        with pytest.raises(ValidationError) as exc_info:
            AssistQueryRequest(query="test", query_history=[f"query {i}" for i in range(11)])

        errors = exc_info.value.errors()
        assert any("too_long" in error["type"] for error in errors)

    def test_query_history_empty_list(self):
        """Test query_history with empty list."""
        request = AssistQueryRequest(query="test", query_history=[])
        assert request.query_history == []

    def test_options_field(self):
        """Test options field accepts arbitrary dict."""
        options = {
            "max_results": 10,
            "language": "ja",
            "filters": {"site": "example.com"},
            "timeout_ms": 5000,
            "custom_field": "custom_value",
        }
        request = AssistQueryRequest(query="test", options=options)
        assert request.options == options


@pytest.mark.unit
class TestCitationValidation:
    """Test cases for Citation schema validation."""

    def test_valid_citation(self):
        """Test validation with valid citation."""
        citation = Citation(
            id=1,
            title="Test Document",
            url="https://example.com/doc",
            snippet="Test snippet",
            score=0.95,
        )
        assert citation.id == 1
        assert citation.title == "Test Document"

    def test_citation_id_minimum(self):
        """Test citation id minimum value (ge=1)."""
        # Valid: id=1
        citation = Citation(id=1, title="Test", url="https://example.com")
        assert citation.id == 1

        # Invalid: id=0
        with pytest.raises(ValidationError) as exc_info:
            Citation(id=0, title="Test", url="https://example.com")

        errors = exc_info.value.errors()
        assert any("greater_than_equal" in error["type"] for error in errors)

        # Invalid: negative id
        with pytest.raises(ValidationError) as exc_info:
            Citation(id=-1, title="Test", url="https://example.com")

    def test_citation_optional_fields(self):
        """Test citation with optional fields."""
        # snippet, score, meta are optional
        citation = Citation(id=1, title="Test", url="https://example.com")
        assert citation.snippet is None
        assert citation.score is None
        assert citation.meta is None

    def test_citation_with_html_snippet(self):
        """Test citation with HTML snippet (UI must sanitize)."""
        html_snippet = '<em>Important</em> information <script>alert("xss")</script>'
        citation = Citation(
            id=1, title="Test", url="https://example.com", snippet=html_snippet
        )
        assert citation.snippet == html_snippet

    def test_citation_meta_arbitrary_data(self):
        """Test citation meta accepts arbitrary dict."""
        meta = {
            "site": "example.com",
            "content_type": "application/pdf",
            "nested": {"key": "value"},
            "list": [1, 2, 3],
        }
        citation = Citation(
            id=1, title="Test", url="https://example.com", meta=meta
        )
        assert citation.meta == meta


@pytest.mark.unit
class TestAnswerValidation:
    """Test cases for Answer schema validation."""

    def test_valid_answer(self):
        """Test validation with valid answer."""
        answer = Answer(
            text="This is the answer.",
            suggested_questions=["Question 1?", "Question 2?"],
        )
        assert answer.text == "This is the answer."
        assert len(answer.suggested_questions) == 2

    def test_answer_text_max_length(self):
        """Test answer text maximum length (max_length=300)."""
        # Valid: exactly 300 characters
        text = "a" * 300
        answer = Answer(text=text)
        assert len(answer.text) == 300

        # Invalid: 301 characters
        with pytest.raises(ValidationError) as exc_info:
            Answer(text="a" * 301)

        errors = exc_info.value.errors()
        assert any(error["type"] == "string_too_long" for error in errors)

    def test_suggested_questions_max_items(self):
        """Test suggested_questions maximum items (max_length=3)."""
        # Valid: exactly 3 questions
        answer = Answer(text="Test", suggested_questions=["Q1?", "Q2?", "Q3?"])
        assert len(answer.suggested_questions) == 3

        # Invalid: 4 questions
        with pytest.raises(ValidationError) as exc_info:
            Answer(text="Test", suggested_questions=["Q1?", "Q2?", "Q3?", "Q4?"])

        errors = exc_info.value.errors()
        assert any("too_long" in error["type"] for error in errors)

    def test_suggested_questions_default(self):
        """Test suggested_questions default value."""
        answer = Answer(text="Test")
        assert answer.suggested_questions == []


@pytest.mark.unit
class TestSessionValidation:
    """Test cases for Session schema validation."""

    def test_valid_session(self):
        """Test validation with valid session."""
        session = Session(id=str(uuid4()), turn=1)
        assert session.turn == 1

    def test_session_turn_minimum(self):
        """Test session turn minimum value (ge=1)."""
        # Valid: turn=1
        session = Session(id="test-id", turn=1)
        assert session.turn == 1

        # Invalid: turn=0
        with pytest.raises(ValidationError) as exc_info:
            Session(id="test-id", turn=0)

        errors = exc_info.value.errors()
        assert any("greater_than_equal" in error["type"] for error in errors)


@pytest.mark.unit
class TestTimingsValidation:
    """Test cases for Timings schema validation."""

    def test_valid_timings(self):
        """Test validation with valid timings."""
        timings = Timings(llm_ms=100, search_ms=200, total_ms=300)
        assert timings.llm_ms == 100
        assert timings.search_ms == 200
        assert timings.total_ms == 300

    def test_timings_non_negative(self):
        """Test all timing fields must be non-negative (ge=0)."""
        # Valid: zero values
        timings = Timings(llm_ms=0, search_ms=0, total_ms=0)
        assert timings.llm_ms == 0

        # Invalid: negative llm_ms
        with pytest.raises(ValidationError) as exc_info:
            Timings(llm_ms=-1, search_ms=0, total_ms=0)

        errors = exc_info.value.errors()
        assert any("greater_than_equal" in error["type"] for error in errors)


@pytest.mark.unit
class TestNoticeValidation:
    """Test cases for Notice schema validation."""

    def test_notice_default_values(self):
        """Test Notice default values."""
        notice = Notice()
        assert notice.fallback is False
        assert notice.reason is None

    def test_notice_with_fallback(self):
        """Test Notice with fallback=True."""
        notice = Notice(fallback=True, reason="LLM_TIMEOUT")
        assert notice.fallback is True
        assert notice.reason == "LLM_TIMEOUT"

    def test_notice_valid_reasons(self):
        """Test Notice with documented reason values."""
        valid_reasons = ["LLM_TIMEOUT", "BAD_LLM_OUTPUT", "LLM_UNAVAILABLE"]

        for reason in valid_reasons:
            notice = Notice(fallback=True, reason=reason)
            assert notice.reason == reason


@pytest.mark.unit
class TestFeedbackRequestValidation:
    """Test cases for FeedbackRequest schema validation."""

    def test_valid_feedback(self):
        """Test validation with valid feedback."""
        feedback = FeedbackRequest(
            session_id=uuid4(),
            turn=1,
            rating="up",
        )
        assert feedback.rating == "up"

    def test_feedback_rating_literal(self):
        """Test feedback rating accepts only 'up' or 'down'."""
        # Valid: up
        feedback = FeedbackRequest(session_id=uuid4(), turn=1, rating="up")
        assert feedback.rating == "up"

        # Valid: down
        feedback = FeedbackRequest(session_id=uuid4(), turn=1, rating="down")
        assert feedback.rating == "down"

        # Invalid: other value
        with pytest.raises(ValidationError) as exc_info:
            FeedbackRequest(session_id=uuid4(), turn=1, rating="neutral")

        errors = exc_info.value.errors()
        assert any("literal_error" in error["type"] for error in errors)

    def test_feedback_comment_max_length(self):
        """Test feedback comment maximum length (max_length=500)."""
        # Valid: exactly 500 characters
        comment = "a" * 500
        feedback = FeedbackRequest(
            session_id=uuid4(), turn=1, rating="up", comment=comment
        )
        assert len(feedback.comment) == 500

        # Invalid: 501 characters
        with pytest.raises(ValidationError) as exc_info:
            FeedbackRequest(
                session_id=uuid4(), turn=1, rating="up", comment="a" * 501
            )

        errors = exc_info.value.errors()
        assert any(error["type"] == "string_too_long" for error in errors)

    def test_feedback_turn_minimum(self):
        """Test feedback turn minimum value (ge=1)."""
        # Valid: turn=1
        feedback = FeedbackRequest(session_id=uuid4(), turn=1, rating="up")
        assert feedback.turn == 1

        # Invalid: turn=0
        with pytest.raises(ValidationError) as exc_info:
            FeedbackRequest(session_id=uuid4(), turn=0, rating="up")

        errors = exc_info.value.errors()
        assert any("greater_than_equal" in error["type"] for error in errors)
