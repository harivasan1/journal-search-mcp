"""Pydantic model describing an author profile."""
from typing import Optional

from pydantic import BaseModel


class AuthorProfile(BaseModel):
    """Author metadata as returned by search_author."""

    name: str
    affiliation: Optional[str] = None
    h_index: Optional[int] = None
    citation_count: int = 0
    works_count: int = 0
    openalex_id: Optional[str] = None
