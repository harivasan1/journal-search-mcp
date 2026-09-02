"""
MCP tool implementations for citation lookup, related papers, and
citation export.

Backs the `get_citations`, `related_papers`, and `export_citation`
MCP tools.
"""

from typing import Any, Dict

from services import crossref, openalex, semanticscholar
from utils.citation_formatter import format_citation
from utils.exceptions import ValidationInputError


def _clean_doi(doi: str) -> str:
    return doi.strip().replace("https://doi.org/", "").replace("http://doi.org/", "")


def get_citations(doi: str, limit: int = 20) -> Dict[str, Any]:
    """
    Get citation count, citing papers, and referenced papers for a DOI.

    Args:
        doi: The DOI of the paper to look up.
        limit: Max number of citing/referenced papers to return.
    """
    if not doi or not doi.strip():
        raise ValidationInputError("`doi` must be a non-empty string.")

    doi = _clean_doi(doi)
    paper = semanticscholar.get_paper_by_doi(doi, fields="title,citationCount,referenceCount")
    citing = semanticscholar.get_citations(doi, limit=limit)
    references = semanticscholar.get_references(doi, limit=limit)

    return {
        "doi": doi,
        "title": paper.get("title"),
        "citation_count": paper.get("citationCount", 0),
        "reference_count": paper.get("referenceCount", 0),
        "citing_papers": [{"title": p.get("title"), "year": p.get("year")} for p in citing if p],
        "referenced_papers": [
            {"title": p.get("title"), "year": p.get("year")} for p in references if p
        ],
    }


def related_papers(doi: str, limit: int = 10) -> Dict[str, Any]:
    """
    Get papers related/similar to the given DOI.

    Args:
        doi: The DOI of the source paper.
        limit: Max number of related papers to return (default 10).
    """
    if not doi or not doi.strip():
        raise ValidationInputError("`doi` must be a non-empty string.")

    doi = _clean_doi(doi)
    recommendations = semanticscholar.get_recommendations(doi, limit=limit)

    return {
        "doi": doi,
        "related_count": len(recommendations),
        "related_papers": [
            {
                "title": p.get("title"),
                "year": p.get("year"),
                "doi": (p.get("externalIds") or {}).get("DOI"),
            }
            for p in recommendations
        ],
    }


def export_citation(doi: str, style: str = "apa") -> Dict[str, Any]:
    """
    Export a formatted citation for a DOI.

    Args:
        doi: The DOI of the paper to cite.
        style: One of "apa", "mla", "ieee", or "bibtex".
    """
    if not doi or not doi.strip():
        raise ValidationInputError("`doi` must be a non-empty string.")

    doi = _clean_doi(doi)
    try:
        message = crossref.get_work_by_doi(doi)
        fields = crossref.extract_citation_fields(message)
    except Exception:
        # Fall back to OpenAlex metadata if Crossref has no record for this DOI.
        work = openalex.get_work(doi)
        authors = [
            {"family": a.split()[-1], "given": " ".join(a.split()[:-1])}
            for a in work.get("authors", [])
            if a
        ]
        fields = {
            "title": work.get("title"),
            "authors": authors,
            "journal": work.get("journal"),
            "year": work.get("year"),
            "volume": None,
            "issue": None,
            "pages": None,
            "publisher": None,
            "doi": doi,
        }

    citation_text = format_citation(fields, style)
    return {"doi": doi, "style": style.upper(), "citation": citation_text}
