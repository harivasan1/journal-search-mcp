"""Unit tests for tools/journal.py (search_journal)."""

from unittest.mock import patch

import pytest

from tools import journal
from utils.exceptions import NotFoundError, ValidationInputError


def test_search_journal_empty_name_raises():
    with pytest.raises(ValidationInputError):
        journal.search_journal("")


@patch("tools.journal.openalex.search_sources")
def test_search_journal_not_found_raises(mock_search):
    mock_search.return_value = []
    with pytest.raises(NotFoundError):
        journal.search_journal("Nonexistent Journal")


@patch("tools.journal.openalex.search_sources")
def test_search_journal_success(mock_search):
    mock_search.return_value = [
        {
            "name": "Nature",
            "publisher": "Springer Nature",
            "issn": "0028-0836",
            "homepage": "https://nature.com",
            "works_count": 500000,
            "openalex_id": "S123",
        }
    ]
    result = journal.search_journal("Nature")
    assert result["result_count"] == 1
    assert result["results"][0]["name"] == "Nature"
    assert result["results"][0]["issn"] == "0028-0836"
