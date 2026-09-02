"""
MCP tool implementation for journal (publication source) search.

Backs the `search_journal` MCP tool.
"""
from typing import Any, Dict

from services import openalex
from utils.exceptions import NotFoundError, ValidationInputError


def search_journal(journal_name: str) -> Dict[str, Any]:
    """
    Search for a journal's publisher, ISSN, homepage, and paper count.

    Args:
        journal_name: Full or partial journal name to search for.

    Returns:
        A dict containing matching journal profiles.
    """
    if not journal_name or not journal_name.strip():
        raise ValidationInputError("`journal_name` must be a non-empty string.")

    results = openalex.search_sources(journal_name.strip())
    if not results:
        raise NotFoundError(f"No journal found matching '{journal_name}'.")

    return {
        "query": journal_name,
        "result_count": len(results),
        "results": results,
    }
