"""Minimal FastAPI wrapper that exposes the existing MCP tools over HTTP.

This file intentionally calls into the existing `tools/` layer rather than
duplicating business logic. It's a thin shim for non-MCP clients.
"""

import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from config import CONTACT_EMAIL, CROSSREF_BASE_URL, OPENALEX_BASE_URL
from tools import author as author_tool
from tools import citation as citation_tool
from tools import concept as concept_tool
from tools import journal as journal_tool
from tools import pdf as pdf_tool
from tools import search as search_tool
from tools import summary as summary_tool
from utils.exceptions import APIRequestError, JournalSearchError
from utils.http_client import get_json

# Mount MCP Streamable HTTP app at /mcp so MCP clients can use
# https://<host>/mcp to talk to the existing MCP server implemented
# in `server.py`. We import the module-level `mcp` instance and
# mount its StreamableHTTP Starlette app. Keep this lightweight to
# avoid duplicating any tool logic.
try:
    # Import locally defined MCP server (does not call mcp.run())
    from server import mcp as _mcp  # type: ignore
except (
    ImportError,
    ModuleNotFoundError,
):  # pragma: no cover - import errors are surfaced at startup
    _mcp = None

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


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add conservative security headers for the optional HTTP deployment path."""
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=()")
    return response


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
def search_papers(
    keyword: str,
    year: int | None = None,
    author: str | None = None,
    journal: str | None = None,
    sort_by: str | None = None,
    page: int = 1,
    per_page: int = 10,
):
    try:
        return search_tool.search_papers(
            keyword=keyword,
            year=year,
            author=author,
            journal=journal,
            sort_by=sort_by,
            page=page,
            per_page=per_page,
        )
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
        get_json(
            f"{OPENALEX_BASE_URL}/works",
            params={"per_page": 1, "mailto": CONTACT_EMAIL},
            service="openalex",
        )
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

    port = int(os.getenv("PORT", os.getenv("PORT_RENDER", "8000")))
    uvicorn.run("fastapi_app:app", host="0.0.0.0", port=port, reload=False)


# Mount the MCP Streamable HTTP app under /mcp when available. We do this
# after the FastAPI app is created so all existing REST endpoints remain
# unchanged. We set the inner FastMCP streamable path to root ("/") so the
# mounted application exposes the transport at exactly /mcp.
if _mcp is not None:
    @app.on_event("startup")
    async def _mcp_startup():
        try:
            # Disable transport security to avoid host validation problems in
            # simple deployments and tests, then create the streamable app and
            # mount it under /mcp so the MCP Streamable HTTP transport is
            # available at POST/GET /mcp.
            _mcp.settings.transport_security = None
            _mcp.settings.streamable_http_path = "/"
            starlette_app = _mcp.streamable_http_app()
            app.mount("/mcp", starlette_app)

            # Enter the session manager lifespan so the manager's task group
            # is available to handle incoming requests.
            cm = _mcp.session_manager.run()
            await cm.__aenter__()
            app.state._mcp_cm = cm
        except (AttributeError, RuntimeError, ValueError) as exc:  # pragma: no cover - best-effort startup
            print("Warning: failed to start/mount MCP streamable-http app:", exc)

    @app.on_event("shutdown")
    async def _mcp_shutdown():
        cm = getattr(app.state, "_mcp_cm", None)
        if cm is not None:
            try:
                await cm.__aexit__(None, None, None)
            except (AttributeError, RuntimeError):
                print("Warning: exception while shutting down MCP session manager")
