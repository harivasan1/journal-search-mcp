# MCP Tools Reference

This document lists the MCP tools implemented in `tools/`. Each tool validates input, calls relevant services, and returns normalized results. The canonical implementations are in `tools/*.py` — the descriptions below summarize behavior as implemented.

Common behavior
- Tools return plain JSON-serializable dicts.
- On failure, tools return an error dict such as `{ "error": "..." }` rather than throwing uncaught exceptions.
- Inputs are validated using Pydantic models or explicit checks in `tools/`.

Implemented tools (file -> exported tool names)

- `tools/search.py`
  - `search_papers` — keyword search across OpenAlex (primary) with filter parameters: year, author, journal, sort_by (relevance/citations/latest), page, per_page. Returns list of normalized paper summaries and keyword suggestions.
  - `paper_details` — fetch full metadata for a paper by DOI or OpenAlex ID (abstract, references, related works).

- `tools/author.py`
  - `search_author` — search authors by name, returns profiles (name, affiliation, works count, citation count).

- `tools/journal.py`
  - `search_journal` — lookup journals by title/ISSN, returns publisher, homepage, and counts.

- `tools/citation.py`
  - `get_citations` — get citing and referenced papers for a DOI.
  - `related_papers` — recommend similar papers.
  - `export_citation` — return formatted citation string in requested style (apa, mla, ieee, bibtex).

- `tools/summary.py`
  - `summarize_paper` — short summary using Semantic Scholar TL;DR when available, with abstract fallback.

- `tools/pdf.py`
  - `open_access_pdf` — find legal OA PDF using OpenAlex and Semantic Scholar fallbacks.

For parameter details and exact schemas, consult the Pydantic models in `models/` and the tool source files.
