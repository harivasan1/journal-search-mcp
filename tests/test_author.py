"""Unit tests for tools/author.py (search_author)."""

from unittest.mock import patch

import pytest

from tools.author import search_author
from utils.exceptions import NotFoundError, ValidationInputError


def test_search_author_empty_name_raises():
    with pytest.raises(ValidationInputError):
        search_author("")


@patch("tools.author.openalex.search_authors")
def test_search_author_not_found_raises(mock_search):
    mock_search.return_value = []
    with pytest.raises(NotFoundError):
        search_author("Nonexistent Person")


@patch("tools.author.openalex.search_authors")
def test_search_author_success(mock_search):
    mock_search.return_value = [
        {
            "name": "Jane Doe",
            "affiliation": "MIT",
            "h_index": 20,
            "citation_count": 500,
            "works_count": 30,
            "openalex_id": "A1",
        }
    ]
    result = search_author("Jane Doe")
    assert result["result_count"] == 1
    assert result["results"][0]["name"] == "Jane Doe"
    assert result["results"][0]["h_index"] == 20
