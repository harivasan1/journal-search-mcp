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
# Create a non-root user and set permissions (install happens as root above)
# Also create a dedicated writable data directory for runtime caches so that
# non-root `appuser` can write SQLite files and pytest caches even when the
# repository is mounted into /app by docker-compose on developer machines.
RUN mkdir -p /data \
	&& adduser --disabled-password --gecos "" appuser \
	&& chown -R appuser:appuser /app /data

USER appuser

EXPOSE 8000

# Default command: run the FastAPI app. CI can override to run tests (docker-compose 'tests' service runs pytest).
CMD ["uvicorn", "fastapi_app:app", "--host", "0.0.0.0", "--port", "8000"]
