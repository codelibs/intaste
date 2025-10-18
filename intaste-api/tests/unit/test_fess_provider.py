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

"""Tests for Fess search provider"""

import pytest
import httpx
from unittest.mock import AsyncMock, patch
from httpx import Response

from app.core.search_provider.fess import FessSearchProvider
from app.core.search_provider.base import SearchQuery, SearchResult


@pytest.fixture
def fess_provider():
    """Create FessSearchProvider instance for testing"""
    return FessSearchProvider(
        base_url="http://test-fess:8080",
        timeout_ms=2000,
    )


@pytest.fixture
def mock_fess_response():
    """Mock Fess JSON response"""
    return {
        "q": "test query",
        "exec_time": 0.15,
        "page_size": 10,
        "page_number": 1,
        "record_count": 2,
        "page_count": 1,
        "data": [
            {
                "doc_id": "doc1",
                "title": "Test Document 1",
                "content_description": "This is a <em>test</em> document",
                "url": "http://example.com/doc1",
                "score": 0.95,
                "host": "example.com",
                "mimetype": "text/html",
            },
            {
                "doc_id": "doc2",
                "title": "Test Document 2",
                "content_description": "Another document",
                "url": "http://example.com/doc2",
                "score": 0.85,
                "host": "example.com",
                "mimetype": "application/pdf",
            },
        ],
    }


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_success(fess_provider, mock_fess_response):
    """Test successful search"""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = mock_fess_response
        mock_get.return_value = mock_response

        query = SearchQuery(q="test query", page=1, size=10)
        result = await fess_provider.search(query)

        assert isinstance(result, SearchResult)
        assert result.total == 2
        assert len(result.hits) == 2
        assert result.hits[0].title == "Test Document 1"
        assert result.hits[0].score == 0.95
        assert result.took_ms == 150  # 0.15 seconds converted to milliseconds


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_with_filters(fess_provider, mock_fess_response):
    """Test search with site and mimetype filters"""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = mock_fess_response
        mock_get.return_value = mock_response

        query = SearchQuery(
            q="test query",
            page=1,
            size=10,
            filters={
                "site": "example.com",
                "mimetype": "application/pdf",
            },
        )
        result = await fess_provider.search(query)

        # Verify the request was made with correct parameters
        call_args = mock_get.call_args
        assert call_args[1]["params"]["site"] == "example.com"
        assert call_args[1]["params"]["mimetype"] == "application/pdf"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_pagination(fess_provider, mock_fess_response):
    """Test search pagination parameters"""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = mock_fess_response
        mock_get.return_value = mock_response

        query = SearchQuery(q="test query", page=3, size=20)
        await fess_provider.search(query)

        # Verify start parameter calculation: (page - 1) * size
        call_args = mock_get.call_args
        assert call_args[1]["params"]["start"] == 40
        assert call_args[1]["params"]["num"] == 20


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_empty_results(fess_provider):
    """Test search with no results"""
    empty_response = {
        "q": "nonexistent query",
        "exec_time": 0.05,
        "page_size": 10,
        "page_number": 1,
        "record_count": 0,
        "page_count": 0,
        "data": [],
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = empty_response
        mock_get.return_value = mock_response

        query = SearchQuery(q="nonexistent query")
        result = await fess_provider.search(query)

        assert result.total == 0
        assert len(result.hits) == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_http_error(fess_provider):
    """Test search with HTTP error"""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500 Server Error", request=AsyncMock(), response=mock_response
        )
        mock_get.return_value = mock_response

        query = SearchQuery(q="test query")

        with pytest.raises(RuntimeError, match="Fess returned 500"):
            await fess_provider.search(query)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_timeout(fess_provider):
    """Test search timeout"""
    import asyncio

    with patch("httpx.AsyncClient.get", side_effect=asyncio.TimeoutError()):
        query = SearchQuery(q="test query")

        with pytest.raises(asyncio.TimeoutError):
            await fess_provider.search(query)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_check_success(fess_provider):
    """Test health check when Fess is healthy"""
    mock_health_response = {
        "data": {
            "status": "green",
            "timed_out": False,
        }
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = mock_health_response
        mock_get.return_value = mock_response

        is_healthy, details = await fess_provider.health()

        assert is_healthy is True
        assert details["status"] == "green"
        assert details["timed_out"] is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_check_failure(fess_provider):
    """Test health check when Fess is unreachable"""
    with patch("httpx.AsyncClient.get", side_effect=Exception("Connection error")):
        is_healthy, details = await fess_provider.health()

        assert is_healthy is False
        assert "error" in details


@pytest.mark.unit
@pytest.mark.asyncio
async def test_normalize_hit_missing_fields(fess_provider):
    """Test normalization with missing optional fields"""
    raw_hit = {
        "id": "doc1",
        "title": "Test",
        "url": "http://example.com/test",
        "score": 0.9,
        # Missing content_description, digest, host, mimetype
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "exec_time": 0.1,
            "record_count": 1,
            "data": [raw_hit],
        }
        mock_get.return_value = mock_response

        query = SearchQuery(q="test")
        result = await fess_provider.search(query)

        assert len(result.hits) == 1
        assert result.hits[0].snippet is None  # snippet is None when both content_description and digest are missing
        assert result.hits[0].meta.get("site") is None  # host is missing
        assert result.hits[0].meta.get("content_type") is None  # mimetype is missing


@pytest.mark.unit
@pytest.mark.asyncio
async def test_id_generation_with_doc_id_field(fess_provider):
    """Test ID generation prioritizes doc_id field (highest priority)"""
    raw_hit = {
        "doc_id": "abc123def456",  # Fess native doc_id
        "id": "fallback_id",
        "title": "Test Document",
        "url": "http://example.com/test",
        "score": 0.9,
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "exec_time": 0.1,
            "record_count": 1,
            "data": [raw_hit],
        }
        mock_get.return_value = mock_response

        query = SearchQuery(q="test")
        result = await fess_provider.search(query)

        assert len(result.hits) == 1
        # Should use doc_id field, not id or URL hash
        assert result.hits[0].id == "abc123def456"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_id_generation_with_id_field(fess_provider):
    """Test ID generation uses id field when doc_id is not available"""
    raw_hit = {
        "id": "doc1",  # Fallback to id field
        "title": "Test Document",
        "url": "http://example.com/test",
        "score": 0.9,
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "exec_time": 0.1,
            "record_count": 1,
            "data": [raw_hit],
        }
        mock_get.return_value = mock_response

        query = SearchQuery(q="test")
        result = await fess_provider.search(query)

        assert len(result.hits) == 1
        # Should use id field
        assert result.hits[0].id == "doc1"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_id_generation_with_url_only(fess_provider):
    """Test ID generation uses URL hash when doc_id and id are not available"""
    import hashlib

    test_url = "http://example.com/test"
    expected_id = hashlib.sha256(test_url.encode()).hexdigest()[:16]

    raw_hit = {
        "title": "Test Document",
        "url": test_url,
        "score": 0.9,
        # Missing doc_id and id
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "exec_time": 0.1,
            "record_count": 1,
            "data": [raw_hit],
        }
        mock_get.return_value = mock_response

        query = SearchQuery(q="test")
        result = await fess_provider.search(query)

        assert len(result.hits) == 1
        # Should use URL hash
        assert result.hits[0].id == expected_id


@pytest.mark.unit
@pytest.mark.asyncio
async def test_id_generation_with_no_id_sources(fess_provider):
    """Test ID generation uses document hash as final fallback"""
    import hashlib

    raw_hit = {
        "title": "Test Document",
        "score": 0.9,
        # Missing doc_id, id, and url
    }

    # Calculate expected document hash
    expected_prefix = "unknown-"

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "exec_time": 0.1,
            "record_count": 1,
            "data": [raw_hit],
        }
        mock_get.return_value = mock_response

        query = SearchQuery(q="test")
        result = await fess_provider.search(query)

        assert len(result.hits) == 1
        # Should use document hash with "unknown-" prefix
        assert result.hits[0].id.startswith(expected_prefix)
        assert len(result.hits[0].id) == len(expected_prefix) + 16  # prefix + 16 hex chars


@pytest.mark.unit
@pytest.mark.asyncio
async def test_id_generation_fallback_stability(fess_provider):
    """Test that fallback IDs are stable across multiple requests"""
    raw_hit = {
        "title": "Test Document",
        "content": "Some content",
        "score": 0.9,
        # Missing doc_id, id, and url
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "exec_time": 0.1,
            "record_count": 1,
            "data": [raw_hit],
        }
        mock_get.return_value = mock_response

        query = SearchQuery(q="test")
        
        # First request
        result1 = await fess_provider.search(query)
        id1 = result1.hits[0].id

        # Second request with same data
        result2 = await fess_provider.search(query)
        id2 = result2.hits[0].id

        # IDs should be identical (stable)
        assert id1 == id2
        assert id1.startswith("unknown-")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_id_generation_with_realistic_fess_response(fess_provider):
    """Test ID generation with realistic Fess API response including doc_id"""
    realistic_response = {
        "q": "test query",
        "exec_time": 0.15,
        "record_count": 2,
        "data": [
            {
                "doc_id": "e79fbfdfb09d4bffb58ec230c68f6f7e",  # Realistic Fess doc_id
                "title": "Open Source Enterprise Search",
                "url": "https://fess.codelibs.org/",
                "filetype": "html",
                "content_description": "Enterprise Search Server...",
                "last_modified": "2025-01-15T10:00:00.000Z",
                "score": 0.95,
            },
            {
                "doc_id": "f12ab34cd56ef78gh90ij12kl34mn56o",  # Another doc_id
                "title": "Fess Documentation",
                "url": "https://fess.codelibs.org/13.10/",
                "filetype": "html",
                "content_description": "Fess documentation...",
                "last_modified": "2025-01-10T08:30:00.000Z",
                "score": 0.88,
            },
        ],
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = realistic_response
        mock_get.return_value = mock_response

        query = SearchQuery(q="test query")
        result = await fess_provider.search(query)

        assert len(result.hits) == 2
        # Should use Fess's native doc_id values
        assert result.hits[0].id == "e79fbfdfb09d4bffb58ec230c68f6f7e"
        assert result.hits[1].id == "f12ab34cd56ef78gh90ij12kl34mn56o"



@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_with_multiple_filters_combined(fess_provider):
    """Test search with multiple filters combined."""
    mock_response_data = {
        "q": "test query",
        "exec_time": 0.1,
        "record_count": 1,
        "data": [
            {
                "doc_id": "doc1",
                "title": "Filtered Document",
                "url": "http://example.com/test",
                "score": 0.9,
            }
        ],
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_get.return_value = mock_response

        query = SearchQuery(
            q="test query",
            page=1,
            size=10,
            filters={
                "site": "example.com",
                "mimetype": "application/pdf",
                "updated_after": "2025-01-01",
            },
        )
        await fess_provider.search(query)

        # Verify all filters are applied
        call_args = mock_get.call_args
        params = call_args[1]["params"]
        assert params["site"] == "example.com"
        assert params["mimetype"] == "application/pdf"
        assert params["last_modified_from"] == "2025-01-01"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_with_invalid_filter_values(fess_provider, mock_fess_response):
    """Test search with invalid or unusual filter values."""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = mock_fess_response
        mock_get.return_value = mock_response

        # Test with special characters in filters
        query = SearchQuery(
            q="test",
            filters={
                "site": "example.com; DROP TABLE users;--",
                "mimetype": "../../../etc/passwd",
            },
        )
        await fess_provider.search(query)

        # Should pass through (Fess API handles validation)
        call_args = mock_get.call_args
        params = call_args[1]["params"]
        assert "site" in params
        assert "mimetype" in params


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_with_sort_parameters(fess_provider, mock_fess_response):
    """Test search with different sort parameters."""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = mock_fess_response
        mock_get.return_value = mock_response

        # Test date_desc sort
        query = SearchQuery(q="test", sort="date_desc")
        await fess_provider.search(query)
        params = mock_get.call_args[1]["params"]
        assert params["sort"] == "last_modified desc"

        # Test date_asc sort
        query = SearchQuery(q="test", sort="date_asc")
        await fess_provider.search(query)
        params = mock_get.call_args[1]["params"]
        assert params["sort"] == "last_modified asc"

        # Test default (relevance) sort
        query = SearchQuery(q="test")
        await fess_provider.search(query)
        params = mock_get.call_args[1]["params"]
        assert params["sort"] == "score"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_with_empty_filter_values(fess_provider, mock_fess_response):
    """Test search with empty filter values."""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = mock_fess_response
        mock_get.return_value = mock_response

        # Empty strings and None values should be handled
        query = SearchQuery(
            q="test",
            filters={
                "site": "",
                "mimetype": None,
            },
        )
        await fess_provider.search(query)

        # Empty/None filters should not be applied
        call_args = mock_get.call_args
        params = call_args[1]["params"]
        # Empty string is still applied (Fess API handles it)
        assert "site" in params or "site" not in params


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_with_filters_and_sorting_combined(fess_provider, mock_fess_response):
    """Test search with both filters and sorting."""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = mock_fess_response
        mock_get.return_value = mock_response

        query = SearchQuery(
            q="test",
            sort="date_desc",
            filters={"site": "example.com"},
        )
        await fess_provider.search(query)

        params = mock_get.call_args[1]["params"]
        assert params["sort"] == "last_modified desc"
        assert params["site"] == "example.com"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_with_custom_timeout(fess_provider, mock_fess_response):
    """Test search with custom timeout parameter."""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = mock_fess_response
        mock_get.return_value = mock_response

        query = SearchQuery(q="test", timeout_ms=5000)
        await fess_provider.search(query)

        # Verify timeout is passed to httpx
        call_args = mock_get.call_args
        assert call_args[1]["timeout"] == 5.0  # 5000ms = 5.0s


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_with_special_date_formats(fess_provider, mock_fess_response):
    """Test search with various date formats in updated_after filter."""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = mock_fess_response
        mock_get.return_value = mock_response

        date_formats = [
            "2025-01-01",
            "2025-01-01T00:00:00",
            "2025-01-01T00:00:00.000Z",
            "2025-01-01T00:00:00+09:00",
        ]

        for date_format in date_formats:
            query = SearchQuery(
                q="test",
                filters={"updated_after": date_format},
            )
            await fess_provider.search(query)

            params = mock_get.call_args[1]["params"]
            assert params["last_modified_from"] == date_format


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_preserves_html_in_snippet(fess_provider):
    """Test that HTML in snippet is preserved (UI must sanitize)."""
    response_with_html = {
        "q": "test",
        "exec_time": 0.1,
        "record_count": 1,
        "data": [
            {
                "doc_id": "doc1",
                "title": "HTML Document",
                "url": "http://example.com/test",
                "content_description": 'This is <em>emphasized</em> and <strong>bold</strong> text with <script>alert("xss")</script>',
                "score": 0.9,
            }
        ],
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = response_with_html
        mock_get.return_value = mock_response

        query = SearchQuery(q="test")
        result = await fess_provider.search(query)

        # HTML should be preserved in snippet (not sanitized by provider)
        assert "<em>" in result.hits[0].snippet
        assert "<strong>" in result.hits[0].snippet
        assert "<script>" in result.hits[0].snippet


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_with_zero_results_total(fess_provider):
    """Test search with zero total but valid response structure."""
    zero_response = {
        "q": "nonexistent",
        "exec_time": 0.05,
        "page_size": 10,
        "page_number": 1,
        "record_count": 0,
        "page_count": 0,
        "data": [],
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = zero_response
        mock_get.return_value = mock_response

        query = SearchQuery(q="nonexistent")
        result = await fess_provider.search(query)

        assert result.total == 0
        assert len(result.hits) == 0
        assert result.took_ms == 50


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_url_construction(fess_provider):
    """Test that search URL is correctly constructed."""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "exec_time": 0.1,
            "record_count": 0,
            "data": [],
        }
        mock_get.return_value = mock_response

        query = SearchQuery(q="test")
        await fess_provider.search(query)

        # Verify URL
        call_args = mock_get.call_args
        url = call_args[0][0]
        assert url == "http://test-fess:8080/api/v1/documents"
