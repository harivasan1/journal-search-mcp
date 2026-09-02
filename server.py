"""
Journal Search MCP Server
==========================
Entry point for the MCP server. Registers all tools and starts the
server over stdio transport, which is compatible with Claude Desktop,
Claude Code, and any other MCP-compatible client.

Run with:
    python server.py
or, with uv:
    uv run server.py
"""
from typing import Optional

from mcp.server.fastmcp import FastMCP

from tools import author, citation, journal, pdf, search, summary
from utils.exceptions import JournalSearchError
from utils.logger import get_logger

logger = get_logger("journal_search_mcp")

mcp = FastMCP(
    name="journal-search-mcp",
    instructions=(
        "A research assistant server for searching and retrieving academic "
        "papers from OpenAlex, Crossref, and Semantic Scholar. Use these "
        "tools to find papers, authors, journals, citations, and open-access "
        "PDFs, and to generate formatted citations and summaries."
    ),
)


def _safe(fn, **kwargs):
    """
    Run a tool function and convert internal errors into clean,
    MCP-friendly dicts instead of raising raw tracebacks to the client.
    """
    try:
        return fn(**kwargs)
    except JournalSearchError as exc:
        logger.warning("Tool error in %s: %s", fn.__name__, exc)
        return {"error": str(exc)}
    except Exception as exc:  # noqa: BLE001 - convert any unexpected error safely
        logger.exception("Unexpected error in %s", fn.__name__)
        return {"error": f"Unexpected error: {exc}"}


@mcp.tool()
def search_papers(
    keyword: str,
    year: Optional[int] = None,
    author: Optional[str] = None,
    journal: Optional[str] = None,
    sort_by: Optional[str] = None,
    page: int = 1,
    per_page: int = 10,
) -> dict:
    """
    Search academic papers by keyword with optional year, author, and
    journal filters. sort_by can be 'relevance' (default), 'citations',
    or 'latest'. Supports pagination via page/per_page.
    """
    return _safe(
        search.search_papers,
        keyword=keyword, year=year, author=author, journal=journal,
        sort_by=sort_by, page=page, per_page=per_page,
    )


@mcp.tool()
def paper_details(identifier: str) -> dict:
    """
    Get full metadata for a paper by DOI or OpenAlex ID, including
    abstract, keywords, references, and related works.
    """
    return _safe(search.paper_details, identifier=identifier)


@mcp.tool()
def search_author(author_name: str) -> dict:
    """Search for an author's profile, affiliation, and citation metrics."""
    return _safe(author.search_author, author_name=author_name)


@mcp.tool()
def search_journal(journal_name: str) -> dict:
    """Search for a journal's publisher, ISSN, homepage, and paper count."""
    return _safe(journal.search_journal, journal_name=journal_name)


@mcp.tool()
def get_citations(doi: str, limit: int = 20) -> dict:
    """Get citation count, citing papers, and referenced papers for a DOI."""
    return _safe(citation.get_citations, doi=doi, limit=limit)


@mcp.tool()
def related_papers(doi: str, limit: int = 10) -> dict:
    """Get up to `limit` papers related/similar to the given DOI."""
    return _safe(citation.related_papers, doi=doi, limit=limit)


@mcp.tool()
def export_citation(doi: str, style: str = "apa") -> dict:
    """Export a formatted citation. style: 'apa', 'mla', 'ieee', or 'bibtex'."""
    return _safe(citation.export_citation, doi=doi, style=style)


@mcp.tool()
def summarize_paper(doi: str) -> dict:
    """Generate a short AI-assisted summary, key findings, and practical applications for a paper."""
    return _safe(summary.summarize_paper, doi=doi)


@mcp.tool()
def open_access_pdf(doi: str) -> dict:
    """Return a legal open-access PDF URL for a DOI, if one exists."""
    return _safe(pdf.open_access_pdf, doi=doi)


if __name__ == "__main__":
    logger.info("Starting Journal Search MCP Server...")
    mcp.run()
