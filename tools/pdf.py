"""
MCP tool implementation for locating legal open-access PDFs.

Backs the `open_access_pdf` MCP tool. Only returns links surfaced by
OpenAlex / Semantic Scholar's own open-access indexes (e.g. Unpaywall
data) — no scraping or paywall bypassing is performed.
"""

from typing import Any

from services import openalex, semanticscholar
from utils.exceptions import APIRequestError, NotFoundError, ValidationInputError
from utils.logger import get_logger

logger = get_logger(__name__)


def _clean_doi(doi: str) -> str:
    return doi.strip().replace("https://doi.org/", "").replace("http://doi.org/", "")


def open_access_pdf(doi: str) -> dict[str, Any]:
    """
    Return a legal open-access PDF URL for the given DOI, if one exists.

    Checks OpenAlex's open-access index first, then falls back to
    Semantic Scholar's. If neither has a legal open-access copy, the
    tool clearly states that none was found rather than guessing.

    Args:
        doi: The DOI of the paper to check.
    """
    if not doi or not doi.strip():
        raise ValidationInputError("`doi` must be a non-empty string.")

    doi = _clean_doi(doi)

    pdf_url = None
    try:
        work = openalex.get_work(doi)
        pdf_url = work.get("open_access_pdf")
    except (APIRequestError, NotFoundError, AttributeError, TypeError, ValueError) as exc:
        # Log but do not fail here; we'll try Semantic Scholar next.
        logger.warning("OpenAlex lookup failed for %s: %s", doi, exc)

    if not pdf_url:
        try:
            paper = semanticscholar.get_paper_by_doi(doi, fields="openAccessPdf")
            pdf_url = (paper.get("openAccessPdf") or {}).get("url")
        except (APIRequestError, NotFoundError, AttributeError, TypeError, ValueError) as exc:
            logger.warning("Semantic Scholar lookup failed for %s: %s", doi, exc)

    if pdf_url:
        return {"doi": doi, "open_access_available": True, "pdf_url": pdf_url}

    return {
        "doi": doi,
        "open_access_available": False,
        "pdf_url": None,
        "message": "No legal open-access PDF was found for this paper.",
    }
