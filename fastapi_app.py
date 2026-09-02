"""Minimal FastAPI wrapper that exposes the existing MCP tools over HTTP.

This file intentionally calls into the existing `tools/` layer rather than
duplicating business logic. It's a thin shim for non-MCP clients.
"""
import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from tools import search as search_tool, author as author_tool, journal as journal_tool
from tools import citation as citation_tool, summary as summary_tool, pdf as pdf_tool
from utils.exceptions import JournalSearchError
from config import OPENALEX_BASE_URL, CROSSREF_BASE_URL, CONTACT_EMAIL
from utils.http_client import get_json
from utils.exceptions import APIRequestError
from tools import concept as concept_tool


app = FastAPI(title="Journal Search HTTP API")

# Add CORS middleware for API access
# Customize allowed origins as needed by setting CORS_ALLOWED_ORIGINS environment variable
allowed_origins = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:*,http://127.0.0.1:*",
).split(",")
allowed_origins = [origin.strip() for origin in allowed_origins if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """Simple landing endpoint for browser requests and service discovery."""
    return {
        "service": "journal-search-mcp",
        "status": "ok",
        "message": "Journal Search MCP HTTP API",
        "endpoints": [
            "/health",
            "/search",
            "/paper/{identifier}",
            "/author",
            "/journal",
            "/citations",
            "/related",
            "/export",
            "/summarize",
            "/pdf",
            "/concepts",
            "/ready",
        ],
    }


@app.get("/health")
def health():
    """Basic health endpoint. Does not perform upstream checks to avoid
    making network calls from automated health checks.
    """
    return {"status": "ok"}


@app.get("/search")
def search_papers(keyword: str, year: Optional[int] = None, author: Optional[str] = None, journal: Optional[str] = None, sort_by: Optional[str] = None, page: int = 1, per_page: int = 10):
    try:
        return search_tool.search_papers(keyword=keyword, year=year, author=author, journal=journal, sort_by=sort_by, page=page, per_page=per_page)
    except JournalSearchError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/paper/{identifier:path}")
def paper_details(identifier: str):
    try:
        return search_tool.paper_details(identifier=identifier)
    except JournalSearchError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/author")
def search_author(author_name: str):
    try:
        # Normalize HTTP API to return a simple list of matching authors
        res = author_tool.search_author(author_name=author_name)
        return res.get("results", [])
    except JournalSearchError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/journal")
def search_journal(journal_name: str):
    try:
        # Normalize HTTP API to return a simple list of matching journals/sources
        res = journal_tool.search_journal(journal_name=journal_name)
        return res.get("results", [])
    except JournalSearchError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/citations")
def get_citations(doi: str, limit: int = 20):
    try:
        return citation_tool.get_citations(doi=doi, limit=limit)
    except JournalSearchError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/related")
def related_papers(doi: str, limit: int = 10):
    try:
        return citation_tool.related_papers(doi=doi, limit=limit)
    except JournalSearchError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/export")
def export_citation(doi: str, style: str = "apa"):
    try:
        return citation_tool.export_citation(doi=doi, style=style)
    except JournalSearchError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/summarize")
def summarize_paper(doi: str):
    try:
        return summary_tool.summarize_paper(doi=doi)
    except JournalSearchError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/pdf")
def open_access_pdf(doi: str):
    try:
        return pdf_tool.open_access_pdf(doi=doi)
    except JournalSearchError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/concepts")
def search_concepts(query: str):
    try:
        return concept_tool.search_concepts(query=query)
    except JournalSearchError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/ready")
def ready():
    """Lightweight readiness probe that checks critical upstream services.

    Returns HTTP 200 when critical upstreams are reachable and returning
    successful responses; otherwise returns 503 with per-service details.
    """
    # Allow skipping upstream checks in containerized/CI environments where
    # external API access may be blocked. Set SKIP_UPSTREAM_CHECKS=true to
    # short-circuit readiness to 'ready' without probing OpenAlex/Crossref.
    skip_checks = os.getenv("SKIP_UPSTREAM_CHECKS", "false").lower() in ("1", "true", "yes")
    if skip_checks:
        return {"status": "ready", "services": {"skipped": True}}

    services = {}

    # Probe OpenAlex (critical)
    try:
        get_json(f"{OPENALEX_BASE_URL}/works", params={"per_page": 1, "mailto": CONTACT_EMAIL}, service="openalex")
        services["openalex"] = {"ok": True}
    except APIRequestError as exc:
        services["openalex"] = {"ok": False, "error": str(exc)}

    # Probe Crossref (critical)
    try:
        get_json(f"{CROSSREF_BASE_URL}/works", params={"rows": 1}, service="crossref")
        services["crossref"] = {"ok": True}
    except APIRequestError as exc:
        services["crossref"] = {"ok": False, "error": str(exc)}

    all_ok = all(v.get("ok") for v in services.values())
    status = 200 if all_ok else 503
    if not all_ok:
        raise HTTPException(status_code=status, detail=services)
    return {"status": "ready", "services": services}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("fastapi_app:app", host="127.0.0.1", port=8000, reload=False)
