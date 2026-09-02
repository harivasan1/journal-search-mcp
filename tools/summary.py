"""
MCP tool implementation for AI-assisted paper summaries.

Backs the `summarize_paper` MCP tool. Uses Semantic Scholar's `tldr`
field (an AI-generated one-line summary produced by their SciTLDR
model) when available, and otherwise falls back to a simple
abstract-based extractive summary so the tool never returns empty.
"""

import re
from typing import Any, Dict

from services import openalex, semanticscholar
from utils.exceptions import ValidationInputError


def _clean_doi(doi: str) -> str:
    return doi.strip().replace("https://doi.org/", "").replace("http://doi.org/", "")


def _extractive_summary(abstract: str, max_sentences: int = 3) -> str:
    """Return the first `max_sentences` sentences of the abstract."""
    if not abstract:
        return "No abstract available to summarize."
    sentences = re.split(r"(?<=[.!?])\s+", abstract.strip())
    return " ".join(sentences[:max_sentences])


def summarize_paper(doi: str) -> Dict[str, Any]:
    """
    Generate a short summary, key findings, and practical applications
    for a paper.

    Args:
        doi: The DOI of the paper to summarize.

    Note:
        This is not a full-text LLM summary — it uses Semantic
        Scholar's AI-generated tldr where available, or an
        abstract-based extract otherwise. Always verify against the
        full paper for anything consequential.
    """
    if not doi or not doi.strip():
        raise ValidationInputError("`doi` must be a non-empty string.")

    doi = _clean_doi(doi)
    paper = semanticscholar.get_paper_by_doi(doi, fields="title,abstract,tldr,venue,year")

    abstract = paper.get("abstract")
    if not abstract:
        # OpenAlex reconstructs abstracts independently and often has one
        # even when Semantic Scholar doesn't.
        try:
            work = openalex.get_work(doi)
            abstract = work.get("abstract")
        except Exception:
            abstract = None

    tldr = (paper.get("tldr") or {}).get("text")
    summary = tldr or _extractive_summary(abstract)

    return {
        "doi": doi,
        "title": paper.get("title"),
        "summary": summary,
        "summary_source": "semantic_scholar_tldr" if tldr else "abstract_extract",
        "key_findings": _extractive_summary(abstract, max_sentences=2) if abstract else None,
        "research_contribution": summary,
        "practical_applications": (
            "This is an automatically generated summary and may be incomplete. "
            "Review the full paper for application-specific guidance."
        ),
    }
