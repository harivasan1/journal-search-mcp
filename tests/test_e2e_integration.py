from starlette.testclient import TestClient

from fastapi_app import app

client = TestClient(app)


def test_e2e_search_to_export_and_pdf(monkeypatch):
    # Mock OpenAlex search_works and get_work
    monkeypatch.setattr("services.openalex.search_works", lambda **kwargs: [{"title": "FindMe", "doi": "10.1/e2e", "keywords": ["x"]}])
    monkeypatch.setattr("services.openalex.get_work", lambda identifier: {"title": "My Paper", "doi": identifier, "open_access_pdf": "https://example.com/p.pdf"})

    # Mock Semantic Scholar citation and related endpoints
    monkeypatch.setattr("services.semanticscholar.get_paper_by_doi", lambda doi, fields=None: {"title": "My Paper", "citationCount": 1, "referenceCount": 0})
    monkeypatch.setattr("services.semanticscholar.get_citations", lambda doi, limit=20: [{"title": "Cite1", "year": 2020}])
    monkeypatch.setattr("services.semanticscholar.get_references", lambda doi, limit=20: [{"title": "Ref1", "year": 2018}])
    monkeypatch.setattr("services.semanticscholar.get_recommendations", lambda doi, limit=10: [{"title": "Rel1", "year": 2019, "externalIds": {"DOI": "10.1/r"}}])

    # Mock Crossref for export
    monkeypatch.setattr("services.crossref.get_work_by_doi", lambda doi: {"title": ["My Paper"], "author": [{"given": "A", "family": "B"}], "container-title": ["J"], "published": {"date-parts": [[2021]]}, "DOI": doi})
    monkeypatch.setattr("services.crossref.extract_citation_fields", lambda message: {"title": "My Paper", "authors": [{"given": "A", "family": "B"}], "journal": "J", "year": 2021, "doi": message.get("DOI")})

    # 1) Search
    r = client.get("/search", params={"keyword": "FindMe"})
    assert r.status_code == 200
    results = r.json()["results"]
    assert any(p["doi"] == "10.1/e2e" for p in results)

    # 2) Paper details
    r2 = client.get("/paper/10.1%2Fe2e")
    assert r2.status_code == 200
    assert r2.json().get("title") == "My Paper"

    # 3) Citations
    rc = client.get("/citations", params={"doi": "10.1/e2e"})
    assert rc.status_code == 200 and "citing_papers" in rc.json()

    # 4) Related
    rr = client.get("/related", params={"doi": "10.1/e2e"})
    assert rr.status_code == 200 and "related_papers" in rr.json()

    # 5) Export
    rex = client.get("/export", params={"doi": "10.1/e2e", "style": "apa"})
    assert rex.status_code == 200 and "citation" in rex.json()

    # 6) PDF availability
    rpdf = client.get("/pdf", params={"doi": "10.1/e2e"})
    assert rpdf.status_code == 200 and rpdf.json().get("open_access_available") is True


def test_e2e_author_journal_search_and_summary(monkeypatch):
    # Mock author and journal search
    monkeypatch.setattr("services.openalex.search_authors", lambda name, per_page=10: [{"name": "Auth1"}])
    monkeypatch.setattr("services.openalex.search_sources", lambda name, per_page=10: [{"name": "Jour1"}])

    # Mock summary backends
    monkeypatch.setattr("services.semanticscholar.get_paper_by_doi", lambda doi, fields=None: {"title": "T", "abstract": None, "tldr": None})
    monkeypatch.setattr("services.openalex.get_work", lambda doi: {"abstract": "This is an abstract. It has two sentences."})

    ra = client.get("/author", params={"author_name": "Auth1"})
    rj = client.get("/journal", params={"journal_name": "Jour1"})
    assert ra.status_code == 200 and isinstance(ra.json(), list)
    assert rj.status_code == 200 and isinstance(rj.json(), list)

    rs = client.get("/summarize", params={"doi": "10.1/e2e"})
    assert rs.status_code == 200 and "summary" in rs.json()
