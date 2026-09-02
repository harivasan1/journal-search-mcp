from fastapi.testclient import TestClient
import pytest

from fastapi_app import app
from utils.exceptions import APIRequestError, NotFoundError

client = TestClient(app)


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    payload = r.json()
    assert payload["service"] == "journal-search-mcp"
    assert "endpoints" in payload


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_search_success(monkeypatch):
    # Mock OpenAlex search_works used by tools.search.search_papers
    monkeypatch.setattr("services.openalex.search_works", lambda **kwargs: [{"title": "T", "doi": "10.1/test", "keywords": ["a"]}])
    r = client.get("/search", params={"keyword": "test"})
    assert r.status_code == 200
    data = r.json()
    assert data["query"] == "test"
    assert isinstance(data["results"], list)


def test_search_validation_failure():
    # keyword empty string should be rejected by tool validation
    r = client.get("/search", params={"keyword": "  "})
    assert r.status_code == 400


def test_search_service_failure(monkeypatch):
    monkeypatch.setattr("services.openalex.search_works", lambda **kwargs: (_ for _ in ()).throw(APIRequestError("down")))
    r = client.get("/search", params={"keyword": "test"})
    assert r.status_code == 400


def test_paper_details_success(monkeypatch):
    monkeypatch.setattr("services.openalex.get_work", lambda identifier: {"title": "Paper", "doi": identifier})
    # encode slash in DOI for path parameter
    r = client.get("/paper/10.1%2Ftestdoi")
    assert r.status_code == 200
    assert r.json().get("title") == "Paper"


def test_paper_details_not_found(monkeypatch):
    monkeypatch.setattr("services.openalex.get_work", lambda identifier: (_ for _ in ()).throw(NotFoundError("no")))
    r = client.get("/paper/10.1%2Fmissing")
    assert r.status_code == 400


def test_author_and_journal_endpoints(monkeypatch):
    monkeypatch.setattr("services.openalex.search_authors", lambda name, per_page=10: [{"name": "A"}])
    monkeypatch.setattr("services.openalex.search_sources", lambda name, per_page=10: [{"name": "J"}])
    ra = client.get("/author", params={"author_name": "A"})
    rj = client.get("/journal", params={"journal_name": "J"})
    assert ra.status_code == 200 and isinstance(ra.json(), list)
    assert rj.status_code == 200 and isinstance(rj.json(), list)


def test_citations_and_related(monkeypatch):
    monkeypatch.setattr("services.semanticscholar.get_paper_by_doi", lambda doi, fields=None: {"title": "T", "citationCount": 1, "referenceCount": 0})
    monkeypatch.setattr("services.semanticscholar.get_citations", lambda doi, limit=20: [{"title": "Cite", "year": 2020}])
    monkeypatch.setattr("services.semanticscholar.get_references", lambda doi, limit=20: [{"title": "Ref", "year": 2019}])
    monkeypatch.setattr("services.semanticscholar.get_recommendations", lambda doi, limit=10: [{"title": "Rel", "year": 2018, "externalIds": {"DOI": "10.1/r"}}])

    rc = client.get("/citations", params={"doi": "10.1/test"})
    rr = client.get("/related", params={"doi": "10.1/test"})
    assert rc.status_code == 200 and "citing_papers" in rc.json()
    assert rr.status_code == 200 and "related_papers" in rr.json()


def test_export_and_summarize_and_pdf(monkeypatch):
    # export citation via crossref
    monkeypatch.setattr("services.crossref.get_work_by_doi", lambda doi: {"title": ["T"], "author": [{"given": "J", "family": "D"}], "container-title": ["J"], "published": {"date-parts": [[2020]]}, "DOI": doi})
    monkeypatch.setattr("services.crossref.extract_citation_fields", lambda message: {"title": "T", "authors": [{"given": "J", "family": "D"}], "journal": "J", "year": 2020, "doi": message.get("DOI")})
    r_export = client.get("/export", params={"doi": "10.1/test", "style": "apa"})
    assert r_export.status_code == 200 and "citation" in r_export.json()

    # summarize
    monkeypatch.setattr("services.semanticscholar.get_paper_by_doi", lambda doi, fields=None: {"title": "T", "abstract": "A. B. C.", "tldr": None})
    monkeypatch.setattr("services.openalex.get_work", lambda doi: {"abstract": "An abstract. Sent two."})
    r_sum = client.get("/summarize", params={"doi": "10.1/test"})
    assert r_sum.status_code == 200 and "summary" in r_sum.json()

    # pdf
    monkeypatch.setattr("services.openalex.get_work", lambda doi: {"open_access_pdf": "https://example.com/p.pdf"})
    r_pdf = client.get("/pdf", params={"doi": "10.1/test"})
    assert r_pdf.status_code == 200 and r_pdf.json().get("open_access_available") is True
