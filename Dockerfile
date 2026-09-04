FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# Standalone healthcheck script — no curl, no heredoc, valid Dockerfile syntax
COPY healthcheck.py /usr/local/bin/healthcheck.py

RUN mkdir -p /data \
    && adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /data

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD ["python", "/usr/local/bin/healthcheck.py"]

CMD ["sh", "-c", "uvicorn fastapi_app:app --host 0.0.0.0 --port ${PORT:-8000}"]