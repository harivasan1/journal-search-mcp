"""Unit tests for tools/pdf.py (open_access_pdf)."""
from unittest.mock import patch

import pytest

from tools import pdf
from utils.exceptions import ValidationInputError


def test_open_access_pdf_empty_doi_raises():
    with pytest.raises(ValidationInputError):
        pdf.open_access_pdf("")


@patch("tools.pdf.openalex.get_work")
def test_open_access_pdf_found_via_openalex(mock_get_work):
    mock_get_work.return_value = {"open_access_pdf": "https://example.com/paper.pdf"}
    result = pdf.open_access_pdf("10.1000/xyz")
    assert result["open_access_available"] is True
    assert result["pdf_url"] == "https://example.com/paper.pdf"


@patch("tools.pdf.semanticscholar.get_paper_by_doi")
@patch("tools.pdf.openalex.get_work")
def test_open_access_pdf_falls_back_to_semantic_scholar(mock_get_work, mock_get_paper):
    mock_get_work.return_value = {"open_access_pdf": None}
    mock_get_paper.return_value = {"openAccessPdf": {"url": "https://example.com/s2.pdf"}}
    result = pdf.open_access_pdf("10.1000/xyz")
    assert result["open_access_available"] is True
    assert result["pdf_url"] == "https://example.com/s2.pdf"


@patch("tools.pdf.semanticscholar.get_paper_by_doi")
@patch("tools.pdf.openalex.get_work")
def test_open_access_pdf_not_found(mock_get_work, mock_get_paper):
    mock_get_work.return_value = {"open_access_pdf": None}
    mock_get_paper.return_value = {"openAccessPdf": None}
    result = pdf.open_access_pdf("10.1000/xyz")
    assert result["open_access_available"] is False
    assert result["pdf_url"] is None
