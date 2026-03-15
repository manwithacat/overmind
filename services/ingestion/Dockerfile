FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir . \
    && addgroup --system app \
    && adduser --system --ingroup app app

USER app

CMD ["python", "-m", "overmind_ingestion"]
