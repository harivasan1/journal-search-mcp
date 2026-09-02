# Journal Search MCP Server

A production-ready [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server that gives AI assistants the ability to search and retrieve academic research papers, authors, journals, and citation data — using only free, legal, no-scraping APIs.

Built with the official **MCP Python SDK**, **OpenAlex**, **Crossref**, and **Semantic Scholar**.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Data Sources](#data-sources)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Server](#running-the-server)
- [Connecting an MCP Client](#connecting-an-mcp-client)
- [Tools Reference](#tools-reference)
- [Example Prompts & Sample Responses](#example-prompts--sample-responses)
- [Testing](#testing)
- [Architecture Notes](#architecture-notes)
- [Screenshots](#screenshots)
- [Future Improvements](#future-improvements)
- [License](#license)

---

## Overview

Journal Search MCP Server exposes 9 tools that let any MCP-compatible AI assistant (Claude Desktop, Claude Code, or a custom MCP client) search scholarly literature, pull full paper metadata, look up authors and journals, trace citation graphs, find related work, export formatted citations, generate quick summaries, and locate legal open-access PDFs.

It talks **only** to official, free, keyless (or optional-key) APIs — **no web scraping, no paywalled content, no unofficial endpoints.**

## Features

- 🔎 Full-text keyword search across scholarly works with year / author / journal filters
- 📄 Rich paper metadata: title, authors, journal, year, DOI, abstract, citation count
- 👤 Author profiles: affiliation, h-index, citation count, publication count
- 📚 Journal/source profiles: publisher, ISSN, homepage, paper count
- 🔗 Citation graphs: who cites this paper, what it references
- 🧭 Related-paper recommendations
- 📝 Citation export in **APA, MLA, IEEE, and BibTeX**
- 🤖 Lightweight AI-assisted summaries (Semantic Scholar TL;DR + abstract fallback)
- 🔓 Legal open-access PDF lookup (Unpaywall-backed, via OpenAlex/Semantic Scholar)
- ⚙️ Pagination, sorting (relevance / citations / latest), keyword suggestions
- 🛡️ Retries with backoff, request timeouts, client-side rate limiting, SQLite response caching
- 🧱 Clean layered architecture: `tools/` → `services/` → external APIs
- ✅ Full unit test coverage with mocked HTTP calls (no network needed to test)

## Running the Backend

```bash
cd "d:\journal-search-mcp self\journal-search-mcp server"
python -m uvicorn fastapi_app:app --host 0.0.0.0 --port 8000
```

The HTTP API will be available at `http://localhost:8000` with the `/health` endpoint ready for health checks

## Project Structure

```
journal-search-mcp server/
├── .dockerignore
├── .env.example
├── .gitignore
├── .github/
│   └── workflows/
│       └── ci.yml
├── API_DOCUMENTATION.md
├── ARCHITECTURE.md
├── DATABASE_CACHE.md
├── DEPLOYMENT.md
├── Dockerfile
├── docker-compose.yml
├── fastapi_app.py
├── LICENSE
├── MCP_TOOLS.md
├── PROJECT_DOCUMENTATION.md
├── README.md
├── pytest.ini
├── pyproject.toml
├── requirements.txt
├── SECURITY.md
├── server.py
├── TESTING.md
├── TROUBLESHOOTING.md
├── config.py
├── cache.sqlite3
├── k8s/
│   └── deployment-readiness.yaml
├── models/
│   ├── __init__.py
│   ├── author.py
│   ├── journal.py
│   └── paper.py
├── services/
│   ├── __init__.py
│   ├── crossref.py
│   ├── openalex.py
│   └── semanticscholar.py
├── tools/
│   ├── __init__.py
│   ├── author.py
│   ├── citation.py
│   ├── concept.py
│   ├── journal.py
│   ├── pdf.py
│   ├── search.py
│   └── summary.py
├── utils/
│   ├── __init__.py
│   ├── cache.py
│   ├── citation_formatter.py
│   ├── exceptions.py
│   ├── http_client.py
│   └── logger.py
├── scripts/
│   ├── run_tests_docker.ps1
│   └── run_tests_docker.sh
└── tests/
  ├── __init__.py
  ├── test_author.py
  ├── test_citation.py
  ├── test_concepts.py
  ├── test_e2e_integration.py
  ├── test_edge_cases.py
  ├── test_fastapi_integration.py
  ├── test_journal.py
  ├── test_pdf.py
  ├── test_rate_limit.py
  ├── test_ready.py
  ├── test_search.py
  └── test_summary.py
```
│   └── exceptions.py               # custom error hierarchy
│
└── tests/                    # Unit tests (mocked HTTP, no network required)
    ├── test_search.py
    ├── test_author.py
    ├── test_journal.py
    ├── test_citation.py
    ├── test_summary.py
    └── test_pdf.py
```

**Why this layout:** `server.py` only knows about MCP wiring. `tools/` validates input and shapes output. `services/` is the only layer that talks HTTP. `utils/` holds infrastructure (caching, retries, logging) shared by every service. This keeps each file small, testable, and easy to extend — e.g. adding a new data source means adding one file to `services/` without touching anything else.

## Installation

**Requirements:** Python 3.12+


```bash
# 1. Clone or download the project
cd journal-search-mcp

# 2. Create a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv venv
uv pip install -r requirements.txt
```

## Configuration

Copy the example environment file and  edit as needed — **every setting has a working default, so this step is optional**:

```bash
cp .env.example .env
```

Key settings:

| Variable | Default | Purpose |
|---|---|---|
| `CONTACT_EMAIL` | `your-email@example.com` | Sent to OpenAlex for higher rate limits |
| `SEMANTIC_SCHOLAR_API_KEY` | *(empty)* | Optional key for higher Semantic Scholar limits |
| `REQUEST_TIMEOUT` | `15` | Seconds before an HTTP request times out |
| `MAX_RETRIES` | `3` | Retry attempts for transient failures (429/5xx) |
| `CACHE_ENABLED` | `true` | Toggle local SQLite response caching |
| `CACHE_TTL_SECONDS` | `3600` | How long cached responses stay valid |
| `DEFAULT_PAGE_SIZE` | `10` | Default results per page for search_papers |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Running the Server

```bash
python server.py
```

This starts the MCP server over **stdio transport**, the standard way MCP clients launch local servers. You won't see much output in the terminal — that's expected; the server is now waiting for an MCP client to connect via stdin/stdout.

## Connecting an MCP Client

### Claude Desktop / Claude Code (VS Code)

Add this to your MCP client's configuration file (e.g. `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "journal-search": {
      "command": "python",
      "args": ["/absolute/path/to/journal-search-mcp/server.py"],
      "env": {
        "CONTACT_EMAIL": "your-email@example.com"
      }
    }
  }
}
```

If you're using a virtual environment, point `command` at the venv's Python interpreter instead, e.g. `/absolute/path/to/journal-search-mcp/.venv/bin/python`.

### VS Code (generic MCP extension)

Most VS Code MCP extensions use the same `mcpServers` JSON shape above — add it to the extension's settings (often `.vscode/mcp.json` in the workspace) and reload the window.

### Testing without a full client — MCP Inspector

The MCP Python SDK ships a CLI dev tool for interactively testing tools in a browser UI:

```bash
mcp dev server.py
```

## Tools Reference

| Tool | Inputs | Returns |
|---|---|---|
| `search_papers` | `keyword`, `year?`, `author?`, `journal?`, `sort_by?` (`relevance`/`citations`/`latest`), `page?`, `per_page?` | List of papers + keyword suggestions |
| `paper_details` | `identifier` (DOI or OpenAlex ID) | Full metadata, abstract, keywords, references, related works |
| `search_author` | `author_name` | Matching author profiles (affiliation, h-index, citations, works count) |
| `search_journal` | `journal_name` | Matching journal profiles (publisher, ISSN, homepage, paper count) |
| `get_citations` | `doi`, `limit?` | Citation count, citing papers, referenced papers |
| `related_papers` | `doi`, `limit?` | Top similar/recommended papers |
| `export_citation` | `doi`, `style?` (`apa`/`mla`/`ieee`/`bibtex`) | Formatted citation string |
| `summarize_paper` | `doi` | Short summary, key findings, research contribution, practical applications |
| `open_access_pdf` | `doi` | Legal open-access PDF URL, or a clear "not found" message |

Every tool returns a plain dict; on failure it returns `{"error": "..."}` instead of raising, so the calling assistant always gets a usable response.

## Example Prompts & Sample Responses

**"Find recent papers about transformer attention mechanisms, sorted by citation count"**
→ calls `search_papers(keyword="transformer attention mechanisms", sort_by="citations")`
```json
{
  "query": "transformer attention mechanisms",
  "result_count": 10,
  "results": [
    {
      "title": "Attention Is All You Need",
      "authors": ["Ashish Vaswani", "Noam Shazeer", "..."],
      "journal": "Advances in Neural Information Processing Systems",
      "year": 2017,
      "doi": "10.48550/arxiv.1706.03762",
      "citation_count": 112000,
      "openalex_id": "W2963403868"
    }
  ],
  "keyword_suggestions": ["neural networks", "sequence modeling", "self-attention"]
}
```

**"Give me full details on DOI 10.1038/s41586-021-03819-2"**
→ calls `paper_details(identifier="10.1038/s41586-021-03819-2")`

**"Who is Yoshua Bengio and what's his citation count?"**
→ calls `search_author(author_name="Yoshua Bengio")`

**"What journal is 'Nature Machine Intelligence' and who publishes it?"**
→ calls `search_journal(journal_name="Nature Machine Intelligence")`

**"How many times has this paper been cited, and what does it cite?"**
→ calls `get_citations(doi="10.1038/s41586-021-03819-2")`

**"Find me 5 papers similar to this one"**
→ calls `related_papers(doi="...", limit=5)`

**"Give me a BibTeX citation for this DOI"**
→ calls `export_citation(doi="...", style="bibtex")`
```bibtex
@article{Vaswani2017,
  title = {Attention Is All You Need},
  author = {Vaswani, Ashish and Shazeer, Noam},
  journal = {Advances in Neural Information Processing Systems},
  year = {2017},
  doi = {10.48550/arxiv.1706.03762},
}
```

**"Summarize this paper for me"**
→ calls `summarize_paper(doi="...")`

**"Is there a free PDF of this paper?"**
→ calls `open_access_pdf(doi="...")`

## Testing

Unit tests mock every HTTP call, so the full suite runs offline in well under a second:

```bash
pytest
# or with verbose output
pytest -v
```

Expected output:

```
tests/test_author.py ...
tests/test_citation.py .......
tests/test_journal.py ...
tests/test_pdf.py ....
tests/test_search.py .....
tests/test_summary.py ...

25 passed
```

## Architecture Notes

- **Retry & timeout:** `utils/http_client.py` wraps every request with `urllib3.Retry` (backoff on 429/5xx) and a configurable timeout, so transient upstream hiccups don't crash a tool call.
- **Rate limiting:** a simple per-service throttle (`MIN_REQUEST_INTERVAL`) spaces out consecutive calls to the same API, keeping the server within each provider's fair-use limits.
- **Caching:** `utils/cache.py` is a small SQLite-backed cache with TTL expiry, keyed by a hash of the request parameters. Identical searches within the TTL window are served instantly without a network round trip.
- **Error handling:** all tool-level errors are `JournalSearchError` subclasses (`ValidationInputError`, `NotFoundError`, `APIRequestError`). `server.py` catches these centrally and converts them into `{"error": "..."}` dicts rather than letting exceptions propagate to the client.
- **Abstract reconstruction:** OpenAlex stores abstracts as an inverted index for copyright reasons; `services/openalex.py` rebuilds plain text from it.

## Screenshots

*(placeholder — add screenshots of the server running, an MCP Inspector session, or example tool calls in your MCP client here)*

```
docs/screenshot-search.png
docs/screenshot-citation-export.png
```

## Future Improvements

- [ ] Add a `FastAPI` REST wrapper exposing the same tools over HTTP for non-MCP clients
- [ ] Add PubMed / arXiv / DOAJ as additional data sources
- [ ] Smarter keyword suggestions using OpenAlex's concept hierarchy
- [ ] Streaming/batched citation graph traversal for large citation networks
- [ ] Optional local LLM-based summarization instead of TL;DR/extractive fallback
- [ ] Docker image for one-command deployment
- [ ] `mcp resources` support to expose cached papers as browsable resources

## License
## Documentation

This repository includes generated developer documentation in these files:

- `PROJECT_DOCUMENTATION.md` — master overview and quick start
- `ARCHITECTURE.md` — system architecture and diagrams
- `API_DOCUMENTATION.md` — HTTP wrapper endpoints (FastAPI)
- `MCP_TOOLS.md` — per-tool reference for the MCP toolset
- `DATABASE_CACHE.md` — cache behavior and lifecycle
- `DEPLOYMENT.md` — local, Docker and Kubernetes deployment notes
- `TESTING.md` — test running and categories
- `SECURITY.md` — security and secrets guidance
- `TROUBLESHOOTING.md` — common errors and fixes

Please consult those files for developer onboarding and operational procedures.

MIT License — free to use, modify, and distribute. See `LICENSE` for details.

---

*Built as a portfolio-quality example of a real-world, production-grade MCP server.*




# 1. Setup
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Run MCP Server
python server.py

# 3. Or run HTTP API
python -m uvicorn fastapi_app:app --host 127.0.0.1 --port 8000

# 4. Run tests
pytest -v