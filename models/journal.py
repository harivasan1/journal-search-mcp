"""Pydantic model describing a journal (publication source) profile."""

from typing import Optional

from pydantic import BaseModel


class JournalProfile(BaseModel):
    """Journal metadata as returned by search_journal."""

    name: str
    publisher: Optional[str] = None
    issn: Optional[str] = None
    homepage: Optional[str] = None
    works_count: int = 0
    openalex_id: Optional[str] = None
