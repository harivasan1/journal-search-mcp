"""
Citation formatting utilities.

Converts normalized paper metadata (a dict with title/authors/journal/
year/volume/issue/pages/publisher/doi) into formatted citation strings
for APA, MLA, IEEE, and BibTeX styles.
"""

from typing import Any, Dict, List


def _format_authors_apa(authors: List[Dict[str, str]]) -> str:
    parts = []
    for a in authors:
        family = (a.get("family") or "").strip()
        given = (a.get("given") or "").strip()
        initials = " ".join(f"{p[0]}." for p in given.split() if p)
        if family:
            parts.append(f"{family}, {initials}".strip())
    if not parts:
        return "Unknown Author"
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + ", & " + parts[-1]


def _format_authors_mla(authors: List[Dict[str, str]]) -> str:
    if not authors:
        return "Unknown Author"
    first = authors[0]
    name = f"{first.get('family', '')}, {first.get('given', '')}".strip(", ")
    if len(authors) == 1:
        return name
    return f"{name}, et al."


def _format_authors_ieee(authors: List[Dict[str, str]]) -> str:
    parts = []
    for a in authors:
        given = (a.get("given") or "").strip()
        family = (a.get("family") or "").strip()
        initials = " ".join(f"{p[0]}." for p in given.split() if p)
        parts.append(f"{initials} {family}".strip())
    return ", ".join(p for p in parts if p) or "Unknown Author"


def to_apa(fields: Dict[str, Any]) -> str:
    authors = _format_authors_apa(fields.get("authors", []))
    year = fields.get("year") or "n.d."
    title = fields.get("title") or "Untitled"
    journal = fields.get("journal")
    volume = fields.get("volume")
    issue = fields.get("issue")
    pages = fields.get("pages")
    doi = fields.get("doi")

    citation = f"{authors} ({year}). {title}."
    if journal:
        citation += f" {journal}"
        if volume:
            citation += f", {volume}"
        if issue:
            citation += f"({issue})"
        if pages:
            citation += f", {pages}"
        citation += "."
    if doi:
        citation += f" https://doi.org/{doi}"
    return citation


def to_mla(fields: Dict[str, Any]) -> str:
    authors = _format_authors_mla(fields.get("authors", []))
    title = fields.get("title") or "Untitled"
    journal = fields.get("journal")
    volume = fields.get("volume")
    issue = fields.get("issue")
    year = fields.get("year") or "n.d."
    pages = fields.get("pages")

    citation = f'{authors}. "{title}."'
    if journal:
        citation += f" {journal}"
    if volume:
        citation += f", vol. {volume}"
    if issue:
        citation += f", no. {issue}"
    citation += f", {year}"
    if pages:
        citation += f", pp. {pages}"
    citation += "."
    return citation


def to_ieee(fields: Dict[str, Any]) -> str:
    authors = _format_authors_ieee(fields.get("authors", []))
    title = fields.get("title") or "Untitled"
    journal = fields.get("journal")
    volume = fields.get("volume")
    issue = fields.get("issue")
    pages = fields.get("pages")
    year = fields.get("year") or "n.d."

    citation = f'{authors}, "{title},"'
    if journal:
        citation += f" {journal}"
    if volume:
        citation += f", vol. {volume}"
    if issue:
        citation += f", no. {issue}"
    if pages:
        citation += f", pp. {pages}"
    citation += f", {year}."
    return citation


def to_bibtex(fields: Dict[str, Any]) -> str:
    authors = fields.get("authors", [])
    author_str = (
        " and ".join(f"{a.get('family', '')}, {a.get('given', '')}".strip(", ") for a in authors)
        or "Unknown Author"
    )

    first_author_last = authors[0].get("family", "unknown") if authors else "unknown"
    year = fields.get("year") or "n.d."
    key = f"{first_author_last}{year}".replace(" ", "")

    lines = [f"@article{{{key},"]
    lines.append(f"  title = {{{fields.get('title', 'Untitled')}}},")
    lines.append(f"  author = {{{author_str}}},")
    if fields.get("journal"):
        lines.append(f"  journal = {{{fields['journal']}}},")
    if fields.get("volume"):
        lines.append(f"  volume = {{{fields['volume']}}},")
    if fields.get("issue"):
        lines.append(f"  number = {{{fields['issue']}}},")
    if fields.get("pages"):
        lines.append(f"  pages = {{{fields['pages']}}},")
    lines.append(f"  year = {{{year}}},")
    if fields.get("publisher"):
        lines.append(f"  publisher = {{{fields['publisher']}}},")
    if fields.get("doi"):
        lines.append(f"  doi = {{{fields['doi']}}},")
    lines.append("}")
    return "\n".join(lines)


FORMATTERS = {
    "apa": to_apa,
    "mla": to_mla,
    "ieee": to_ieee,
    "bibtex": to_bibtex,
}


def format_citation(fields: Dict[str, Any], style: str) -> str:
    """Format `fields` into a citation string of the given style."""
    style_key = style.lower().strip()
    formatter = FORMATTERS.get(style_key)
    if not formatter:
        supported = ", ".join(FORMATTERS.keys())
        raise ValueError(f"Unsupported citation style '{style}'. Supported styles: {supported}")
    return formatter(fields)
