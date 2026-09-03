# Security Guidance

This repository keeps the local MCP stdio server and the optional HTTP wrapper separate. The default deployment mode is local stdio for MCP clients; the FastAPI app is a thin HTTP access layer for health checks and deployment convenience, not a browser-driven frontend.

## 1. Secret management
- Real secrets are never committed to the repository.
- Local configuration is kept in `.env`, which is ignored by Git.
- `.env.example` contains only placeholder values.
- Production deployments should use environment variables or a secret manager instead of baking credentials into the image.
- The Semantic Scholar API key, if configured, is optional and only sent to the Semantic Scholar host.

## 2. Environment variables
- The project reads configuration from environment variables via `config.py`.
- These values are safely defaulted where no secret is required.
- The HTTP wrapper does not expose environment variables in its responses.

## 3. Input validation
- Tool entry points validate required strings and DOI inputs before making network calls.
- Search parameters are constrained by the tool implementations and by the upstream API parameter limits.
- DOI values are normalized by stripping `https://doi.org/` and `http://doi.org/` prefixes before use.
- The project does not accept arbitrary filesystem paths from user input.

## 4. SSRF protection
- The server only targets approved external research APIs: OpenAlex, Crossref, and Semantic Scholar.
- The HTTP client does not accept arbitrary URLs from user input for outbound requests.
- User-controlled values are processed as DOI strings or search text, not as free-form destinations.
- The project does not expose internal services or loopback addresses to untrusted clients.

## 5. External API security
- All outbound HTTP calls use the shared client in `utils/http_client.py`.
- Requests are sent with explicit timeouts and retries for transient failures.
- The client raises API-specific exceptions instead of exposing raw stack traces.
- Secrets are only included when the request is going to the service that expects them.

## 6. Timeout handling
- `REQUEST_TIMEOUT`, `MAX_RETRIES`, and backoff settings are configured in `config.py`.
- The project uses retry logic for transient 429/5xx responses and fails fast on malformed input.

## 7. Error handling
- Tool and service errors are translated into controlled exceptions such as `APIRequestError`, `NotFoundError`, and `ValidationInputError`.
- The MCP server converts these to clean error payloads rather than leaking internal tracebacks to clients.
- The HTTP wrapper converts business errors to HTTP 400 responses and upstream service failures to structured readiness details.

## 8. Logging security
- Logs are centralized in `utils/logger.py`.
- Secrets and authorization headers are not intentionally logged.
- Diagnostic logging is limited to service names and human-readable error messages.

## 9. Docker non-root execution
- The Docker image creates and uses the non-root user `appuser`.
- The application is not run as root in the container.
- The production container does not include the repository’s `.git` metadata or local `.venv` dependencies.

## 10. Dependency security
- Dependencies are kept minimal in `requirements.txt`.
- CI runs linting and tests to catch regressions.
- Dependency vulnerability scanning can be added later if the project grows; this repository does not add large, unnecessary security tooling by default.

## 11. CI security
- GitHub Actions runs the real lint, format, and pytest checks without `continue-on-error`.
- The workflow uses pinned action versions and does not print secrets.
- The project does not disable Ruff rules globally.

## 12. Authentication considerations
- Local MCP usage over stdio is not authenticated by design and does not require an authentication layer.
- The optional HTTP deployment path is not meant to be a public internet API by default.
- If exposed remotely, it should sit behind HTTPS and a reverse proxy, firewall, or gateway that enforces access controls.

## 13. HTTPS requirements for production
- Remote MCP or HTTP access should always use HTTPS in production.
- Do not expose the local stdio server directly over the internet.
- Use a reverse proxy, TLS termination, and access controls for any remote deployment.

## 14. Rate limiting considerations
- The HTTP client enforces lightweight client-side throttling per upstream service.
- This reduces burst traffic and helps avoid abuse or accidental rate-limit spikes.
- The stdio MCP server is local by default and does not need a separate public rate limiter.

## 15. Security reporting procedure
- Report suspected vulnerabilities privately through the project maintainer or repository security contact.
- Do not disclose credentials, tokens, or internal deployment settings in public issues.
- Share the affected component, impact, and reproduction steps in a concise security report.
