"""
MCP tool implementation for OpenAlex concept lookup.

Backs a `search_concepts` tool used by the HTTP shim.
"""

from typing import Any

from services import openalex
from utils.exceptions import NotFoundError, ValidationInputError


def search_concepts(query: str) -> list[dict[str, Any]]:
    if not query or not query.strip():
        raise ValidationInputError("`query` must be a non-empty string.")

    results = openalex.search_concepts(query.strip())
    if not results:
        raise NotFoundError(f"No concepts found for '{query}'.")

    return results
