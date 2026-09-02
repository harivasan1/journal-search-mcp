"""Pydantic models describing academic papers."""

from typing import List, Optional

from pydantic import BaseModel, Field


class Paper(BaseModel):
    """Core metadata for a single academic paper, as returned by search_papers."""

    title: str
    authors: List[str] = Field(default_factory=list)
    journal: Optional[str] = None
    year: Optional[int] = None
    doi: Optional[str] = None
    abstract: Optional[str] = None
    citation_count: int = 0
    openalex_id: Optional[str] = None
    url: Optional[str] = None


class PaperDetails(Paper):
    """Extended metadata for a single paper, as returned by paper_details."""

    keywords: List[str] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list)
    related_works: List[str] = Field(default_factory=list)
    open_access_pdf: Optional[str] = None
