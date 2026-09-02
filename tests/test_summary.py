"""Unit tests for tools/summary.py (summarize_paper)."""
from unittest.mock import patch

import pytest

from tools import summary
from utils.exceptions import ValidationInputError


def test_summarize_paper_empty_doi_raises():
    with pytest.raises(ValidationInputError):
        summary.summarize_paper("")


@patch("tools.summary.semanticscholar.get_paper_by_doi")
def test_summarize_paper_with_tldr(mock_get_paper):
    mock_get_paper.return_value = {
        "title": "Sample Paper",
        "abstract": "This is a long abstract with multiple sentences. It has more detail here. And even more.",
        "tldr": {"text": "Short AI summary."},
    }
    result = summary.summarize_paper("10.1000/xyz")
    assert result["summary"] == "Short AI summary."
    assert result["summary_source"] == "semantic_scholar_tldr"


@patch("tools.summary.openalex.get_work")
@patch("tools.summary.semanticscholar.get_paper_by_doi")
def test_summarize_paper_falls_back_to_abstract(mock_get_paper, mock_get_work):
    mock_get_paper.return_value = {"title": "Sample Paper", "abstract": None, "tldr": None}
    mock_get_work.return_value = {"abstract": "First sentence. Second sentence. Third sentence."}

    result = summary.summarize_paper("10.1000/xyz")
    assert result["summary_source"] == "abstract_extract"
    assert "First sentence." in result["summary"]
