"""
MCP tool implementations for paper search and detailed retrieval.

Backs the `search_papers` and `paper_details` MCP tools.
"""

from typing import Any

from services import openalex
from utils.exceptions import ValidationInputError
from utils.logger import get_logger

logger = get_logger(__name__)

# Human-friendly sort options mapped to OpenAlex sort expressions.
_SORT_MAP = {
    "citations": "cited_by_count:desc",
    "latest": "publication_date:desc",
    "relevance": None,
}


def search_papers(
    keyword: str,
    year: int | None = None,
    author: str | None = None,
    journal: str | None = None,
    sort_by: str | None = None,
    page: int = 1,
    per_page: int = 10,
) -> dict[str, Any]:
    """
    Search for academic papers by keyword, with optional year, author,
    and journal filters, sorting, and pagination.

    Args:
        keyword: Search term (required).
        year: Restrict results to a specific publication year.
        author: Restrict results to a specific author name.
        journal: Restrict results to a specific journal/source name.
        sort_by: "relevance" (default), "citations", or "latest".
        page: 1-indexed page number.
        per_page: Number of results per page (max 50).

    Returns:
        A dict with the query, pagination info, matching papers, and
        keyword suggestions derived from the results.
    """
    if not keyword or not keyword.strip():
        raise ValidationInputError("`keyword` must be a non-empty string.")

    sort_param = _SORT_MAP.get((sort_by or "relevance").lower())

    papers = openalex.search_works(
        keyword=keyword,
        year=year,
        author=author,
        journal=journal,
        sort=sort_param,
        page=page,
        per_page=per_page,
    )

    return {
        "query": keyword,
        "page": page,
        "per_page": per_page,
        "result_count": len(papers),
        "results": papers,
        "keyword_suggestions": _keyword_suggestions(papers),
    }


def _keyword_suggestions(papers: list[dict[str, Any]], limit: int = 8) -> list[str]:
    """Derive simple keyword suggestions from the concepts of the top results."""
    seen: list[str] = []
    for paper in papers:
        for kw in paper.get("keywords", []) or []:
            if kw and kw not in seen:
                seen.append(kw)
        if len(seen) >= limit:
            break
    return seen[:limit]


def paper_details(identifier: str) -> dict[str, Any]:
    """
    Retrieve full metadata for a single paper by DOI or OpenAlex ID,
    including abstract, keywords, references, and related works.

    Args:
        identifier: A DOI (e.g. "10.1038/s41586-021-03819-2") or an
            OpenAlex work ID (e.g. "W2741809807").
    """
    if not identifier or not identifier.strip():
        raise ValidationInputError("`identifier` (DOI or OpenAlex ID) must be provided.")

    work = openalex.get_work(identifier.strip())
    return {
        "title": work.get("title"),
        "authors": work.get("authors"),
        "journal": work.get("journal"),
        "year": work.get("year"),
        "doi": work.get("doi"),
        "abstract": work.get("abstract"),
        "citation_count": work.get("citation_count"),
        "openalex_id": work.get("openalex_id"),
        "keywords": work.get("keywords"),
        "references": (work.get("referenced_works") or [])[:20],
        "related_works": (work.get("related_works") or [])[:10],
        "open_access_pdf": work.get("open_access_pdf"),
        "url": work.get("url"),
    }
