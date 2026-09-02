"""
Client for the OpenAlex API (https://docs.openalex.org).

OpenAlex is a free, open catalog of scholarly works, authors, and
journals covering ~250M+ works. No API key is required. We send a
contact email on every request to join the "polite pool," which
grants higher and more stable rate limits.
"""

from typing import Any, Dict, List, Optional

from config import CONTACT_EMAIL, DEFAULT_PAGE_SIZE, OPENALEX_BASE_URL
from utils.cache import cache
from utils.exceptions import NotFoundError
from utils.http_client import get_json
from utils.logger import get_logger

logger = get_logger(__name__)

SERVICE_NAME = "openalex"


def _headers() -> Dict[str, str]:
    return {"User-Agent": f"journal-search-mcp (mailto:{CONTACT_EMAIL})"}


def _reconstruct_abstract(inverted_index: Optional[Dict[str, List[int]]]) -> Optional[str]:
    """
    OpenAlex stores abstracts as an inverted index (word -> positions)
    for copyright reasons. Rebuild the plain-text abstract from it.
    """
    if not inverted_index:
        return None
    positions: Dict[int, str] = {}
    for word, idxs in inverted_index.items():
        for idx in idxs:
            positions[idx] = word
    if not positions:
        return None
    ordered = [positions[i] for i in sorted(positions)]
    return " ".join(ordered)


def _work_to_dict(work: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a raw OpenAlex 'work' object into our internal paper dict."""
    authorships = work.get("authorships", []) or []
    authors = [a.get("author", {}).get("display_name", "") for a in authorships if a.get("author")]

    primary_location = work.get("primary_location") or {}
    source = primary_location.get("source") or {}
    open_access = work.get("open_access") or {}

    return {
        "title": work.get("title") or work.get("display_name") or "Untitled",
        "authors": [a for a in authors if a],
        "journal": source.get("display_name"),
        "year": work.get("publication_year"),
        "doi": (work.get("doi") or "").replace("https://doi.org/", "") or None,
        "abstract": _reconstruct_abstract(work.get("abstract_inverted_index")),
        "citation_count": work.get("cited_by_count", 0),
        "openalex_id": (work.get("id") or "").replace("https://openalex.org/", "") or None,
        "url": work.get("id"),
        "open_access_pdf": open_access.get("oa_url"),
        "keywords": [c.get("display_name") for c in (work.get("concepts") or [])[:8]],
        "referenced_works": work.get("referenced_works", []) or [],
        "related_works": work.get("related_works", []) or [],
    }


def search_works(
    keyword: str,
    year: Optional[int] = None,
    author: Optional[str] = None,
    journal: Optional[str] = None,
    sort: Optional[str] = None,
    page: int = 1,
    per_page: int = DEFAULT_PAGE_SIZE,
) -> List[Dict[str, Any]]:
    """
    Search OpenAlex works (papers) by keyword, with optional year,
    author, and journal filters, plus sorting and pagination.

    sort: an OpenAlex sort expression, e.g. "cited_by_count:desc"
          or "publication_date:desc". None means relevance order.
    """
    cache_key = (
        "search_works",
        keyword,
        str(year),
        str(author),
        str(journal),
        str(sort),
        str(page),
        str(per_page),
    )
    cached = cache.get(*cache_key)
    if cached is not None:
        return cached

    filters = []
    if year:
        filters.append(f"publication_year:{year}")
    if author:
        filters.append(f"authorships.author.display_name.search:{author}")
    if journal:
        filters.append(f"primary_location.source.display_name.search:{journal}")

    params: Dict[str, Any] = {
        "search": keyword,
        "per_page": min(per_page, 50),
        "page": page,
        "mailto": CONTACT_EMAIL,
    }
    if filters:
        params["filter"] = ",".join(filters)
    if sort:
        params["sort"] = sort

    data = get_json(
        f"{OPENALEX_BASE_URL}/works", params=params, headers=_headers(), service=SERVICE_NAME
    )
    results = [_work_to_dict(w) for w in data.get("results", [])]
    cache.set(*cache_key, results)
    return results


def get_work(identifier: str) -> Dict[str, Any]:
    """Fetch a single work by OpenAlex ID (e.g. 'W123456789') or DOI."""
    cache_key = ("get_work", identifier)
    cached = cache.get(*cache_key)
    if cached is not None:
        return cached

    identifier = identifier.strip()
    if identifier.lower().startswith("10."):
        url = f"{OPENALEX_BASE_URL}/works/https://doi.org/{identifier}"
    else:
        url = f"{OPENALEX_BASE_URL}/works/{identifier}"

    try:
        data = get_json(
            url, params={"mailto": CONTACT_EMAIL}, headers=_headers(), service=SERVICE_NAME
        )
    except Exception as exc:
        raise NotFoundError(f"No paper found for identifier: {identifier}") from exc

    result = _work_to_dict(data)
    cache.set(*cache_key, result)
    return result


def search_authors(name: str, per_page: int = DEFAULT_PAGE_SIZE) -> List[Dict[str, Any]]:
    """Search OpenAlex authors by name."""
    cache_key = ("search_authors", name, str(per_page))
    cached = cache.get(*cache_key)
    if cached is not None:
        return cached

    params = {"search": name, "per_page": per_page, "mailto": CONTACT_EMAIL}
    data = get_json(
        f"{OPENALEX_BASE_URL}/authors", params=params, headers=_headers(), service=SERVICE_NAME
    )

    results = []
    for a in data.get("results", []):
        last_inst = a.get("last_known_institutions") or []
        if isinstance(last_inst, dict):
            last_inst = [last_inst]
        affiliation = last_inst[0].get("display_name") if last_inst else None
        results.append(
            {
                "name": a.get("display_name"),
                "affiliation": affiliation,
                "h_index": (a.get("summary_stats") or {}).get("h_index"),
                "citation_count": a.get("cited_by_count", 0),
                "works_count": a.get("works_count", 0),
                "openalex_id": (a.get("id") or "").replace("https://openalex.org/", "") or None,
            }
        )
    cache.set(*cache_key, results)
    return results


def search_sources(name: str, per_page: int = DEFAULT_PAGE_SIZE) -> List[Dict[str, Any]]:
    """Search OpenAlex sources (journals / conference proceedings / repositories)."""
    cache_key = ("search_sources", name, str(per_page))
    cached = cache.get(*cache_key)
    if cached is not None:
        return cached

    params = {"search": name, "per_page": per_page, "mailto": CONTACT_EMAIL}
    data = get_json(
        f"{OPENALEX_BASE_URL}/sources", params=params, headers=_headers(), service=SERVICE_NAME
    )

    results = []
    for s in data.get("results", []):
        issn_list = s.get("issn") or []
        results.append(
            {
                "name": s.get("display_name"),
                "publisher": s.get("host_organization_name"),
                "issn": issn_list[0] if issn_list else None,
                "homepage": s.get("homepage_url"),
                "works_count": s.get("works_count", 0),
                "openalex_id": (s.get("id") or "").replace("https://openalex.org/", "") or None,
            }
        )
    cache.set(*cache_key, results)
    return results


def search_concepts(query: str, per_page: int = DEFAULT_PAGE_SIZE) -> List[Dict[str, Any]]:
    """Search OpenAlex concepts (topics/keywords) by name or query."""
    cache_key = ("search_concepts", query, str(per_page))
    cached = cache.get(*cache_key)
    if cached is not None:
        return cached

    params = {"search": query, "per_page": per_page, "mailto": CONTACT_EMAIL}
    data = get_json(
        f"{OPENALEX_BASE_URL}/concepts", params=params, headers=_headers(), service=SERVICE_NAME
    )

    results = []
    for c in data.get("results", []):
        results.append(
            {
                "id": (c.get("id") or "").replace("https://openalex.org/", ""),
                "name": c.get("display_name"),
                "level": c.get("level"),
                "works_count": c.get("works_count", 0),
            }
        )

    cache.set(*cache_key, results)
    return results
