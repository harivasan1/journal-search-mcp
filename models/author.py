"""Pydantic model describing an author profile."""

from pydantic import BaseModel


class AuthorProfile(BaseModel):
    """Author metadata as returned by search_author."""

    name: str
    affiliation: str | None = None
    h_index: int | None = None
    citation_count: int = 0
    works_count: int = 0
    openalex_id: str | None = None
