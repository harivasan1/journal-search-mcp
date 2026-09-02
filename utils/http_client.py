"""
Shared HTTP client used by every service module.

Provides:
- Automatic retries with exponential backoff for transient failures
  (429, 500, 502, 503, 504).
- Request timeouts.
- A simple per-service client-side rate limiter (throttle).
- Consistent error translation into JournalSearchError subclasses.
"""

import threading
import time
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import MAX_RETRIES, MIN_REQUEST_INTERVAL, REQUEST_TIMEOUT, RETRY_BACKOFF_FACTOR
from utils.exceptions import APIRequestError
from utils.logger import get_logger

logger = get_logger(__name__)

_last_request_time: Dict[str, float] = {}
_throttle_lock = threading.Lock()


def _throttle(service: str) -> None:
    """Enforce a minimum interval between consecutive requests to a service."""
    with _throttle_lock:
        last = _last_request_time.get(service, 0.0)
        elapsed = time.time() - last
        if elapsed < MIN_REQUEST_INTERVAL:
            time.sleep(MIN_REQUEST_INTERVAL - elapsed)
        _last_request_time[service] = time.time()


def _build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=MAX_RETRIES,
        backoff_factor=RETRY_BACKOFF_FACTOR,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


_session = _build_session()


def get_json(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    service: str = "default",
) -> Dict[str, Any]:
    """
    Perform a GET request and return the parsed JSON body.

    Applies client-side throttling per `service`, retries transient
    failures, enforces a request timeout, and raises APIRequestError
    on any failure so callers can handle a single error type.
    """
    _throttle(service)
    try:
        response = _session.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout as exc:
        logger.error("Timeout calling %s: %s", url, exc)
        raise APIRequestError(f"Request to {service} timed out.") from exc
    except requests.exceptions.HTTPError as exc:
        logger.error("HTTP error calling %s: %s", url, exc)
        raise APIRequestError(f"{service} returned an error: {exc}") from exc
    except requests.exceptions.RequestException as exc:
        logger.error("Request failed calling %s: %s", url, exc)
        raise APIRequestError(f"Failed to reach {service}: {exc}") from exc
    except ValueError as exc:  # JSON decoding error
        logger.error("Invalid JSON from %s: %s", url, exc)
        raise APIRequestError(f"{service} returned invalid JSON.") from exc
