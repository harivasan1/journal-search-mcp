"""
Custom exception hierarchy for the Journal Search MCP Server.

Keeping errors in one place lets tools/server.py catch them uniformly
and convert them into clean, user-friendly MCP tool responses instead
of leaking raw tracebacks to the client.
"""


class JournalSearchError(Exception):
    """Base exception for all Journal Search MCP errors."""


class APIRequestError(JournalSearchError):
    """Raised when an upstream API request fails (network, HTTP, or JSON errors)."""


class NotFoundError(JournalSearchError):
    """Raised when a requested resource (paper, author, journal) cannot be found."""


class ValidationInputError(JournalSearchError):
    """Raised when tool input fails validation before any network call is made."""
