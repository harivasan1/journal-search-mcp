"""
Configuration module for the Journal Search MCP Server.

Loads environment variables (via python-dotenv) and exposes them as
typed module-level constants. Every value has a sensible default so
the server runs out of the box with no .env file required.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ---- Upstream API base URLs (all free, no key required) ----
OPENALEX_BASE_URL = "https://api.openalex.org"
CROSSREF_BASE_URL = "https://api.crossref.org"
SEMANTIC_SCHOLAR_BASE_URL = "https://api.semanticscholar.org/graph/v1"

# ---- Identification ----
# OpenAlex grants higher rate limits ("polite pool") to requests that
# identify a contact email. This is optional but recommended.
CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", "your-email@example.com")

# ---- Optional API keys ----
# Semantic Scholar works without a key; a key just raises rate limits.
SEMANTIC_SCHOLAR_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")

# ---- Networking ----
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "15"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_BACKOFF_FACTOR = float(os.getenv("RETRY_BACKOFF_FACTOR", "0.5"))

# ---- Client-side rate limiting ----
# Minimum seconds between consecutive requests to the same upstream service.
MIN_REQUEST_INTERVAL = float(os.getenv("MIN_REQUEST_INTERVAL", "0.15"))

# ---- Local caching (SQLite) ----
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
CACHE_DB_PATH = os.getenv("CACHE_DB_PATH", "cache.sqlite3")
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))

# ---- Pagination ----
DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE", "10"))
MAX_PAGE_SIZE = int(os.getenv("MAX_PAGE_SIZE", "50"))

# ---- Logging ----
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "journal_search_mcp.log")
