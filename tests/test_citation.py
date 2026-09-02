"""Unit tests for tools/citation.py (get_citations, related_papers, export_citation)."""
from unittest.mock import patch

import pytest

from services import semanticscholar
from tools import citation
from utils.exceptions import ValidationInputError


def test_get_citations_empty_doi_raises():
    with pytest.raises(ValidationInputError):
        citation.get_citations("")


@patch("tools.citation.semanticscholar.get_references")
@patch("tools.citation.semanticscholar.get_citations")
@patch("tools.citation.semanticscholar.get_paper_by_doi")
def test_get_citations_success(mock_paper, mock_citing, mock_refs):
    mock_paper.return_value = {"title": "Sample", "citationCount": 5, "referenceCount": 3}
    mock_citing.return_value = [{"title": "Citing Paper", "year": 2023}]
    mock_refs.return_value = [{"title": "Reference Paper", "year": 2019}]

    result = citation.get_citations("10.1000/xyz")
    assert result["citation_count"] == 5
    assert result["reference_count"] == 3
    assert result["citing_papers"][0]["title"] == "Citing Paper"
    assert result["referenced_papers"][0]["title"] == "Reference Paper"


def test_related_papers_empty_doi_raises():
    with pytest.raises(ValidationInputError):
        citation.related_papers("")


@patch("tools.citation.semanticscholar.get_recommendations")
def test_related_papers_success(mock_recs):
    mock_recs.return_value = [
        {"title": "Related Paper", "year": 2020, "externalIds": {"DOI": "10.1000/abc"}}
    ]
    result = citation.related_papers("10.1000/xyz")
    assert result["related_count"] == 1
    assert result["related_papers"][0]["doi"] == "10.1000/abc"


@patch("services.semanticscholar.get_json")
def test_semantic_scholar_handles_null_api_response(mock_get_json):
    mock_get_json.return_value = None

    assert semanticscholar.get_citations("10.1000/xyz") == []
    assert semanticscholar.get_references("10.1000/xyz") == []


def test_export_citation_empty_doi_raises():
    with pytest.raises(ValidationInputError):
        citation.export_citation("")


@patch("tools.citation.crossref.get_work_by_doi")
def test_export_citation_apa(mock_crossref):
    mock_crossref.return_value = {
        "title": ["Sample Title"],
        "author": [{"given": "Jane", "family": "Doe"}],
        "container-title": ["Journal of Testing"],
        "published": {"date-parts": [[2022]]},
        "volume": "10",
        "issue": "2",
        "page": "1-10",
        "publisher": "Test Publisher",
        "DOI": "10.1000/xyz",
    }
    result = citation.export_citation("10.1000/xyz", style="apa")
    assert result["style"] == "APA"
    assert "Doe" in result["citation"]
    assert "2022" in result["citation"]


@patch("tools.citation.crossref.get_work_by_doi")
def test_export_citation_bibtex(mock_crossref):
    mock_crossref.return_value = {
        "title": ["Sample Title"],
        "author": [{"given": "Jane", "family": "Doe"}],
        "container-title": ["Journal of Testing"],
        "published": {"date-parts": [[2022]]},
        "volume": "10",
        "issue": "2",
        "page": "1-10",
        "publisher": "Test Publisher",
        "DOI": "10.1000/xyz",
    }
    result = citation.export_citation("10.1000/xyz", style="bibtex")
    assert result["citation"].startswith("@article{Doe2022,")
