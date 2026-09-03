"""
MCP tool implementation for author search.

Backs the `search_author` MCP tool.
"""

from typing import Any

from services import openalex
from utils.exceptions import NotFoundError, ValidationInputError


def search_author(author_name: str) -> dict[str, Any]:
    """
    Search for an author's profile, affiliation, and citation metrics.

    Args:
        author_name: Full or partial author name to search for.

    Returns:
        A dict containing matching author profiles, each with name,
        affiliation, h-index (if available), citation count, and
        number of publications.
    """
    if not author_name or not author_name.strip():
        raise ValidationInputError("`author_name` must be a non-empty string.")

    results = openalex.search_authors(author_name.strip())
    if not results:
        raise NotFoundError(f"No author found matching '{author_name}'.")

    return {
        "query": author_name,
        "result_count": len(results),
        "results": results,
    }
