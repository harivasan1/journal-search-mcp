# Deployment Guide

This document explains local and containerized deployment options for the project.

## Local (development)

1. Create and activate a Python virtual environment (Python 3.12+).
2. Install dependencies: `pip install -r requirements.txt`.
3. (Optional) Copy `.env.example` to `.env` and set `CONTACT_EMAIL` and optional `SEMANTIC_SCHOLAR_API_KEY`.
4. Run the MCP server (stdio): `python server.py`.
5. Or run the FastAPI REST wrapper: `python -m uvicorn fastapi_app:app --reload --host 127.0.0.1 --port 8000`

## Docker

Build the Docker image:

```bash
docker build -t journal-search-mcp:latest .
```

Run the container with environment variables (example):

```bash
docker run -e CONTACT_EMAIL=you@example.com -p 8000:8000 journal-search-mcp:latest
```

Compose

`docker-compose.yml` in the repository provides a convenience configuration; run `docker compose up --build` to launch.

## Kubernetes

The `k8s/` folder contains a sample manifest for deployment readiness and health probes. Adapt ConfigMaps and Secrets for production.

## Notes

- Keep API keys and secrets out of the Docker image; pass them as environment variables or Secrets.
