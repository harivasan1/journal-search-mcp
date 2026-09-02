# Architecture — Journal Search MCP Server

This file documents the system architecture and major components. It is grounded in the source files at the repository root.

## High-level architecture

- Client layer: MCP clients (stdio) or HTTP REST clients
- FastAPI REST layer: `fastapi_app.py` (serves HTTP API for non-MCP clients)
- MCP tools layer: `tools/*.py` (validate inputs, orchestrate service calls)
- Service clients: `services/*.py` (OpenAlex, Semantic Scholar, Crossref)
- Cache layer: `utils/cache.py` (SQLite cache)
- Utilities: `utils/http_client.py`, `utils/logger.py`, `utils/exceptions.py`

## Component diagram (Mermaid)

```mermaid
flowchart LR
  A[MCP Client] -->|stdio| B[server.py / MCP tools]
  C[HTTP Client] -->|REST| D[fastapi_app.py]
  B --> E[tools/*]
  E --> F[services/*]
  F --> G[OpenAlex]
  F --> H[Semantic Scholar]
  F --> I[Crossref]
  F --> J[utils/cache]
```

## Sequence (Search request)

```mermaid
sequenceDiagram
  participant Client
  participant MCP as server.py
  participant Tools as tools/search.py
  participant Services as services/openalex.py
  participant Cache as utils/cache.py

  Client->>MCP: search_papers(query)
  MCP->>Tools: validate & orchestrate
  Tools->>Cache: check cache for query
  Cache-->>Tools: hit/miss
  alt cache miss
    Tools->>Services: call OpenAlex / fallback
    Services-->>Tools: normalized response
    Tools->>Cache: store response
  end
  Tools-->>MCP: response
  MCP-->>Client: return results
```

## Notes
- The FastAPI layer shares services and cache so both MCP and HTTP interfaces remain consistent.
- The SQLite cache is intentionally simple and local — it's a performance and rate-limit mitigation, not a canonical datastore.
