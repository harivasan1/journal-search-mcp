"""
Client for the Semantic Scholar Graph API
(https://api.semanticscholar.org/graph/v1).

Semantic Scholar provides citation graphs, references, paper
recommendations, and an AI-generated one-line "tldr" summary for
many papers. An API key is optional and only used to raise rate
limits; the public endpoints work without one.
"""

from typing import Any

from config import SEMANTIC_SCHOLAR_API_KEY, SEMANTIC_SCHOLAR_BASE_URL
from utils.cache import cache
from utils.exceptions import APIRequestError, NotFoundError
from utils.http_client import get_json
from utils.logger import get_logger

logger = get_logger(__name__)
SERVICE_NAME = "semantic_scholar"

DEFAULT_FIELDS = (
    "title,abstract,year,venue,citationCount,referenceCount,tldr,openAccessPdf,externalIds,authors"
)


def _headers() -> dict[str, str]:
    headers = {}
    if SEMANTIC_SCHOLAR_API_KEY:
        headers["x-api-key"] = SEMANTIC_SCHOLAR_API_KEY
    return headers


def get_paper_by_doi(doi: str, fields: str = DEFAULT_FIELDS) -> dict[str, Any]:
    """Fetch a paper's Semantic Scholar record by DOI."""
    cache_key = ("s2_paper", doi, fields)
    cached = cache.get(*cache_key)
    if cached is not None:
        return cached

    url = f"{SEMANTIC_SCHOLAR_BASE_URL}/paper/DOI:{doi}"
    try:
        data = get_json(url, params={"fields": fields}, headers=_headers(), service=SERVICE_NAME)
    except Exception as exc:
        raise NotFoundError(f"No Semantic Scholar record found for DOI: {doi}") from exc

    cache.set(*cache_key, data)
    return data


def get_citations(doi: str, limit: int = 20) -> list[dict[str, Any]]:
    """Fetch papers that cite the given DOI."""
    cache_key = ("s2_citations", doi, str(limit))
    cached = cache.get(*cache_key)
    if cached is not None:
        return cached

    url = f"{SEMANTIC_SCHOLAR_BASE_URL}/paper/DOI:{doi}/citations"
    params = {"fields": "title,year,authors,externalIds", "limit": limit}
    data = get_json(url, params=params, headers=_headers(), service=SERVICE_NAME)
    items = data.get("data", []) if isinstance(data, dict) else []
    results = [item.get("citingPaper", {}) for item in items if isinstance(item, dict)]
    cache.set(*cache_key, results)
    return results


def get_references(doi: str, limit: int = 20) -> list[dict[str, Any]]:
    """Fetch papers referenced by the given DOI."""
    cache_key = ("s2_references", doi, str(limit))
    cached = cache.get(*cache_key)
    if cached is not None:
        return cached

    url = f"{SEMANTIC_SCHOLAR_BASE_URL}/paper/DOI:{doi}/references"
    params = {"fields": "title,year,authors,externalIds", "limit": limit}
    data = get_json(url, params=params, headers=_headers(), service=SERVICE_NAME)
    items = data.get("data", []) if isinstance(data, dict) else []
    results = [item.get("citedPaper", {}) for item in items if isinstance(item, dict)]
    cache.set(*cache_key, results)
    return results


def get_recommendations(doi: str, limit: int = 10) -> list[dict[str, Any]]:
    """Fetch related/recommended papers for a given DOI."""
    cache_key = ("s2_recommend", doi, str(limit))
    cached = cache.get(*cache_key)
    if cached is not None:
        return cached

    paper = get_paper_by_doi(doi, fields="paperId")
    paper_id = paper.get("paperId")
    if not paper_id:
        return []

    url = f"https://api.semanticscholar.org/recommendations/v1/papers/forpaper/{paper_id}"
    params = {"fields": "title,year,authors,externalIds", "limit": limit}
    try:
        data = get_json(url, params=params, headers=_headers(), service=SERVICE_NAME)
    except APIRequestError as exc:
        logger.warning("Recommendations unavailable for %s: %s", doi, exc)
        return []

    results = data.get("recommendedPapers", [])
    cache.set(*cache_key, results)
    return results
