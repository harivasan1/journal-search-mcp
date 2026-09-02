# Testing Guide

This repository includes unit tests in the `tests/` folder. Tests are written to run offline with mocked HTTP responses.

Running tests

```bash
# from repo root
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
pytest -q
```

Test categories
- Unit: functions in `tools/`, `services/`, and `utils/` are unit tested with mocks.
- Integration-like: tests invoking service logic with recorded responses or network-mocked fixtures.
- Edge cases: rate limits, timeouts, empty responses, and error mapping.

Test files (sample)
- `tests/test_author.py`
- `tests/test_citation.py`
- `tests/test_concepts.py`
- `tests/test_search.py`
- `tests/test_summary.py`
- `tests/test_pdf.py`

Notes
- Tests are designed to be fast and deterministic; they don't hit external APIs.
- If you add new services, add tests that mock HTTP responses using the same pattern as existing tests.
