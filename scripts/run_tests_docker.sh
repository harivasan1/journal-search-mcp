#!/usr/bin/env bash
set -euo pipefail

# Build image and run tests (POSIX)
docker build -t journal-search-tests:latest .
docker run --rm -v "$(pwd)":/app journal-search-tests:latest pytest -q
