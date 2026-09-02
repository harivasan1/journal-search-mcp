"""Unit tests for tools/search.py (search_papers, paper_details)."""

from unittest.mock import patch

import pytest

from tools import search
from utils.exceptions import ValidationInputError


def test_search_papers_empty_keyword_raises():
    with pytest.raises(ValidationInputError):
        search.search_papers(keyword="")


@patch("tools.search.openalex.search_works")
def test_search_papers_returns_results(mock_search):
    mock_search.return_value = [
        {
            "title": "Deep Learning in Healthcare",
            "authors": ["A. Smith"],
            "journal": "Nature Medicine",
            "year": 2022,
            "doi": "10.1000/xyz",
            "abstract": "Sample abstract",
            "citation_count": 42,
            "openalex_id": "W123",
            "keywords": ["deep learning", "healthcare"],
        }
    ]
    result = search.search_papers(keyword="deep learning")
    assert result["result_count"] == 1
    assert result["results"][0]["title"] == "Deep Learning in Healthcare"
    assert "deep learning" in result["keyword_suggestions"]


@patch("tools.search.openalex.search_works")
def test_search_papers_sort_by_citations_maps_correctly(mock_search):
    mock_search.return_value = []
    search.search_papers(keyword="ai", sort_by="citations")
    _, kwargs = mock_search.call_args
    assert kwargs["sort"] == "cited_by_count:desc"


@patch("tools.search.openalex.get_work")
def test_paper_details_returns_full_metadata(mock_get_work):
    mock_get_work.return_value = {
        "title": "Sample Paper",
        "authors": ["B. Jones"],
        "journal": "Science",
        "year": 2021,
        "doi": "10.1000/abc",
        "abstract": "Abstract text",
        "citation_count": 10,
        "openalex_id": "W456",
        "keywords": ["ai"],
        "referenced_works": [],
        "related_works": [],
        "open_access_pdf": None,
        "url": "https://openalex.org/W456",
    }
    result = search.paper_details("10.1000/abc")
    assert result["title"] == "Sample Paper"
    assert result["doi"] == "10.1000/abc"


def test_paper_details_empty_identifier_raises():
    with pytest.raises(ValidationInputError):
        search.paper_details("")
