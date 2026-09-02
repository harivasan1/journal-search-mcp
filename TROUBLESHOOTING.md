# Troubleshooting Guide

Common problems and resolutions when developing or running the server.

1) Port already in use
- Cause: another process (uvicorn, etc.) is using the port.
- Fix: kill the process or change configured port in the `fastapi_app` run command.

2) SQLite locked
- Cause: concurrent processes accessing `cache.sqlite3` incorrectly.
- Fix: ensure single writer pattern, or move to a networked cache for concurrency.

3) Tests failing with network calls
- Cause: tests assume mocked HTTP; if network is allowed, mocks may be bypassed.
- Fix: run tests with the same virtualization (venv) used for development and install test dependencies. Inspect failing test for missing mock fixture.

4) 500 errors from FastAPI endpoints
- Cause: upstream API failures, misconfigured env (CONTACT_EMAIL), or unhandled edge case.
- Fix: check FastAPI logs (console), confirm environment variables, examine `utils/http_client.py` retry and timeout settings.

5) 429 (Rate limited)
- Cause: too many requests to upstream APIs.
- Fix: respect rate-limits, increase cache TTL, add backoff, or obtain higher-rate API keys where supported.
