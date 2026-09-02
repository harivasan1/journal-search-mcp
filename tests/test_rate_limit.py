import threading
import time
import requests

import pytest

from utils import http_client
from config import MIN_REQUEST_INTERVAL, MAX_RETRIES
from utils.exceptions import APIRequestError


def test_throttle_no_sleep_when_elapsed_large(monkeypatch):
    svc = "test_service_no_sleep"
    now = time.time()
    http_client._last_request_time[svc] = now - (MIN_REQUEST_INTERVAL + 1.0)

    slept = {"called": False}

    def fake_sleep(seconds):
        slept["called"] = True

    monkeypatch.setattr(http_client, "time", time)
    monkeypatch.setattr(http_client, "time", time)
    monkeypatch.setattr(http_client, "time", time)
    monkeypatch.setattr(http_client, "time", time)
    monkeypatch.setattr(time, "sleep", fake_sleep)

    http_client._throttle(svc)
    assert not slept["called"]


def test_throttle_calls_sleep_when_elapsed_small(monkeypatch):
    svc = "test_service_sleep"
    last = time.time()
    http_client._last_request_time[svc] = last

    # Simulate time now being last + (MIN_REQUEST_INTERVAL / 2)
    def fake_time():
        return last + (MIN_REQUEST_INTERVAL / 2)

    slept = {"called_with": None}

    def fake_sleep(seconds):
        slept["called_with"] = seconds

    # Patch the time.time used by the http_client module to our fake_time
    monkeypatch.setattr(http_client.time, "time", fake_time)
    # Patch the global time.sleep function
    monkeypatch.setattr(time, "sleep", fake_sleep)

    http_client._throttle(svc)
    assert slept["called_with"] is not None
    assert pytest.approx(slept["called_with"]) == MIN_REQUEST_INTERVAL / 2


def test_independent_rate_limits(monkeypatch):
    s1 = "svc_one"
    s2 = "svc_two"
    now = time.time()
    http_client._last_request_time[s1] = now
    http_client._last_request_time[s2] = now - (MIN_REQUEST_INTERVAL + 1)

    calls = []

    def fake_sleep(seconds):
        calls.append(seconds)

    monkeypatch.setattr("time.sleep", fake_sleep)

    http_client._throttle(s1)
    http_client._throttle(s2)

    # Only s1 should have triggered a sleep
    assert len(calls) == 1


def test_concurrent_throttle_threads():
    svc = "concurrent_svc"
    http_client._last_request_time.pop(svc, None)

    def worker():
        # calling _throttle concurrently should not raise
        http_client._throttle(svc)

    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # ensure last request time was set
    assert svc in http_client._last_request_time


def test_throttle_updates_time_after_exception(monkeypatch):
    svc = "exc_svc"
    http_client._last_request_time.pop(svc, None)

    # make session.get raise a RequestException
    def fake_get(url, params=None, headers=None, timeout=None):
        raise requests.exceptions.RequestException("network failure")

    monkeypatch.setattr(http_client._session, "get", fake_get)

    before = time.time()
    with pytest.raises(APIRequestError):
        http_client.get_json("https://example.invalid", service=svc)

    assert svc in http_client._last_request_time
    assert http_client._last_request_time[svc] >= before


def test_session_adapter_retries_configured():
    # Inspect the https adapter for retry settings
    adapter = http_client._session.adapters.get("https://")
    # adapter.max_retries may be a Retry object or int depending on requests version
    mr = getattr(adapter, "max_retries", None)
    assert mr is not None
    # If it's a Retry object, check total equals config MAX_RETRIES
    total = getattr(mr, "total", None)
    if total is not None:
        assert total == MAX_RETRIES
