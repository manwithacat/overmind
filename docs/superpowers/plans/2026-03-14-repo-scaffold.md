# OVERMIND Mail — Repository Scaffold & PoC Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold `manwithacat/overmind` with a fully functional Docker Compose PoC where `docker compose up` runs the complete mail → intelligence pipeline.

**Architecture:** Stalwart mail server receives SMTP, fires webhook to a Python bridge service that publishes to NATS JetStream. Three async Python workers (ingestion, classifier, graph-writer) process messages through the pipeline. A FastAPI service exposes the resulting graph data. All orchestrated via Docker Compose.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, nats.py, LiteLLM, PostgreSQL 16 + Apache AGE, NATS JetStream, Stalwart Mail Server, Caddy, Docker Compose, Rust (Sieve plugin skeleton), GitHub Actions, ruff, mypy, pytest.

**Spec:** `docs/superpowers/specs/2026-03-14-repo-scaffold-design.md`

---

## Chunk 1: Repository Initialisation & Infrastructure Config

This chunk creates the GitHub repo, root-level project files, Docker infrastructure configs, and the Docker Compose file. After this chunk, `docker compose up` starts all infrastructure services (Stalwart, NATS, Postgres+AGE, Caddy) with health checks passing, but no custom Python services yet.

### Task 1: Create GitHub repo and initialise git

**Files:**
- Create: `.gitignore`
- Create: `LICENSE.md`
- Create: `.env.example`
- Create: `pyproject.toml` (workspace root)

- [ ] **Step 1: Initialise git repo locally**

```bash
cd /Volumes/SSD/overmind
git init
```

- [ ] **Step 2: Create .gitignore**

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
.venv/
.mypy_cache/
.pytest_cache/
.ruff_cache/

# Rust
services/stalwart-sieve-nats/target/

# Environment
.env

# IDE
.idea/
.vscode/
*.swp

# OS
.DS_Store
Thumbs.db

# Docker volumes (local dev)
data/

# Dev docs
dev_docs/
```

- [ ] **Step 3: Create LICENSE.md (BSL-1.1)**

Use the standard BSL-1.1 template text with:
- Licensor: OVERMIND Mail Contributors
- Licensed Work: OVERMIND Mail
- Change License: Apache License, Version 2.0
- Change Date: 2029-03-14 (3 years from today)
- Additional Use Grant: "You may use the Licensed Work for any non-production purpose. Production use by organisations with fewer than 50 employees is additionally permitted."

- [ ] **Step 4: Create .env.example**

```env
# === LLM Provider Configuration ===
# WARNING: The default uses a cloud API. For production use with real
# organisational email, switch to a local model (e.g., ollama/mistral)
# to ensure no message content leaves your infrastructure.
OVERMIND_LLM_PROVIDER=anthropic/claude-sonnet-4-20250514

# API keys (set the one matching your provider)
ANTHROPIC_API_KEY=sk-ant-your-key-here
# OPENAI_API_KEY=sk-your-key-here

# === PostgreSQL ===
POSTGRES_USER=overmind
POSTGRES_PASSWORD=overmind-dev
POSTGRES_DB=overmind

# === NATS ===
NATS_URL=nats://nats:4222

# === Stalwart Mail Server ===
STALWART_ADMIN_USER=admin@overmind.local
STALWART_ADMIN_PASSWORD=admin-dev

# === Internal service hostnames (Docker Compose networking) ===
POSTGRES_HOST=postgres
```

- [ ] **Step 5: Create root pyproject.toml (workspace tooling config)**

```toml
[project]
name = "overmind"
version = "0.1.0"
description = "Organisational Intelligence Mail Platform"
requires-python = ">=3.12"

[tool.ruff]
target-version = "py312"
line-length = 100
src = ["services/*/src"]

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM", "RUF"]

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.pytest.ini_options]
testpaths = ["services"]
asyncio_mode = "auto"
```

- [ ] **Step 6: Commit initial files**

```bash
git add .gitignore LICENSE.md .env.example pyproject.toml
git commit -m "chore: initialise repository with licence, env template, and tooling config"
```

- [ ] **Step 7: Create the GitHub repository and push**

```bash
gh repo create manwithacat/overmind --public --description "Organisational Intelligence Mail Platform — self-hosted email with LLM-powered communication analytics" --source . --push
```

---

### Task 2: PostgreSQL + Apache AGE Docker image

**Files:**
- Create: `config/postgres/Dockerfile`
- Create: `config/postgres/init.sql`

- [ ] **Step 1: Create Postgres AGE Dockerfile**

```dockerfile
FROM postgres:16

# Install build dependencies for Apache AGE
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libreadline-dev \
    zlib1g-dev \
    flex \
    bison \
    wget \
    postgresql-server-dev-16 \
    && rm -rf /var/lib/apt/lists/*

# Download and install Apache AGE 1.5.0
RUN wget -q https://github.com/apache/age/releases/download/PG16%2Fv1.5.0-rc0/apache-age-1.5.0-src.tar.gz \
    && tar xzf apache-age-1.5.0-src.tar.gz \
    && cd apache-age-1.5.0 \
    && make install \
    && cd .. \
    && rm -rf apache-age-1.5.0 apache-age-1.5.0-src.tar.gz

# Clean up build dependencies
RUN apt-get purge -y --auto-remove \
    build-essential \
    libreadline-dev \
    zlib1g-dev \
    flex \
    bison \
    wget \
    postgresql-server-dev-16
```

- [ ] **Step 2: Create init.sql**

```sql
-- Enable Apache AGE extension
CREATE EXTENSION IF NOT EXISTS age;
LOAD 'age';

-- Set search path to include ag_catalog
SET search_path = ag_catalog, "$user", public;

-- Create the overmind graph
SELECT create_graph('overmind');

-- Create vertex labels (node types)
SELECT create_vlabel('overmind', 'Person');
SELECT create_vlabel('overmind', 'Thread');
SELECT create_vlabel('overmind', 'Topic');

-- Create edge labels
SELECT create_elabel('overmind', 'SENT_TO');
SELECT create_elabel('overmind', 'PARTICIPATED_IN');
SELECT create_elabel('overmind', 'THREAD_REFERENCES');
SELECT create_elabel('overmind', 'REPORTS_TO');

-- Classification results storage (relational, for fast lookup)
CREATE TABLE IF NOT EXISTS classifications (
    id SERIAL PRIMARY KEY,
    message_id TEXT UNIQUE NOT NULL,
    message_type TEXT NOT NULL,
    information_density FLOAT NOT NULL,
    action_required BOOLEAN NOT NULL,
    action_urgency TEXT,
    automation_candidate BOOLEAN NOT NULL,
    automation_type TEXT,
    thread_role TEXT NOT NULL,
    key_entities TEXT[] DEFAULT '{}',
    sentiment_valence TEXT NOT NULL,
    confidence FLOAT NOT NULL,
    classified_at TIMESTAMPTZ DEFAULT NOW()
);

-- Materialised view: attention cost index (placeholder, populated by aggregation job)
CREATE TABLE IF NOT EXISTS metrics_attention_cost (
    person_email TEXT PRIMARY KEY,
    display_name TEXT,
    attention_cost_index FLOAT NOT NULL DEFAULT 0,
    message_count INT NOT NULL DEFAULT 0,
    avg_density FLOAT NOT NULL DEFAULT 0,
    computed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit log (append-only)
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    ts TIMESTAMPTZ DEFAULT NOW(),
    user_id TEXT,
    action TEXT NOT NULL,
    detail JSONB
);
```

- [ ] **Step 3: Verify the Dockerfile builds**

```bash
cd /Volumes/SSD/overmind
docker build -t overmind-postgres config/postgres/
```
Expected: successful build, image tagged `overmind-postgres`.

- [ ] **Step 4: Commit**

```bash
git add config/postgres/
git commit -m "feat: add PostgreSQL + Apache AGE Docker image and schema init"
```

---

### Task 3: NATS JetStream configuration

**Files:**
- Create: `config/nats/nats-server.conf`

- [ ] **Step 1: Create NATS server config with JetStream streams**

```conf
# NATS Server Configuration for OVERMIND
listen: 0.0.0.0:4222

http_port: 8222

jetstream {
    store_dir: /data
    max_mem: 256M
    max_file: 1G
}
```

Note: JetStream streams will be created programmatically by the services on first connection, not via static config. NATS server config only enables JetStream — stream creation is done by the mail-bridge and ingestion services using `nats.py` with `add_stream()` calls. This is the standard NATS pattern and avoids config-based stream definitions which are fragile.

- [ ] **Step 2: Commit**

```bash
git add config/nats/
git commit -m "feat: add NATS JetStream server configuration"
```

---

### Task 4: Caddy reverse proxy configuration

**Files:**
- Create: `config/caddy/Caddyfile`

- [ ] **Step 1: Create Caddyfile**

```caddyfile
{
    # Use self-signed certs for local PoC
    local_certs
}

localhost {
    tls internal

    # JMAP / Stalwart web interface
    handle /mail/* {
        reverse_proxy stalwart:8080
    }

    # Intelligence API
    handle /api/* {
        reverse_proxy api:8000
    }

    # Default: Stalwart web interface
    handle {
        reverse_proxy stalwart:8080
    }
}
```

- [ ] **Step 2: Commit**

```bash
git add config/caddy/
git commit -m "feat: add Caddy reverse proxy configuration"
```

---

### Task 5: Stalwart Mail Server configuration

**Files:**
- Create: `config/stalwart/config.toml`

- [ ] **Step 1: Research Stalwart v0.10 webhook config format**

Check Stalwart docs for the exact webhook configuration syntax. The config needs:
- Local domain: `overmind.local`
- Admin account
- Test user accounts: `alice@overmind.local`, `bob@overmind.local`
- Webhook to fire on `message-ingest` event, POST to `http://mail-bridge:8025/webhook`

- [ ] **Step 2: Create config.toml**

Write the Stalwart configuration based on the v0.10 documentation. Key sections:
- Server listeners (SMTP on 25, Submission on 587, IMAP on 993, JMAP on 8080)
- Local delivery for `overmind.local` domain
- Webhook configuration pointing to mail-bridge
- Admin credentials from environment variables
- Local filesystem storage (no S3 for PoC)

Note: Stalwart's exact config format should be verified against the official documentation at implementation time. The implementer should use `context7` MCP tool to fetch current Stalwart v0.10 docs.

- [ ] **Step 3: Commit**

```bash
git add config/stalwart/
git commit -m "feat: add Stalwart mail server configuration with webhook"
```

---

### Task 6: Docker Compose file

**Files:**
- Create: `docker-compose.yml`

- [ ] **Step 1: Create docker-compose.yml with infrastructure services**

```yaml
services:
  # === Infrastructure Services ===

  stalwart:
    image: stalwartlabs/mail-server:v0.10
    ports:
      - "25:25"
      - "587:587"
      - "993:993"
      - "8080:8080"
    volumes:
      - stalwart-data:/opt/stalwart-mail
      - ./config/stalwart:/opt/stalwart-mail/etc:ro
    environment:
      - STALWART_ADMIN_USER=${STALWART_ADMIN_USER}
      - STALWART_ADMIN_PASSWORD=${STALWART_ADMIN_PASSWORD}
    healthcheck:
      test: ["CMD", "nc", "-z", "localhost", "587"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - overmind-net

  nats:
    image: nats:2.10
    ports:
      - "4222:4222"
      - "8222:8222"
    volumes:
      - nats-data:/data
      - ./config/nats/nats-server.conf:/etc/nats/nats-server.conf:ro
    command: ["-c", "/etc/nats/nats-server.conf"]
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:8222/healthz"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - overmind-net

  postgres:
    build: ./config/postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./config/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - overmind-net

  caddy:
    image: caddy:2-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./config/caddy/Caddyfile:/etc/caddy/Caddyfile:ro
    depends_on:
      stalwart:
        condition: service_healthy
    networks:
      - overmind-net

  # === Application Services (added in subsequent chunks) ===
  # mail-bridge, ingestion, classifier, graph-writer, api, seed

networks:
  overmind-net:
    driver: bridge

volumes:
  stalwart-data:
  postgres-data:
  nats-data:
```

- [ ] **Step 2: Verify infrastructure starts**

```bash
cd /Volumes/SSD/overmind
cp .env.example .env
# Edit .env with a real API key (or leave placeholder for now)
docker compose up -d stalwart nats postgres
docker compose ps
```
Expected: stalwart, nats, postgres all running with healthy status.

- [ ] **Step 3: Verify NATS JetStream is enabled**

```bash
docker compose exec nats nats-server --help 2>&1 | head -5
curl -s http://localhost:8222/jsz | python3 -m json.tool
```
Expected: JetStream info returned.

- [ ] **Step 4: Verify Postgres + AGE extension**

```bash
docker compose exec postgres psql -U overmind -c "SELECT extname FROM pg_extension WHERE extname = 'age';"
```
Expected: `age` in results.

- [ ] **Step 5: Commit**

```bash
git add docker-compose.yml
git commit -m "feat: add Docker Compose with infrastructure services (Stalwart, NATS, Postgres+AGE, Caddy)"
```

- [ ] **Step 6: Push to GitHub**

```bash
git push -u origin main
```

---

## Chunk 2: Mail Bridge & Ingestion Pipeline

This chunk builds the first two Python services: the mail-bridge (Stalwart webhook → NATS) and the ingestion worker (NATS → normalise → NATS). After this chunk, emails delivered to Stalwart appear as normalised JSON messages on the NATS analysis queue.

### Task 7: Shared Python service conventions

Before building individual services, establish the shared patterns. Each Python service follows this structure:
- `pyproject.toml` with hatchling backend, deps in `[project.dependencies]`
- `Dockerfile` based on `python:3.12-slim`
- `src/<package_name>/` layout
- `tests/` with pytest + pytest-asyncio

**Files:**
- Reference only — patterns applied in Tasks 8-12

The standard Dockerfile template for all Python services:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Copy source first — hatchling needs it to build the package
COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir .

CMD ["python", "-m", "<package_name>"]
```

**Important**: hatchling requires the source directory to exist at `pip install` time. Always copy `src/` before `pip install .`.

---

### Task 8: Mail Bridge service

**Files:**
- Create: `services/mail-bridge/pyproject.toml`
- Create: `services/mail-bridge/Dockerfile`
- Create: `services/mail-bridge/src/overmind_mail_bridge/__init__.py`
- Create: `services/mail-bridge/src/overmind_mail_bridge/server.py`
- Create: `services/mail-bridge/src/overmind_mail_bridge/__main__.py`
- Create: `services/mail-bridge/tests/__init__.py`
- Create: `services/mail-bridge/tests/test_server.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "overmind-mail-bridge"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn>=0.34.0",
    "nats-py>=2.9.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.27.0",
]
```

- [ ] **Step 2: Write the failing test**

```python
# services/mail-bridge/tests/test_server.py
import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint():
    from overmind_mail_bridge.server import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_webhook_accepts_valid_payload():
    from overmind_mail_bridge.server import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post("/webhook", json={
            "event": "message-ingest",
            "message": "From: alice@test\nTo: bob@test\nSubject: Hi\n\nHello",
        })
    assert resp.status_code == 200
    assert resp.json()["status"] == "accepted"


@pytest.mark.asyncio
async def test_webhook_rejects_invalid_payload():
    from overmind_mail_bridge.server import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post("/webhook", json={"invalid": "data"})
    assert resp.status_code == 422
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd /Volumes/SSD/overmind/services/mail-bridge
pip install -e ".[dev]"
pytest tests/ -v
```
Expected: FAIL — `overmind_mail_bridge` not found.

- [ ] **Step 4: Implement the mail bridge server**

```python
# services/mail-bridge/src/overmind_mail_bridge/__init__.py
```

```python
# services/mail-bridge/src/overmind_mail_bridge/server.py
import logging
import os

import nats
from fastapi import FastAPI, Request, Response
from pydantic import BaseModel

logger = logging.getLogger(__name__)

app = FastAPI(title="OVERMIND Mail Bridge")

# NATS connection (lazy init)
_nc = None


class WebhookPayload(BaseModel):
    """Stalwart webhook payload for message-ingest events."""
    # Stalwart sends event type and message data
    # Exact fields depend on Stalwart v0.10 webhook format
    # This is a minimal model — extend based on actual Stalwart docs
    event: str
    message: str  # Raw EML as base64 or string


async def get_nats():
    global _nc
    if _nc is None or not _nc.is_connected:
        nats_url = os.environ.get("NATS_URL", "nats://localhost:4222")
        _nc = await nats.connect(nats_url)
        js = _nc.jetstream()
        # Ensure stream exists
        try:
            await js.find_stream_name_by_subject("mail.inbound")
        except nats.js.errors.NotFoundError:
            await js.add_stream(name="MAIL", subjects=["mail.inbound", "mail.outbound"])
    return _nc


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/webhook")
async def webhook(payload: WebhookPayload, response: Response):
    """Receive Stalwart webhook and publish to NATS."""
    if payload.event != "message-ingest":
        return {"status": "ignored", "reason": f"event type {payload.event}"}

    try:
        nc = await get_nats()
        js = nc.jetstream()
        await js.publish("mail.inbound", payload.message.encode())
        logger.info("Published message to mail.inbound")
    except Exception:
        # Fire-and-forget: log but don't fail the webhook
        logger.exception("Failed to publish to NATS")

    return {"status": "accepted"}
```

```python
# services/mail-bridge/src/overmind_mail_bridge/__main__.py
import uvicorn


def main():
    uvicorn.run(
        "overmind_mail_bridge.server:app",
        host="0.0.0.0",
        port=8025,
        log_level="info",
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/ -v
```
Expected: 2 tests PASS.

- [ ] **Step 6: Create Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir .

CMD ["python", "-m", "overmind_mail_bridge"]
```

- [ ] **Step 7: Verify Docker build**

```bash
docker build -t overmind-mail-bridge services/mail-bridge/
```

- [ ] **Step 8: Commit**

```bash
git add services/mail-bridge/
git commit -m "feat: add mail-bridge service (Stalwart webhook → NATS)"
```

---

### Task 9: Ingestion service — Pydantic schemas

**Files:**
- Create: `services/ingestion/pyproject.toml`
- Create: `services/ingestion/src/overmind_ingestion/__init__.py`
- Create: `services/ingestion/src/overmind_ingestion/schemas.py`
- Create: `services/ingestion/tests/__init__.py`
- Create: `services/ingestion/tests/test_schemas.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "overmind-ingestion"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "nats-py>=2.9.0",
    "pydantic>=2.0.0",
    "email-validator>=2.0.0",
    "mail-parser>=3.15.0",
    "beautifulsoup4>=4.12.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
]
```

- [ ] **Step 2: Write the failing test for NormalisedMessage schema**

```python
# services/ingestion/tests/test_schemas.py
from datetime import datetime, timezone


def test_normalised_message_valid():
    from overmind_ingestion.schemas import MessageDirection, NormalisedMessage

    msg = NormalisedMessage(
        message_id="<abc123@overmind.local>",
        thread_id=None,
        sender="alice@overmind.local",
        recipients=["bob@overmind.local"],
        bcc_count=0,
        subject="Test subject",
        body_text="Hello world",
        body_hash="abc123",
        has_attachments=False,
        attachment_types=[],
        received_at=datetime.now(timezone.utc),
        direction=MessageDirection.internal,
    )
    assert msg.message_id == "<abc123@overmind.local>"
    assert msg.direction == MessageDirection.internal


def test_normalised_message_rejects_invalid_direction():
    import pytest
    from pydantic import ValidationError

    from overmind_ingestion.schemas import NormalisedMessage

    with pytest.raises(ValidationError):
        NormalisedMessage(
            message_id="<abc@test>",
            thread_id=None,
            sender="a@b.com",
            recipients=["c@d.com"],
            bcc_count=0,
            subject="x",
            body_text="y",
            body_hash="z",
            has_attachments=False,
            attachment_types=[],
            received_at=datetime.now(timezone.utc),
            direction="invalid",
        )
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd /Volumes/SSD/overmind/services/ingestion
pip install -e ".[dev]"
pytest tests/test_schemas.py -v
```

- [ ] **Step 4: Implement schemas**

```python
# services/ingestion/src/overmind_ingestion/schemas.py
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr


class MessageDirection(str, Enum):
    inbound = "inbound"
    outbound = "outbound"
    internal = "internal"


class NormalisedMessage(BaseModel):
    message_id: str
    thread_id: str | None
    sender: EmailStr
    recipients: list[EmailStr]
    bcc_count: int
    subject: str
    body_text: str
    body_hash: str
    has_attachments: bool
    attachment_types: list[str]
    received_at: datetime
    direction: MessageDirection
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_schemas.py -v
```
Expected: 2 PASS.

- [ ] **Step 6: Commit**

```bash
git add services/ingestion/
git commit -m "feat: add ingestion service scaffold with NormalisedMessage schema"
```

---

### Task 10: Ingestion service — EML parser

**Files:**
- Create: `services/ingestion/src/overmind_ingestion/parser.py`
- Create: `services/ingestion/tests/test_parser.py`
- Create: `services/ingestion/tests/fixtures/sample.eml`

- [ ] **Step 1: Create a sample EML fixture**

```
From: alice@overmind.local
To: bob@overmind.local
Cc: carol@overmind.local
Subject: Q3 Budget Review
Date: Fri, 14 Mar 2026 10:30:00 +0000
Message-ID: <budget-review-001@overmind.local>
In-Reply-To: <budget-thread-001@overmind.local>
MIME-Version: 1.0
Content-Type: text/html; charset="UTF-8"

<html><body><p>Hi Bob,</p><p>Please review the <b>Q3 budget proposal</b> attached. We need sign-off by Friday.</p><p>Thanks,<br/>Alice</p></body></html>
```

- [ ] **Step 2: Write the failing test**

```python
# services/ingestion/tests/test_parser.py
from pathlib import Path


def test_parse_eml_extracts_fields():
    from overmind_ingestion.parser import parse_eml

    eml_path = Path(__file__).parent / "fixtures" / "sample.eml"
    raw = eml_path.read_bytes()
    result = parse_eml(raw)

    assert result.sender == "alice@overmind.local"
    assert "bob@overmind.local" in result.recipients
    assert "carol@overmind.local" in result.recipients
    assert result.subject == "Q3 Budget Review"
    assert result.message_id == "<budget-review-001@overmind.local>"
    assert result.thread_id == "<budget-thread-001@overmind.local>"
    assert "<html>" not in result.body_text  # HTML stripped
    assert "Q3 budget proposal" in result.body_text
    assert result.has_attachments is False
    assert result.bcc_count == 0


def test_parse_eml_truncates_long_body():
    from overmind_ingestion.parser import parse_eml

    # Build an EML with a very long body
    long_body = "word " * 10000
    eml = f"From: a@b.com\nTo: c@d.com\nSubject: Long\nMessage-ID: <long@test>\n\n{long_body}"
    result = parse_eml(eml.encode())
    # Body should be truncated (exact limit depends on token counting, but should be < original)
    assert len(result.body_text) < len(long_body)
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
pytest tests/test_parser.py -v
```

- [ ] **Step 4: Implement parser**

```python
# services/ingestion/src/overmind_ingestion/parser.py
import hashlib
from datetime import datetime, timezone

import mailparser
from bs4 import BeautifulSoup

from .schemas import MessageDirection, NormalisedMessage

MAX_BODY_CHARS = 8192  # ~2048 tokens at ~4 chars/token


def _strip_html(html: str) -> str:
    """Strip HTML tags, return plain text."""
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def _determine_direction(sender: str, recipients: list[str], local_domain: str = "overmind.local") -> MessageDirection:
    sender_internal = sender.endswith(f"@{local_domain}")
    all_recipients_internal = all(r.endswith(f"@{local_domain}") for r in recipients)

    if sender_internal and all_recipients_internal:
        return MessageDirection.internal
    elif sender_internal:
        return MessageDirection.outbound
    else:
        return MessageDirection.inbound


def parse_eml(raw: bytes) -> NormalisedMessage:
    """Parse raw EML bytes into a NormalisedMessage."""
    mail = mailparser.parse_from_bytes(raw)

    # Extract sender
    sender = mail.from_[0][1] if mail.from_ else "unknown@unknown"

    # Extract recipients (To + CC)
    recipients = [addr[1] for addr in (mail.to or [])] + [addr[1] for addr in (mail.cc or [])]

    # Extract body — prefer plain text, fall back to stripped HTML
    body = mail.text_plain[0] if mail.text_plain else ""
    if not body and mail.text_html:
        body = _strip_html(mail.text_html[0])
    body = body[:MAX_BODY_CHARS]

    # Compute body hash
    body_hash = hashlib.sha256(body.encode()).hexdigest()

    # Thread ID from In-Reply-To
    thread_id = mail.message_id if not mail.in_reply_to else mail.in_reply_to[0] if isinstance(mail.in_reply_to, list) else mail.in_reply_to

    # Subject normalisation — strip Re:/Fwd: prefixes for thread grouping
    import re
    subject = mail.subject or ""
    subject = re.sub(r"^(Re|Fwd|Fw)\s*:\s*", "", subject, flags=re.IGNORECASE).strip()

    # Parse date
    received_at = mail.date or datetime.now(timezone.utc)
    if received_at.tzinfo is None:
        received_at = received_at.replace(tzinfo=timezone.utc)

    # Attachments
    has_attachments = len(mail.attachments) > 0
    attachment_types = [att.get("mail_content_type", "application/octet-stream") for att in mail.attachments]

    return NormalisedMessage(
        message_id=mail.message_id or f"<generated-{body_hash[:8]}@overmind>",
        thread_id=thread_id if thread_id != mail.message_id else None,
        sender=sender,
        recipients=recipients,
        bcc_count=0,  # BCC not visible in received mail
        subject=subject,
        body_text=body,
        body_hash=body_hash,
        has_attachments=has_attachments,
        attachment_types=attachment_types,
        received_at=received_at,
        direction=_determine_direction(sender, recipients),
    )
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_parser.py -v
```
Expected: 2 PASS.

- [ ] **Step 6: Commit**

```bash
git add services/ingestion/
git commit -m "feat: add EML parser with HTML stripping and body truncation"
```

---

### Task 11: Ingestion service — NATS worker

**Files:**
- Create: `services/ingestion/src/overmind_ingestion/worker.py`
- Create: `services/ingestion/src/overmind_ingestion/__main__.py`
- Create: `services/ingestion/Dockerfile`
- Create: `services/ingestion/tests/test_worker.py`

- [ ] **Step 1: Write the failing test**

```python
# services/ingestion/tests/test_worker.py
import pytest


@pytest.mark.asyncio
async def test_process_message_returns_normalised():
    from overmind_ingestion.worker import process_message

    eml = (
        b"From: alice@overmind.local\n"
        b"To: bob@overmind.local\n"
        b"Subject: Test\n"
        b"Message-ID: <test-001@overmind.local>\n\n"
        b"Hello Bob, please review the proposal."
    )
    result = await process_message(eml)
    assert result.sender == "alice@overmind.local"
    assert result.message_id == "<test-001@overmind.local>"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_worker.py -v
```

- [ ] **Step 3: Implement worker**

```python
# services/ingestion/src/overmind_ingestion/worker.py
import asyncio
import json
import logging
import os

import nats
from nats.js.api import ConsumerConfig, DeliverPolicy

from .parser import parse_eml
from .schemas import NormalisedMessage

logger = logging.getLogger(__name__)


async def process_message(raw: bytes) -> NormalisedMessage:
    """Parse raw EML and return normalised message."""
    return parse_eml(raw)


async def run():
    """Main worker loop: consume from NATS MAIL stream, normalise, publish to ANALYSIS."""
    nats_url = os.environ.get("NATS_URL", "nats://localhost:4222")
    nc = await nats.connect(nats_url)
    js = nc.jetstream()

    # Ensure streams exist
    try:
        await js.find_stream_name_by_subject("mail.inbound")
    except nats.js.errors.NotFoundError:
        await js.add_stream(name="MAIL", subjects=["mail.inbound", "mail.outbound"])

    try:
        await js.find_stream_name_by_subject("mail.analysis.queue")
    except nats.js.errors.NotFoundError:
        await js.add_stream(name="ANALYSIS", subjects=["mail.analysis.queue"])

    # Subscribe with durable consumer
    sub = await js.pull_subscribe(
        "mail.inbound",
        durable="ingestion",
        config=ConsumerConfig(deliver_policy=DeliverPolicy.ALL),
    )

    logger.info("Ingestion worker started, consuming from mail.inbound")

    while True:
        try:
            msgs = await sub.fetch(batch=10, timeout=5)
            for msg in msgs:
                try:
                    normalised = await process_message(msg.data)
                    payload = normalised.model_dump_json().encode()
                    await js.publish("mail.analysis.queue", payload)
                    await msg.ack()
                    logger.info("Normalised message %s", normalised.message_id)
                except Exception:
                    logger.exception("Failed to process message")
                    await msg.nak()
        except nats.errors.TimeoutError:
            continue  # No messages, loop back
```

```python
# services/ingestion/src/overmind_ingestion/__main__.py
import asyncio
import logging

logging.basicConfig(level=logging.INFO)


def main():
    from .worker import run
    asyncio.run(run())


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/ -v
```
Expected: All tests PASS.

- [ ] **Step 5: Create Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir .

CMD ["python", "-m", "overmind_ingestion"]
```

- [ ] **Step 6: Commit**

```bash
git add services/ingestion/
git commit -m "feat: add ingestion NATS worker with EML normalisation pipeline"
```

---

## Chunk 3: Classifier & Graph Writer

This chunk builds the LLM classification service (LiteLLM integration) and the graph writer (PostgreSQL/AGE). After this chunk, normalised messages on NATS get classified and written to the graph.

### Task 12: Classifier service — schemas and prompts

**Files:**
- Create: `services/classifier/pyproject.toml`
- Create: `services/classifier/src/overmind_classifier/__init__.py`
- Create: `services/classifier/src/overmind_classifier/schemas.py`
- Create: `services/classifier/src/overmind_classifier/prompts.py`
- Create: `services/classifier/tests/__init__.py`
- Create: `services/classifier/tests/test_schemas.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "overmind-classifier"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "nats-py>=2.9.0",
    "pydantic>=2.0.0",
    "litellm>=1.50.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
]
```

- [ ] **Step 2: Write failing test for ClassificationOutput**

```python
# services/classifier/tests/test_schemas.py
def test_classification_output_valid():
    from overmind_classifier.schemas import ClassificationOutput

    output = ClassificationOutput(
        message_type="request",
        information_density=0.7,
        action_required=True,
        action_urgency="this_week",
        automation_candidate=False,
        automation_type=None,
        thread_role="initiating",
        key_entities=["Q3 Budget", "Finance Team"],
        sentiment_valence="neutral",
        confidence=0.85,
    )
    assert output.message_type == "request"
    assert output.action_required is True


def test_classification_output_rejects_out_of_range_density():
    import pytest
    from pydantic import ValidationError

    from overmind_classifier.schemas import ClassificationOutput

    with pytest.raises(ValidationError):
        ClassificationOutput(
            message_type="request",
            information_density=1.5,  # out of range
            action_required=False,
            action_urgency=None,
            automation_candidate=False,
            automation_type=None,
            thread_role="noise",
            key_entities=[],
            sentiment_valence="neutral",
            confidence=0.5,
        )
```

- [ ] **Step 3: Run test, verify fail, implement schemas**

```python
# services/classifier/src/overmind_classifier/schemas.py
from enum import Enum

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    decision = "decision"
    request = "request"
    status_update = "status_update"
    broadcast = "broadcast"
    acknowledgement = "acknowledgement"
    social = "social"
    unknown = "unknown"


class ActionUrgency(str, Enum):
    immediate = "immediate"
    this_week = "this_week"
    no_deadline = "no_deadline"


class ThreadRole(str, Enum):
    initiating = "initiating"
    contributing = "contributing"
    closing = "closing"
    noise = "noise"


class SentimentValence(str, Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"
    urgent = "urgent"


class ClassificationOutput(BaseModel):
    message_type: MessageType
    information_density: float = Field(ge=0.0, le=1.0)
    action_required: bool
    action_urgency: ActionUrgency | None = None
    automation_candidate: bool
    automation_type: str | None = None
    thread_role: ThreadRole
    key_entities: list[str] = Field(default_factory=list)
    sentiment_valence: SentimentValence
    confidence: float = Field(ge=0.0, le=1.0)
```

- [ ] **Step 4: Create prompts.py**

```python
# services/classifier/src/overmind_classifier/prompts.py
SYSTEM_PROMPT = """You are an organisational communication analyst. Given a business email, return a JSON object with the following fields. Return ONLY valid JSON. No explanation, preamble, or markdown fencing.

Fields:
- message_type: one of "decision", "request", "status_update", "broadcast", "acknowledgement", "social", "unknown"
- information_density: float 0-1 (0 = pure noise/acknowledgement, 1 = dense novel information)
- action_required: boolean (true if recipient action is explicitly or implicitly requested)
- action_urgency: one of "immediate", "this_week", "no_deadline", or null (null if action_required is false)
- automation_candidate: boolean (true if the message pattern suggests a human is performing a machine-substitutable task)
- automation_type: string or null (brief label if automation_candidate is true, e.g. "approval routing", "status notification")
- thread_role: one of "initiating", "contributing", "closing", "noise"
- key_entities: list of strings (named entities: projects, systems, external organisations)
- sentiment_valence: one of "positive", "neutral", "negative", "urgent"
- confidence: float 0-1 (your confidence in the classification)"""

SIMPLIFIED_PROMPT = """You are an organisational communication analyst. Given a business email, return a JSON object with ONLY these fields. Return ONLY valid JSON. No explanation.

Fields:
- message_type: one of "decision", "request", "status_update", "broadcast", "acknowledgement", "social", "unknown"
- information_density: float 0-1
- action_required: boolean"""

def build_user_prompt(subject: str, body: str, sender: str, recipients: list[str]) -> str:
    return f"Subject: {subject}\nFrom: {sender}\nTo: {', '.join(recipients)}\n\n{body}"
```

- [ ] **Step 5: Run tests, verify pass, commit**

```bash
pytest tests/ -v
git add services/classifier/
git commit -m "feat: add classifier schemas, prompts, and validation"
```

---

### Task 13: Classifier service — LiteLLM worker

**Files:**
- Create: `services/classifier/src/overmind_classifier/worker.py`
- Create: `services/classifier/src/overmind_classifier/__main__.py`
- Create: `services/classifier/Dockerfile`
- Create: `services/classifier/tests/test_worker.py`

- [ ] **Step 1: Write the failing test (mocking LiteLLM)**

```python
# services/classifier/tests/test_worker.py
import json
from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_classify_message_returns_valid_output():
    from overmind_classifier.worker import classify_message

    mock_response = AsyncMock()
    mock_response.choices = [
        AsyncMock(
            message=AsyncMock(
                content=json.dumps({
                    "message_type": "request",
                    "information_density": 0.7,
                    "action_required": True,
                    "action_urgency": "this_week",
                    "automation_candidate": False,
                    "automation_type": None,
                    "thread_role": "initiating",
                    "key_entities": ["Q3 Budget"],
                    "sentiment_valence": "neutral",
                    "confidence": 0.85,
                })
            )
        )
    ]

    with patch("overmind_classifier.worker.litellm.acompletion", return_value=mock_response):
        result = await classify_message(
            subject="Q3 Budget Review",
            body="Please review the budget proposal.",
            sender="alice@overmind.local",
            recipients=["bob@overmind.local"],
        )

    assert result.message_type == "request"
    assert result.action_required is True
```

- [ ] **Step 2: Run test, verify fail**

- [ ] **Step 3: Implement worker**

```python
# services/classifier/src/overmind_classifier/worker.py
import asyncio
import json
import logging
import os

import litellm
import nats
from nats.js.api import ConsumerConfig, DeliverPolicy
from pydantic import ValidationError

from .prompts import SIMPLIFIED_PROMPT, SYSTEM_PROMPT, build_user_prompt
from .schemas import ClassificationOutput

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


async def classify_message(
    subject: str, body: str, sender: str, recipients: list[str]
) -> ClassificationOutput:
    """Classify a single message via LiteLLM."""
    model = os.environ.get("OVERMIND_LLM_PROVIDER", "anthropic/claude-sonnet-4-20250514")
    user_prompt = build_user_prompt(subject, body, sender, recipients)

    response = await litellm.acompletion(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    raw_json = response.choices[0].message.content
    data = json.loads(raw_json)
    return ClassificationOutput(**data)


async def classify_with_retry(
    subject: str, body: str, sender: str, recipients: list[str]
) -> ClassificationOutput:
    """Classify with fallback to simplified prompt on validation failure."""
    try:
        return await classify_message(subject, body, sender, recipients)
    except (ValidationError, json.JSONDecodeError) as e:
        logger.warning("Full classification failed, trying simplified: %s", e)

    # Simplified fallback
    model = os.environ.get("OVERMIND_LLM_PROVIDER", "anthropic/claude-sonnet-4-20250514")
    user_prompt = build_user_prompt(subject, body, sender, recipients)

    response = await litellm.acompletion(
        model=model,
        messages=[
            {"role": "system", "content": SIMPLIFIED_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    raw_json = response.choices[0].message.content
    data = json.loads(raw_json)
    # Fill in defaults for missing fields
    data.setdefault("action_urgency", None)
    data.setdefault("automation_candidate", False)
    data.setdefault("automation_type", None)
    data.setdefault("thread_role", "noise")
    data.setdefault("key_entities", [])
    data.setdefault("sentiment_valence", "neutral")
    data.setdefault("confidence", 0.5)
    return ClassificationOutput(**data)


async def run():
    """Main worker loop: consume from ANALYSIS stream, classify, publish to RESULTS."""
    nats_url = os.environ.get("NATS_URL", "nats://localhost:4222")
    nc = await nats.connect(nats_url)
    js = nc.jetstream()

    # Ensure streams exist
    try:
        await js.find_stream_name_by_subject("mail.analysis.queue")
    except nats.js.errors.NotFoundError:
        await js.add_stream(name="ANALYSIS", subjects=["mail.analysis.queue"])

    try:
        await js.find_stream_name_by_subject("mail.analysis.results")
    except nats.js.errors.NotFoundError:
        await js.add_stream(name="RESULTS", subjects=["mail.analysis.results"])

    try:
        await js.find_stream_name_by_subject("mail.analysis.dlq")
    except nats.js.errors.NotFoundError:
        await js.add_stream(name="DLQ", subjects=["mail.analysis.dlq"])

    sub = await js.pull_subscribe(
        "mail.analysis.queue",
        durable="classifier",
        config=ConsumerConfig(deliver_policy=DeliverPolicy.ALL),
    )

    logger.info("Classifier worker started, consuming from mail.analysis.queue")

    while True:
        try:
            msgs = await sub.fetch(batch=1, timeout=5)  # Process one at a time (LLM is slow)
            for msg in msgs:
                try:
                    payload = json.loads(msg.data)
                    result = await classify_with_retry(
                        subject=payload["subject"],
                        body=payload["body_text"],
                        sender=payload["sender"],
                        recipients=payload["recipients"],
                    )
                    # Combine message metadata with classification
                    output = {
                        "message_id": payload["message_id"],
                        "sender": payload["sender"],
                        "recipients": payload["recipients"],
                        "classification": result.model_dump(),
                    }
                    await js.publish("mail.analysis.results", json.dumps(output).encode())
                    await msg.ack()
                    logger.info("Classified message %s as %s", payload["message_id"], result.message_type)
                except Exception:
                    logger.exception("Failed to classify message")
                    # Send to DLQ after failure
                    try:
                        await js.publish("mail.analysis.dlq", msg.data)
                    except Exception:
                        logger.exception("Failed to publish to DLQ")
                    await msg.ack()  # Ack to prevent infinite retry
        except nats.errors.TimeoutError:
            continue
```

```python
# services/classifier/src/overmind_classifier/__main__.py
import asyncio
import logging

logging.basicConfig(level=logging.INFO)


def main():
    from .worker import run
    asyncio.run(run())


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests, verify pass**

- [ ] **Step 5: Create Dockerfile, verify build, commit**

```bash
git add services/classifier/
git commit -m "feat: add classifier service with LiteLLM integration and retry logic"
```

---

### Task 14: Graph Writer service

**Files:**
- Create: `services/graph-writer/pyproject.toml`
- Create: `services/graph-writer/src/overmind_graph_writer/__init__.py`
- Create: `services/graph-writer/src/overmind_graph_writer/queries.py`
- Create: `services/graph-writer/src/overmind_graph_writer/worker.py`
- Create: `services/graph-writer/src/overmind_graph_writer/__main__.py`
- Create: `services/graph-writer/Dockerfile`
- Create: `services/graph-writer/tests/__init__.py`
- Create: `services/graph-writer/tests/test_queries.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "overmind-graph-writer"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "nats-py>=2.9.0",
    "psycopg[binary]>=3.2.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
]
```

- [ ] **Step 2: Write failing test for Cypher query generation**

```python
# services/graph-writer/tests/test_queries.py
def test_upsert_person_cypher():
    from overmind_graph_writer.queries import upsert_person_cypher

    sql = upsert_person_cypher("alice@overmind.local", "Alice", "overmind.local", True)
    assert "ag_catalog.cypher" in sql
    assert "MERGE" in sql
    assert "alice@overmind.local" in sql
    assert "true" in sql  # internal flag


def test_upsert_sent_to_cypher():
    from overmind_graph_writer.queries import upsert_sent_to_cypher

    sql = upsert_sent_to_cypher("alice@overmind.local", "bob@overmind.local", 0.7)
    assert "alice@overmind.local" in sql
    assert "bob@overmind.local" in sql
    assert "SENT_TO" in sql


def test_age_escape_handles_quotes():
    from overmind_graph_writer.queries import _age_escape

    assert _age_escape("O'Brien") == "O\\'Brien"
    assert _age_escape("back\\slash") == "back\\\\slash"
```

- [ ] **Step 3: Run tests, verify fail**

- [ ] **Step 4: Implement queries**

```python
# services/graph-writer/src/overmind_graph_writer/queries.py
"""Cypher queries for Apache AGE graph operations.

Apache AGE executes Cypher via ag_catalog.cypher(graph_name, query).
AGE does NOT support Cypher parameterisation through the SQL wrapper —
values must be interpolated into the Cypher string. We use Python string
formatting with proper escaping to prevent injection.

Reference: https://age.apache.org/age-manual/master/intro/agload.html
"""

import json


def _age_escape(value: str) -> str:
    """Escape a string value for embedding in AGE Cypher."""
    return value.replace("\\", "\\\\").replace("'", "\\'")


def upsert_person_cypher(email: str, display_name: str, domain: str, internal: bool) -> str:
    """Generate full SQL to create or update a Person node."""
    e = _age_escape(email)
    dn = _age_escape(display_name)
    d = _age_escape(domain)
    i = "true" if internal else "false"
    return f"""
    SELECT * FROM ag_catalog.cypher('overmind', $$
        MERGE (p:Person {{email: '{e}'}})
        ON CREATE SET p.display_name = '{dn}', p.domain = '{d}',
                      p.internal = {i}, p.first_seen = timestamp(), p.last_seen = timestamp()
        ON MATCH SET p.last_seen = timestamp(), p.display_name = '{dn}'
        RETURN p
    $$) AS (v ag_catalog.agtype);
    """


def upsert_sent_to_cypher(sender: str, recipient: str, density: float) -> str:
    """Generate full SQL to create or update a SENT_TO edge."""
    s = _age_escape(sender)
    r = _age_escape(recipient)
    return f"""
    SELECT * FROM ag_catalog.cypher('overmind', $$
        MATCH (s:Person {{email: '{s}'}}), (r:Person {{email: '{r}'}})
        MERGE (s)-[e:SENT_TO]->(r)
        ON CREATE SET e.count = 1, e.last_at = timestamp(), e.avg_density = {density},
                      e.avg_response_latency_hrs = 0.0
        ON MATCH SET e.count = e.count + 1, e.last_at = timestamp(),
                     e.avg_density = (e.avg_density * (e.count - 1) + {density}) / e.count
        RETURN e
    $$) AS (e ag_catalog.agtype);
    """


def insert_classification_query() -> str:
    """SQL to insert classification result into relational table (uses psycopg parameterisation)."""
    return """
    INSERT INTO classifications (
        message_id, message_type, information_density, action_required,
        action_urgency, automation_candidate, automation_type, thread_role,
        key_entities, sentiment_valence, confidence
    ) VALUES (
        %(message_id)s, %(message_type)s, %(information_density)s, %(action_required)s,
        %(action_urgency)s, %(automation_candidate)s, %(automation_type)s, %(thread_role)s,
        %(key_entities)s, %(sentiment_valence)s, %(confidence)s
    ) ON CONFLICT (message_id) DO NOTHING;
    """


def upsert_attention_cost_query() -> str:
    """SQL to update the attention cost metric for a sender.

    Note: This is an incremental accumulator for the PoC. The production
    version should use a proper 30-day rolling window materialised view
    as specified in docs/data-models/derived-metrics.md.
    """
    return """
    INSERT INTO metrics_attention_cost (person_email, display_name, attention_cost_index, message_count, avg_density)
    VALUES (%(email)s, %(display_name)s, %(cost)s, 1, %(density)s)
    ON CONFLICT (person_email) DO UPDATE SET
        attention_cost_index = metrics_attention_cost.attention_cost_index + %(cost)s,
        message_count = metrics_attention_cost.message_count + 1,
        avg_density = (metrics_attention_cost.avg_density * metrics_attention_cost.message_count + %(density)s)
                      / (metrics_attention_cost.message_count + 1),
        computed_at = NOW();
    """
```

- [ ] **Step 5: Implement worker (NATS consumer → Postgres writes)**

```python
# services/graph-writer/src/overmind_graph_writer/worker.py
import asyncio
import json
import logging
import os

import nats
import psycopg
from nats.js.api import ConsumerConfig, DeliverPolicy

from .queries import (
    insert_classification_query,
    upsert_attention_cost_query,
    upsert_person_cypher,
    upsert_sent_to_cypher,
)

logger = logging.getLogger(__name__)


def get_db_url() -> str:
    user = os.environ.get("POSTGRES_USER", "overmind")
    password = os.environ.get("POSTGRES_PASSWORD", "overmind-dev")
    host = os.environ.get("POSTGRES_HOST", "localhost")
    db = os.environ.get("POSTGRES_DB", "overmind")
    return f"postgresql://{user}:{password}@{host}:5432/{db}"


async def process_result(data: dict, conn) -> None:
    """Write classification result to graph and relational tables."""
    message_id = data["message_id"]
    sender = data["sender"]
    recipients = data["recipients"]
    classification = data["classification"]

    sender_domain = sender.split("@")[1] if "@" in sender else "unknown"
    sender_name = sender.split("@")[0] if "@" in sender else sender
    is_internal = sender_domain == "overmind.local"

    async with conn.cursor() as cur:
        # Set AGE search path
        await cur.execute("LOAD 'age';")
        await cur.execute("SET search_path = ag_catalog, \"$user\", public;")

        # Upsert sender Person node (AGE Cypher — values interpolated, not parameterised)
        await cur.execute(upsert_person_cypher(sender, sender_name, sender_domain, is_internal))

        # Upsert recipient Person nodes and SENT_TO edges
        density = classification.get("information_density", 0.5)
        for recipient in recipients:
            r_domain = recipient.split("@")[1] if "@" in recipient else "unknown"
            r_name = recipient.split("@")[0] if "@" in recipient else recipient
            r_internal = r_domain == "overmind.local"

            await cur.execute(upsert_person_cypher(recipient, r_name, r_domain, r_internal))
            await cur.execute(upsert_sent_to_cypher(sender, recipient, density))

        # Insert classification into relational table
        await cur.execute(insert_classification_query(), {
            "message_id": message_id,
            "message_type": classification["message_type"],
            "information_density": classification["information_density"],
            "action_required": classification["action_required"],
            "action_urgency": classification.get("action_urgency"),
            "automation_candidate": classification["automation_candidate"],
            "automation_type": classification.get("automation_type"),
            "thread_role": classification["thread_role"],
            "key_entities": classification.get("key_entities", []),
            "sentiment_valence": classification["sentiment_valence"],
            "confidence": classification["confidence"],
        })

        # Update attention cost metric
        recipient_count = len(recipients)
        cost = recipient_count * (1.0 - density)
        await cur.execute(upsert_attention_cost_query(), {
            "email": sender,
            "display_name": sender_name,
            "cost": cost,
            "density": density,
        })

    await conn.commit()
    logger.info("Wrote graph data for message %s", message_id)


async def run():
    """Main worker loop."""
    nats_url = os.environ.get("NATS_URL", "nats://localhost:4222")
    nc = await nats.connect(nats_url)
    js = nc.jetstream()

    try:
        await js.find_stream_name_by_subject("mail.analysis.results")
    except nats.js.errors.NotFoundError:
        await js.add_stream(name="RESULTS", subjects=["mail.analysis.results"])

    sub = await js.pull_subscribe(
        "mail.analysis.results",
        durable="graph-writer",
        config=ConsumerConfig(deliver_policy=DeliverPolicy.ALL),
    )

    conn = await psycopg.AsyncConnection.connect(get_db_url(), autocommit=False)

    logger.info("Graph writer started, consuming from mail.analysis.results")

    while True:
        try:
            msgs = await sub.fetch(batch=10, timeout=5)
            for msg in msgs:
                try:
                    data = json.loads(msg.data)
                    await process_result(data, conn)
                    await msg.ack()
                except Exception:
                    logger.exception("Failed to write graph data")
                    await msg.nak()
        except nats.errors.TimeoutError:
            continue
```

- [ ] **Step 6: Create `__main__.py`, Dockerfile**
- [ ] **Step 7: Run tests, verify pass, commit**

```bash
git add services/graph-writer/
git commit -m "feat: add graph-writer service with AGE Cypher queries and attention cost metrics"
```

---

## Chunk 4: API Service & Seed Script

This chunk builds the FastAPI intelligence API and the seed email script. After this chunk, the full pipeline is testable end-to-end.

### Task 15: API service

**Files:**
- Create: `services/api/pyproject.toml`
- Create: `services/api/Dockerfile`
- Create: `services/api/src/overmind_api/__init__.py`
- Create: `services/api/src/overmind_api/main.py`
- Create: `services/api/src/overmind_api/db.py`
- Create: `services/api/src/overmind_api/routers/graph.py`
- Create: `services/api/src/overmind_api/routers/metrics.py`
- Create: `services/api/src/overmind_api/routers/__init__.py`
- Create: `services/api/tests/__init__.py`
- Create: `services/api/tests/test_main.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "overmind-api"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn>=0.34.0",
    "psycopg[binary]>=3.2.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.27.0",
]
```

- [ ] **Step 2: Write failing test for health and persons endpoint**

```python
# services/api/tests/test_main.py
import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_health():
    from overmind_api.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
```

- [ ] **Step 3: Implement API**

`db.py` — async connection pool to Postgres.
`routers/graph.py` — `GET /api/v1/graph/persons` returns persons from AGE graph.
`routers/metrics.py` — `GET /api/v1/metrics/attention-cost` returns from `metrics_attention_cost` table.
`main.py` — FastAPI app, includes routers, CORS middleware, health endpoint.

- [ ] **Step 4: Run tests, create Dockerfile, commit**

```bash
git add services/api/
git commit -m "feat: add FastAPI intelligence API with graph and metrics endpoints"
```

---

### Task 16: Seed emails script

**Files:**
- Create: `scripts/Dockerfile`
- Create: `scripts/seed-emails.py`
- Create: `scripts/seed-data/emails.json`

- [ ] **Step 1: Create sample email data**

`scripts/seed-data/emails.json` — ~20 sample business emails covering all `message_type` categories: decisions, requests, status updates, broadcasts, acknowledgements, social messages. Each entry has: `from`, `to`, `cc` (optional), `subject`, `body`. Realistic corporate tone, referencing fictional projects/people.

- [ ] **Step 2: Create seed script**

```python
# scripts/seed-emails.py
"""Send sample emails to Stalwart via SMTP for PoC demonstration."""
import json
import smtplib
import time
from email.mime.text import MIMEText
from pathlib import Path


def main():
    emails = json.loads((Path(__file__).parent / "seed-data" / "emails.json").read_text())

    # Wait for Stalwart to be ready
    for attempt in range(30):
        try:
            with smtplib.SMTP("stalwart", 25, timeout=5) as smtp:
                smtp.ehlo()
                break
        except (ConnectionRefusedError, OSError):
            print(f"Waiting for Stalwart... (attempt {attempt + 1}/30)")
            time.sleep(2)
    else:
        raise RuntimeError("Stalwart not available after 60 seconds")

    # Send each email
    with smtplib.SMTP("stalwart", 25) as smtp:
        for i, email_data in enumerate(emails):
            msg = MIMEText(email_data["body"])
            msg["Subject"] = email_data["subject"]
            msg["From"] = email_data["from"]
            msg["To"] = email_data["to"]
            if "cc" in email_data:
                msg["Cc"] = email_data["cc"]

            recipients = [email_data["to"]]
            if "cc" in email_data:
                recipients.append(email_data["cc"])

            smtp.sendmail(email_data["from"], recipients, msg.as_string())
            print(f"Sent email {i + 1}/{len(emails)}: {email_data['subject']}")
            time.sleep(0.5)  # Don't overwhelm

    print(f"Done! Sent {len(emails)} seed emails.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Create Dockerfile**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY seed-data/ seed-data/
COPY seed-emails.py .
CMD ["python", "seed-emails.py"]
```

- [ ] **Step 4: Commit**

```bash
git add scripts/
git commit -m "feat: add seed email script with 20 sample business emails"
```

---

### Task 17: Wire all services into Docker Compose

**Files:**
- Modify: `docker-compose.yml`

- [ ] **Step 1: Add all application services to docker-compose.yml**

Add `mail-bridge`, `ingestion`, `classifier`, `graph-writer`, `api`, and `seed` services to the existing `docker-compose.yml`. Each service:
- Builds from its respective directory
- Depends on required infrastructure services
- Receives env vars from `.env`
- Is on the `overmind-net` network

- [ ] **Step 2: Test full stack startup**

```bash
docker compose up --build
```
Expected: All services start, seed emails are sent, pipeline processes them.

- [ ] **Step 3: Verify end-to-end**

```bash
# Check API returns persons
curl -s http://localhost:8000/api/v1/graph/persons | python3 -m json.tool

# Check metrics
curl -s http://localhost:8000/api/v1/metrics/attention-cost | python3 -m json.tool
```

- [ ] **Step 4: Commit**

```bash
git add docker-compose.yml
git commit -m "feat: wire all services into Docker Compose for full end-to-end pipeline"
```

---

## Chunk 5: Rust Sieve Plugin Skeleton, CI/CD & Community Artefacts

This chunk adds the Rust Sieve plugin skeleton (compiles but not wired into PoC), GitHub Actions, Dependabot, README, CONTRIBUTING, issue templates, and the updated CLAUDE.md. After this chunk, the repository is complete and ready for `git push` and community visibility.

### Task 18: Rust Sieve plugin skeleton

**Files:**
- Create: `services/stalwart-sieve-nats/Cargo.toml`
- Create: `services/stalwart-sieve-nats/src/lib.rs`
- Create: `services/stalwart-sieve-nats/README.md`

- [ ] **Step 1: Create Cargo.toml**

Minimal Rust library crate with `nats` client dependency. Targets a future Stalwart plugin API.

- [ ] **Step 2: Create lib.rs with placeholder implementation**

Exports a `publish_to_nats()` function that connects to NATS and publishes a message. Includes unit tests for serialisation logic. The function is callable but not integrated with Stalwart — it's a building block.

- [ ] **Step 3: Create README documenting the production integration path**

Explain the three options (fork, upstream proposal, milter) from spec Section 5.6.

- [ ] **Step 4: Verify it compiles**

```bash
cd services/stalwart-sieve-nats && cargo check && cargo test
```

- [ ] **Step 5: Commit**

```bash
git add services/stalwart-sieve-nats/
git commit -m "feat: add Rust Sieve NATS plugin skeleton (production target, not wired into PoC)"
```

---

### Task 19: GitHub Actions CI workflow

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create ci.yml**

Four jobs: `lint-and-typecheck`, `test-python`, `build-rust`, `docker-build`. Use service containers for Postgres+AGE and NATS in the test job. Pin all action versions.

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add CI workflow (lint, typecheck, test, docker build)"
```

---

### Task 20: GitHub Actions publish workflow

**Files:**
- Create: `.github/workflows/publish.yml`

- [ ] **Step 1: Create publish.yml**

Triggers on push to main. Builds and pushes each service image to `ghcr.io/manwithacat/overmind/<service>`. Tags with `:latest` and `:sha-<commit>`. Builds Rust plugin and uploads `.so` as artefact.

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/publish.yml
git commit -m "ci: add publish workflow (ghcr.io image push on merge to main)"
```

---

### Task 21: Dependabot configuration

**Files:**
- Create: `.github/dependabot.yml`

- [ ] **Step 1: Create dependabot.yml**

Per spec Section 7.3: pip (per service directory), docker, github-actions, cargo.

- [ ] **Step 2: Commit**

```bash
git add .github/dependabot.yml
git commit -m "ci: add Dependabot for Python, Docker, GH Actions, and Cargo deps"
```

---

### Task 22: GitHub issue templates

**Files:**
- Create: `.github/ISSUE_TEMPLATE/bug_report.yml`
- Create: `.github/ISSUE_TEMPLATE/feature_request.yml`

- [ ] **Step 1: Create templates**

Bug report: steps to reproduce, expected/actual, environment info.
Feature request: use case, proposed approach, which spec section.

- [ ] **Step 2: Commit**

```bash
git add .github/ISSUE_TEMPLATE/
git commit -m "chore: add GitHub issue templates for bugs and feature requests"
```

---

### Task 23: README.md

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write README**

Sections per spec Section 8.1:
- One-line description
- Badge row (licence, CI status)
- Architecture diagram (ASCII from spec)
- Quickstart (5 commands)
- What you'll see (example API output)
- Privacy note (cloud API for PoC, switch to local for production)
- Project status (PoC — what works, what's planned)
- Links to docs/ and CONTRIBUTING

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with quickstart, architecture diagram, and project status"
```

---

### Task 24: CONTRIBUTING.md

**Files:**
- Create: `CONTRIBUTING.md`

- [ ] **Step 1: Write CONTRIBUTING.md**

Per spec Section 8.2: dev setup, testing, PR process, code style, good first issues.

- [ ] **Step 2: Commit**

```bash
git add CONTRIBUTING.md
git commit -m "docs: add CONTRIBUTING guide"
```

---

### Task 25: Update CLAUDE.md for implementation context

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update CLAUDE.md**

Add implementation details: how to run tests, Docker Compose commands, service architecture, env var reference. Keep it concise — point to docs/ for full spec.

- [ ] **Step 2: Commit and push**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with implementation context"
git push
```

---

### Task 26: Final verification

- [ ] **Step 1: Clean Docker environment and test from scratch**

```bash
docker compose down -v
docker compose up --build
```

- [ ] **Step 2: Verify all success criteria from spec Section 12**

Walk through each criterion and confirm.

- [ ] **Step 3: Verify CI passes on GitHub**

```bash
gh run list --limit 1
gh run view <run-id>
```

- [ ] **Step 4: Tag and push**

```bash
git tag -a v0.1.0-poc -m "PoC: full mail-to-intelligence pipeline"
git push --tags
```

---

## Implementer Notes

Issues identified during plan review that the implementer should address inline:

1. **Stalwart config (Task 5)**: The plan does not provide a concrete `config.toml`. Use the `context7` MCP tool or Stalwart docs to get the exact v0.10 TOML format for webhook config, user provisioning, and domain setup. This is the most integration-sensitive config in the PoC.

2. **API service (Task 15)**: Code for `db.py`, `routers/graph.py`, `routers/metrics.py` is described in prose. The implementer must write AGE Cypher read queries (for graph endpoint) and standard SQL queries (for metrics endpoint). Use the query patterns from `services/graph-writer/src/overmind_graph_writer/queries.py` as reference.

3. **CI workflows (Tasks 19-20)**: Write real YAML, not pseudo-YAML. Key details: use `actions/checkout@v4`, `actions/setup-python@v5`, `docker/login-action@v3` for ghcr.io, `docker/build-push-action@v6`. For the test job, use GitHub Actions service containers for Postgres+AGE (build the custom image in a prior step) and NATS.

4. **Additional tests to write during implementation**:
   - `test_classify_with_retry` — mock first LLM call returning invalid JSON, verify simplified prompt succeeds
   - `test_process_result` — mock psycopg connection, verify correct queries are called
   - API endpoint tests for `/api/v1/graph/persons` and `/api/v1/metrics/attention-cost`

5. **Postgres connection resilience**: The graph-writer uses a single async connection. Add reconnection logic (try/except around the connection, reconnect on `OperationalError`).

6. **Attention cost metric**: The current implementation is an unbounded accumulator. The spec requires a 30-day rolling window. This is acceptable for PoC but should be documented as a known limitation.

7. **Canonical data model references**: When implementing schemas, cross-check against `docs/data-models/normalised-message.md`, `docs/data-models/classification-output.md`, and `docs/data-models/graph-model.md` as the source of truth.
