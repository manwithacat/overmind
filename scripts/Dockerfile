FROM python:3.12-slim
RUN groupadd --gid 1000 appuser && useradd --uid 1000 --gid 1000 --create-home appuser
WORKDIR /app
COPY seed-data/ seed-data/
COPY seed-emails.py .
USER appuser
CMD ["python", "seed-emails.py"]
