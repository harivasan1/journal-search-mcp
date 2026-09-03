# Deployment Guide

This project implements a local MCP server over stdio transport and also includes an optional HTTP wrapper for health checks and lightweight web deployment.

## Local MCP (stdio transport)

This is the primary deployment mode for MCP clients such as Claude Desktop or local coding tools.

1. Create and activate a Python virtual environment (Python 3.11+).
2. Install dependencies: `pip install -r requirements.txt`.
3. Optionally copy `.env.example` to `.env` and set `CONTACT_EMAIL` or an optional `SEMANTIC_SCHOLAR_API_KEY`.
4. Start the MCP server: `python server.py`.

This transport is designed for local use and is not intended to be directly exposed on the public internet.

## HTTP wrapper (optional)

The repository also includes `fastapi_app.py`, which exposes the same journal-search logic through a minimal HTTP API for health checks and deployment convenience.

Run locally:

```bash
python -m uvicorn fastapi_app:app --host 127.0.0.1 --port 8000
```

Endpoints include:
- `/health`
- `/ready`
- `/search`
- `/paper/{identifier}`
- `/author`
- `/journal`
- `/citations`
- `/related`
- `/export`
- `/summarize`
- `/pdf`
- `/concepts`

This HTTP layer is not a browser frontend and should not be treated as a public user-facing app by default.

## Docker

Build the image:

```bash
docker build -t journal-search-mcp:latest .
```

Run the container:

```bash
docker run -e CONTACT_EMAIL=you@example.com -p 8000:8000 journal-search-mcp:latest
```

The repository also includes a Compose setup in `docker-compose.yml` for local validation and container testing.

## GitHub Actions

CI workflow steps run:

1. checkout
2. Python setup
3. dependency install
4. Ruff lint
5. Ruff format check
6. pytest
7. Docker build/compose validation

This pipeline is intended to verify code quality and deployment readiness without bypassing failing checks.

## Cloud deployment

For remote deployment, use HTTPS and a reverse proxy or ingress. The MCP stdio server should stay local unless you intentionally run a remote HTTP service behind controlled access.

Recommended pattern:

Local MCP
  ↓
Docker or HTTP wrapper
  ↓
HTTPS reverse proxy / ingress
  ↓
Authentication + access control (if public)
  ↓
Monitoring and health checks

## Monitoring and health checks

- `/health` provides a lightweight status response.
- `/ready` checks the configured upstream research services and returns status details for operational monitoring.
- Use container health checks and upstream service checks for deployment validation.

## Notes

- Keep credentials and `.env` values out of the repository and Docker image.
- Do not expose the local stdio MCP server directly to the public internet.
- Use TLS and network controls before exposing any HTTP endpoint remotely.
