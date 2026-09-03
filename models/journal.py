"""Pydantic model describing a journal (publication source) profile."""

from pydantic import BaseModel


class JournalProfile(BaseModel):
    """Journal metadata as returned by search_journal."""

    name: str
    publisher: str | None = None
    issn: str | None = None
    homepage: str | None = None
    works_count: int = 0
    openalex_id: str | None = None
