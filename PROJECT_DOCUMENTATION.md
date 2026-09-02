# Journal Search MCP Server — Project Documentation

This document is a machine-generated, code-grounded technical reference for the repository at the project root. It documents implemented features, architecture, and developer operations based on the actual source files in this repository.

See also: `ARCHITECTURE.md`, `API_DOCUMENTATION.md`, `MCP_TOOLS.md`, `DATABASE_CACHE.md`, `DEPLOYMENT.md`, `TESTING.md`, `SECURITY.md`, `TROUBLESHOOTING.md`.

## 1 — Project Overview

- Project title: Journal Search MCP Server
- Purpose: Provide an MCP-compatible server that exposes tools for searching and retrieving scholarly metadata (papers, authors, journals, citations, related works, exported citations, summaries, and open-access PDFs) by aggregating and normalizing data from OpenAlex, Crossref and Semantic Scholar.
- Background: The repository implements a layered MCP server where `tools/` map to MCP tools, `services/` implement thin API clients, and `utils/` provide caching, HTTP client behavior, and logging.
- Problem statement: Scholarly metadata is fragmented across multiple APIs with different shapes, rate limits and formats. Clients (MCP assistants) need consistent, normalized responses without dealing with multiple upstream providers.
- Proposed solution: A single MCP server that orchestrates normalized calls to OpenAlex, Crossref and Semantic Scholar, caches responses in SQLite, and exposes simple, stable tools for assistant clients.
- Key objectives: correctness, testability (mocked tests), predictable rate-limiting, caching to reduce upstream calls, and a production-ready deployment (Docker).
- Scope: Server-side MCP tools; a REST wrapper is included (FastAPI) for non-MCP clients. The canonical interface is the MCP toolset exposed by `server.py`.
- Target users: Developers integrating scholarly search into MCP assistants and researchers who want a programmable interface for discovery workflows.
- Supported platforms: Python 3.12+ environments; Docker-compatible containers.

## 2 — System Overview

- MCP server entrypoint: `server.py` — registers tools and runs an MCP server (stdio transport).
- FastAPI layer: `fastapi_app.py` — optional REST wrapper that reuses the same services for non-MCP clients.
- Research services: `services/openalex.py`, `services/semanticscholar.py`, `services/crossref.py` implement network calls and normalization.
- Cache layer: `utils/cache.py` — SQLite-backed cache used to reduce duplicate calls.
- External APIs: OpenAlex, Semantic Scholar, Crossref — each used for specific data and fallbacks; no secrets are embedded in the repo.
- Response normalization: Each service returns Pydantic models in `models/` and tools format responses into simple dicts for MCP consumers.

## 3 — Quick repo landmarks

- `server.py` — MCP wiring and tool registration
- `fastapi_app.py` — FastAPI HTTP wrapper for the same features
- `tools/` — tool-level validation and orchestration
- `services/` — HTTP clients for external providers
- `models/` — Pydantic models for Paper / Author / Journal
- `utils/` — cache, http client, logger and custom exceptions
- `tests/` — unit tests (mocked upstream calls)

## 4 — How to use (developer quick start)

1. Create and activate a Python venv (Python 3.12+).
2. Install dependencies: `pip install -r requirements.txt`.
3. Optionally copy `.env.example` to `.env` and set `CONTACT_EMAIL` and `SEMANTIC_SCHOLAR_API_KEY` if available.
4. Start MCP server (stdio transport): `python server.py`.
5. Or run the HTTP API wrapper: `python -m uvicorn fastapi_app:app --host 127.0.0.1 --port 8000`

---

Note: This document is generated from repository structure and source code. See the other markdown files in the repo for in-depth API docs, architecture diagrams, tool definitions and troubleshooting steps.
