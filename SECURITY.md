# Security Guidance

This file highlights security best practices relevant to this repository.

Secrets & environment variables
- Never commit API keys or secrets. Use `.env` locally and environment variables or Secrets management in production.
- `.env.example` documents configurable settings; copy it to `.env` and set values locally.

API keys
- The Semantic Scholar API key is optional and should be set in an environment variable (e.g. `SEMANTIC_SCHOLAR_API_KEY`). Never commit API keys to the repository.

Input validation
- Tools validate inputs at the tool boundary (see `tools/`), and services validate upstream responses.

Logging
- Avoid logging secrets. `utils/logger.py` centralizes logging for consistent levels and formats.

Dependencies
- Keep `requirements.txt` up to date and run dependency scans in CI for vulnerabilities.

Production recommendations
- Run the service behind a reverse proxy or API gateway.
- Use Secrets management for Docker/Kubernetes deployments.
- Monitor rate limits and set up alerting for increased 429 rates.
