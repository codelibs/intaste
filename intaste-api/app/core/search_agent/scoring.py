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
Scoring utilities for search result relevance.
"""

import re
from typing import Any


def calculate_relevance_score(query: str, title: str) -> float:
    """
    Calculate relevance score between search query and result title.

    Uses a combination of token-based similarity metrics:
    - Jaccard similarity: measures overlap relative to union of tokens
    - Token overlap ratio: measures how many query tokens appear in title

    Args:
        query: The search query string
        title: The result title string

    Returns:
        A score from 0.0 (no relevance) to 1.0 (high relevance)
    """
    # Normalize and tokenize
    query_tokens = _tokenize(query)
    title_tokens = _tokenize(title)

    if not query_tokens or not title_tokens:
        return 0.0

    # Calculate Jaccard similarity
    intersection = query_tokens & title_tokens
    union = query_tokens | title_tokens
    jaccard = len(intersection) / len(union) if union else 0.0

    # Calculate token overlap ratio (query coverage)
    overlap_ratio = len(intersection) / len(query_tokens) if query_tokens else 0.0

    # Calculate substring bonus (partial word matches)
    substring_score = _calculate_substring_score(query.lower(), title.lower())

    # Combined score with weighted average
    # - Jaccard (30%): Overall similarity
    # - Overlap ratio (50%): Query coverage in title
    # - Substring score (20%): Partial matches
    score = 0.3 * jaccard + 0.5 * overlap_ratio + 0.2 * substring_score

    return min(1.0, max(0.0, score))


def _tokenize(text: str) -> set[str]:
    """
    Tokenize text into normalized word tokens.

    Args:
        text: Input text

    Returns:
        Set of lowercase tokens (words)
    """
    # Convert to lowercase and split by non-alphanumeric characters
    tokens = re.findall(r"\w+", text.lower())
    # Filter out very short tokens (1-2 chars) and common stop words
    stop_words = {"a", "an", "the", "in", "on", "at", "to", "for", "of", "is", "are", "was"}
    return {t for t in tokens if len(t) > 2 and t not in stop_words}


def _calculate_substring_score(query: str, title: str) -> float:
    """
    Calculate score based on query substrings found in title.

    Args:
        query: Normalized query string (lowercase)
        title: Normalized title string (lowercase)

    Returns:
        Score from 0.0 to 1.0 based on substring matches
    """
    if not query or not title:
        return 0.0

    # Check if full query appears in title (highest score)
    if query in title:
        return 1.0

    # Check for partial matches (query words as substrings)
    query_words = query.split()
    if not query_words:
        return 0.0

    matches = sum(1 for word in query_words if word in title)
    return matches / len(query_words)


def score_search_results(
    query: str,
    hits: list[Any],
) -> list[Any]:
    """
    Score and sort search results by relevance to query.

    Updates each hit's 'score' field with the relevance score and sorts
    results in descending order (highest score first).

    Args:
        query: The search query string
        hits: List of SearchHit objects

    Returns:
        Sorted list of SearchHit objects with updated scores
    """
    # Calculate relevance scores
    for hit in hits:
        relevance = calculate_relevance_score(query, hit.title)
        # Store as relevance_score in meta for reference
        if hit.meta is None:
            hit.meta = {}
        hit.meta["relevance_score"] = relevance
        # Update the main score field
        hit.score = relevance

    # Sort by score descending (highest first)
    sorted_hits = sorted(hits, key=lambda h: h.score or 0.0, reverse=True)

    return sorted_hits


def has_low_relevance(hits: list[Any], threshold: float = 0.3) -> bool:
    """
    Check if all search results have low relevance scores.

    Args:
        hits: List of SearchHit objects with scores
        threshold: Maximum score to consider "low" (default: 0.3)

    Returns:
        True if all results have scores below threshold
    """
    if not hits:
        return True

    return all((hit.score or 0.0) < threshold for hit in hits)
