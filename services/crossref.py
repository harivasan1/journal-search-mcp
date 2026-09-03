"""
Client for the Crossref REST API (https://api.crossref.org).

Crossref is the DOI registration agency for scholarly publishers and
holds authoritative bibliographic metadata (authors, volume, issue,
pages, publisher) for the vast majority of DOIs. No API key is
required. Used mainly to power accurate citation exports.
"""

from typing import Any

from config import CONTACT_EMAIL, CROSSREF_BASE_URL
from utils.cache import cache
from utils.exceptions import APIRequestError, NotFoundError
from utils.http_client import get_json
from utils.logger import get_logger

logger = get_logger(__name__)
SERVICE_NAME = "crossref"


def _headers() -> dict[str, str]:
    return {"User-Agent": f"journal-search-mcp (mailto:{CONTACT_EMAIL})"}


def get_work_by_doi(doi: str) -> dict[str, Any]:
    """Fetch raw Crossref metadata for a DOI."""
    cache_key = ("crossref_doi", doi)
    cached = cache.get(*cache_key)
    if cached is not None:
        return cached

    url = f"{CROSSREF_BASE_URL}/works/{doi}"
    try:
        data = get_json(url, headers=_headers(), service=SERVICE_NAME)
    except APIRequestError as exc:
        # Distinguish between a genuine 404/not-found and other upstream errors.
        msg = str(exc)
        if "404" in msg or "Not Found" in msg:
            raise NotFoundError(f"No Crossref record found for DOI: {doi}") from exc
        # Re-raise other API errors so calling code can decide how to handle them.
        raise

    message = data.get("message", {})
    cache.set(*cache_key, message)
    return message


def extract_citation_fields(message: dict[str, Any]) -> dict[str, Any]:
    """Normalize raw Crossref metadata into fields used by the citation formatter."""
    authors = []
    for a in message.get("author", []) or []:
        authors.append({"given": a.get("given", ""), "family": a.get("family", "")})

    container = message.get("container-title") or []
    published = (
        message.get("published")
        or message.get("published-print")
        or message.get("published-online")
        or {}
    )
    date_parts = (published.get("date-parts") or [[None]])[0]

    return {
        "title": (message.get("title") or [""])[0],
        "authors": authors,
        "journal": container[0] if container else None,
        "year": date_parts[0] if date_parts else None,
        "volume": message.get("volume"),
        "issue": message.get("issue"),
        "pages": message.get("page"),
        "publisher": message.get("publisher"),
        "doi": message.get("DOI"),
    }
