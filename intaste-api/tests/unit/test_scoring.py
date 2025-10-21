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
Unit tests for search result scoring.
"""

import pytest

from app.core.search_agent.scoring import (
    calculate_relevance_score,
    has_low_relevance,
    score_search_results,
)
from app.core.search_provider.base import SearchHit


class TestCalculateRelevanceScore:
    """Tests for calculate_relevance_score function."""

    def test_exact_match(self):
        """Test exact match between query and title."""
        score = calculate_relevance_score("python tutorial", "python tutorial")
        assert score > 0.8

    def test_partial_match(self):
        """Test partial match between query and title."""
        score = calculate_relevance_score("python tutorial", "python programming tutorial guide")
        assert 0.5 < score < 1.0

    def test_no_match(self):
        """Test no match between query and title."""
        score = calculate_relevance_score("python tutorial", "java enterprise development")
        assert score < 0.3

    def test_substring_match(self):
        """Test substring matching."""
        score = calculate_relevance_score(
            "database optimization", "advanced database optimization techniques"
        )
        assert score > 0.6

    def test_empty_inputs(self):
        """Test with empty inputs."""
        assert calculate_relevance_score("", "title") == 0.0
        assert calculate_relevance_score("query", "") == 0.0
        assert calculate_relevance_score("", "") == 0.0

    def test_case_insensitive(self):
        """Test case-insensitive matching."""
        score1 = calculate_relevance_score("Python Tutorial", "python tutorial")
        score2 = calculate_relevance_score("python tutorial", "PYTHON TUTORIAL")
        assert score1 > 0.8
        assert score2 > 0.8

    def test_stop_words_filtered(self):
        """Test that stop words are filtered."""
        # "the", "a", "of" should be filtered
        score = calculate_relevance_score(
            "the guide of python", "python guide for beginners"
        )
        assert score > 0.4

    def test_word_order_irrelevant(self):
        """Test that word order doesn't significantly affect score."""
        score1 = calculate_relevance_score("machine learning tutorial", "tutorial machine learning")
        score2 = calculate_relevance_score("machine learning tutorial", "machine learning tutorial")
        # Both should have high scores
        assert score1 > 0.6
        assert score2 > 0.6


class TestScoreSearchResults:
    """Tests for score_search_results function."""

    def test_scoring_and_sorting(self):
        """Test that results are scored and sorted correctly."""
        hits = [
            SearchHit(
                id="1",
                title="Java programming guide",
                url="https://example.com/1",
                snippet="About Java",
                score=0.9,
            ),
            SearchHit(
                id="2",
                title="Python tutorial for beginners",
                url="https://example.com/2",
                snippet="Learn Python",
                score=0.8,
            ),
            SearchHit(
                id="3",
                title="Advanced Python programming",
                url="https://example.com/3",
                snippet="Python advanced",
                score=0.7,
            ),
        ]

        scored_hits = score_search_results("python tutorial", hits)

        # Should be sorted by relevance score
        assert len(scored_hits) == 3
        # "Python tutorial" should be first
        assert scored_hits[0].id == "2"
        assert scored_hits[0].score is not None
        assert scored_hits[0].score > scored_hits[1].score
        # Check that meta contains relevance_score
        assert scored_hits[0].meta is not None
        assert "relevance_score" in scored_hits[0].meta

    def test_empty_hits(self):
        """Test with empty hits list."""
        scored_hits = score_search_results("test query", [])
        assert scored_hits == []

    def test_score_updates(self):
        """Test that original scores are replaced with relevance scores."""
        hits = [
            SearchHit(
                id="1",
                title="completely unrelated topic",
                url="https://example.com/1",
                score=0.99,  # High original score
            ),
            SearchHit(
                id="2",
                title="python programming tutorial guide",
                url="https://example.com/2",
                score=0.1,  # Low original score
            ),
        ]

        scored_hits = score_search_results("python tutorial", hits)

        # Relevance score should override original score
        # The relevant result should be first despite lower original score
        assert scored_hits[0].id == "2"


class TestHasLowRelevance:
    """Tests for has_low_relevance function."""

    def test_all_low_scores(self):
        """Test when all scores are below threshold."""
        hits = [
            SearchHit(id="1", title="test", url="https://example.com/1", score=0.1),
            SearchHit(id="2", title="test", url="https://example.com/2", score=0.2),
            SearchHit(id="3", title="test", url="https://example.com/3", score=0.25),
        ]
        assert has_low_relevance(hits, threshold=0.3) is True

    def test_some_high_scores(self):
        """Test when some scores are above threshold."""
        hits = [
            SearchHit(id="1", title="test", url="https://example.com/1", score=0.1),
            SearchHit(id="2", title="test", url="https://example.com/2", score=0.5),
            SearchHit(id="3", title="test", url="https://example.com/3", score=0.25),
        ]
        assert has_low_relevance(hits, threshold=0.3) is False

    def test_empty_hits(self):
        """Test with empty hits list."""
        assert has_low_relevance([], threshold=0.3) is True

    def test_custom_threshold(self):
        """Test with custom threshold."""
        hits = [
            SearchHit(id="1", title="test", url="https://example.com/1", score=0.4),
        ]
        assert has_low_relevance(hits, threshold=0.3) is False
        assert has_low_relevance(hits, threshold=0.5) is True

    def test_none_scores(self):
        """Test with None scores."""
        hits = [
            SearchHit(id="1", title="test", url="https://example.com/1", score=None),
        ]
        # None scores should be treated as 0.0
        assert has_low_relevance(hits, threshold=0.3) is True
