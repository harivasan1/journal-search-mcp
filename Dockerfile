FROM python:3.13-slim

# Container environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY . /app

# Create a non-root user and set permissions (install happens as root above).
# Create a dedicated writable data directory for runtime caches so that
# the non-root `appuser` can write SQLite files and pytest caches even when the
# repository is mounted into /app by docker-compose on developer machines.
RUN mkdir -p /data \
	&& adduser --disabled-password --gecos "" appuser \
	&& chown -R appuser:appuser /data

USER appuser

EXPOSE 8000

# Healthcheck: lightweight Python stdlib HTTP GET to /ready (no curl required)
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python - <<'PY'
import sys, urllib.request
try:
	r = urllib.request.urlopen('http://localhost:8000/ready', timeout=5)
	sys.exit(0 if r.getcode() == 200 else 1)
except Exception:
	sys.exit(1)
PY

# Default command: run the FastAPI app. CI can override to run tests (docker-compose 'tests' service runs pytest).
CMD ["sh", "-c", "uvicorn fastapi_app:app --host 0.0.0.0 --port ${PORT:-8000}"]
