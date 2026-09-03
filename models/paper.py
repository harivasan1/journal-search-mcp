"""Pydantic models describing academic papers."""

from pydantic import BaseModel, Field


class Paper(BaseModel):
    """Core metadata for a single academic paper, as returned by search_papers."""

    title: str
    authors: list[str] = Field(default_factory=list)
    journal: str | None = None
    year: int | None = None
    doi: str | None = None
    abstract: str | None = None
    citation_count: int = 0
    openalex_id: str | None = None
    url: str | None = None


class PaperDetails(Paper):
    """Extended metadata for a single paper, as returned by paper_details."""

    keywords: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
    related_works: list[str] = Field(default_factory=list)
    open_access_pdf: str | None = None
