FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir .

RUN useradd --create-home appuser
USER appuser

CMD ["python", "-m", "overmind_graph_writer"]
