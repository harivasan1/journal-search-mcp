import time
import json
import requests
import pytest

from utils import http_client
from utils.exceptions import APIRequestError, NotFoundError, ValidationInputError
from services import openalex, crossref, semanticscholar
from tools import (
    search as search_tool,
    citation as citation_tool,
    pdf as pdf_tool,
    summary as summary_tool,
)
from utils.cache import cache


class FakeResp:
    def __init__(self, status_code=200, json_data=None, raise_exc=None):
        self.status_code = status_code
        self._json = json_data
        self._raise_exc = raise_exc

    def raise_for_status(self):
        if self._raise_exc:
            raise self._raise_exc

    def json(self):
        if isinstance(self._json, Exception):
            raise self._json
        return self._json


def test_get_json_http_errors(monkeypatch):
    codes = [400, 401, 403, 404, 429, 500, 502, 503]
    for code in codes:
        exc = requests.exceptions.HTTPError(f"{code} Client Error")

        def fake_get(url, params=None, headers=None, timeout=None):
            return FakeResp(status_code=code, json_data=None, raise_exc=exc)

        monkeypatch.setattr(http_client._session, "get", fake_get)
        with pytest.raises(APIRequestError):
            http_client.get_json("https://example.invalid", service="test")


def test_get_json_timeout_and_connection(monkeypatch):
    def fake_timeout(url, params=None, headers=None, timeout=None):
        raise requests.exceptions.Timeout("timed out")

    monkeypatch.setattr(http_client._session, "get", fake_timeout)
    with pytest.raises(APIRequestError):
        http_client.get_json("https://example.invalid", service="test")

    def fake_conn(url, params=None, headers=None, timeout=None):
        raise requests.exceptions.ConnectionError("conn fail")

    monkeypatch.setattr(http_client._session, "get", fake_conn)
    with pytest.raises(APIRequestError):
        http_client.get_json("https://example.invalid", service="test")


def test_get_json_malformed_json(monkeypatch):
    def fake_get(url, params=None, headers=None, timeout=None):
        return FakeResp(status_code=200, json_data=ValueError("bad json"))

    monkeypatch.setattr(http_client._session, "get", fake_get)
    with pytest.raises(APIRequestError):
        http_client.get_json("https://example.invalid", service="test")


def test_empty_search_results(monkeypatch):
    monkeypatch.setattr(openalex, "search_works", lambda **kwargs: [])
    res = search_tool.search_papers(keyword="something")
    assert res["result_count"] == 0
    assert res["results"] == []


def test_search_invalid_input():
    with pytest.raises(ValidationInputError):
        search_tool.search_papers(keyword="  ")


def test_paper_details_not_found(monkeypatch):
    monkeypatch.setattr(
        openalex, "get_work", lambda identifier: (_ for _ in ()).throw(NotFoundError("no"))
    )
    with pytest.raises(NotFoundError):
        search_tool.paper_details("10.invalid/doi")


def test_pdf_no_pdf_when_services_fail(monkeypatch):
    # openalex returns no pdf
    monkeypatch.setattr(openalex, "get_work", lambda doi: {"open_access_pdf": None, "doi": doi})
    # semantic scholar fails
    monkeypatch.setattr(
        semanticscholar,
        "get_paper_by_doi",
        lambda doi, fields=None: (_ for _ in ()).throw(APIRequestError("down")),
    )

    res = pdf_tool.open_access_pdf("10.0/testdoi")
    assert res["open_access_available"] is False
    assert "message" in res


def test_cache_hit_and_expiry():
    key = ("get_work", "cache-doi-123")
    cache.set(*key, {"title": "Cached Title"})
    # cache hit
    got = openalex.get_work("cache-doi-123")
    assert got.get("title") == "Cached Title"

    # simulate expiry
    old_ttl = cache.ttl
    try:
        cache.ttl = 0
        cache.set(*key, {"title": "New Title"})
        expired = cache.get(*key)
        assert expired is None
    finally:
        cache.ttl = old_ttl


def test_citation_api_failure(monkeypatch):
    # make paper retrieval succeed
    monkeypatch.setattr(
        semanticscholar,
        "get_paper_by_doi",
        lambda doi, fields=None: {"title": "X", "citationCount": 0, "referenceCount": 0},
    )
    # make citations call fail
    monkeypatch.setattr(
        semanticscholar,
        "get_citations",
        lambda doi, limit=20: (_ for _ in ()).throw(APIRequestError("down")),
    )
    with pytest.raises(APIRequestError):
        citation_tool.get_citations("10.0/testdoi")


def test_export_citation_crossref_unavailable_fallback(monkeypatch):
    # Crossref fails
    monkeypatch.setattr(
        crossref, "get_work_by_doi", lambda doi: (_ for _ in ()).throw(APIRequestError("x"))
    )
    # openalex provides fallback metadata
    monkeypatch.setattr(
        openalex,
        "get_work",
        lambda doi: {"title": "T", "authors": ["Jane Doe"], "journal": "J", "year": 2020},
    )

    res = citation_tool.export_citation("10.0/testdoi", style="apa")
    assert res["doi"] == "10.0/testdoi"
    assert "citation" in res


def test_summary_semantic_scholar_missing_abstract_fallback_to_openalex(monkeypatch):
    # Semantic Scholar returns a paper but without an abstract; OpenAlex provides one
    monkeypatch.setattr(
        semanticscholar,
        "get_paper_by_doi",
        lambda doi, fields=None: {"title": "T", "abstract": None, "tldr": None},
    )
    monkeypatch.setattr(
        openalex, "get_work", lambda doi: {"abstract": "An abstract. This is second sentence."}
    )

    res = summary_tool.summarize_paper("10.0/testdoi")
    assert res["summary_source"] == "abstract_extract"


def test_summary_semantic_scholar_unavailable_raises(monkeypatch):
    # If Semantic Scholar is unavailable at the top-level call, the tool should raise
    monkeypatch.setattr(
        semanticscholar,
        "get_paper_by_doi",
        lambda doi, fields=None: (_ for _ in ()).throw(APIRequestError("down")),
    )
    with pytest.raises(APIRequestError):
        summary_tool.summarize_paper("10.0/testdoi")
