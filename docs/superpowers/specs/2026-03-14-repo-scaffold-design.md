# OVERMIND Mail — Repository Scaffold & PoC Design

**Date**: 2026-03-14
**Status**: Approved
**Scope**: GitHub repo creation, project scaffold, Docker Compose PoC with real mail flow

---

## 1. Goals

- Create `manwithacat/overmind` GitHub repository
- Scaffold a fully functional local Docker Compose stack that demonstrates the end-to-end pipeline: real SMTP mail → Stalwart webhook → NATS → ingestion → LLM classification → graph storage → API
- Use LiteLLM for provider-agnostic LLM integration (Anthropic API by default for PoC, swappable to local Ollama)
- Build a Stalwart-to-NATS bridge via Stalwart's HTTP webhook API (Sieve plugin is the production target but requires a Stalwart fork — see Section 5)
- Set up CI/CD via GitHub Actions (lint/test/build on PR, image publish on merge, Dependabot for deps)
- Make the project community-ready: README, CONTRIBUTING, issue templates, BSL-1.1 licence
- Document an OAuth/OIDC provider stretch target for future phases

## 2. Licence

**Business Source Licence 1.1 (BSL-1.1)**

- Source available immediately
- Change licence: Apache-2.0
- Change date: 3 years from each release
- Additional use grant: TBD (e.g., "may be used in production for organisations with fewer than X employees" — common pattern, decision deferred to first release)

**Licensing note on Stalwart integration**: Stalwart is AGPL-3.0. If the production Sieve plugin (Section 5.6) requires forking Stalwart and modifying its source, those modifications fall under AGPL-3.0, not BSL-1.1. The PoC webhook bridge (Section 5) is a standalone service and is covered by BSL-1.1. OVERMIND-authored services (ingestion, classifier, graph-writer, API) are separate works under BSL-1.1.

## 3. Repository Structure

```
manwithacat/overmind
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                          # Lint, type-check, test on PR + push to main
│   │   └── publish.yml                     # Build + push images to ghcr.io on merge to main
│   ├── dependabot.yml                      # Python, Docker, GH Actions, Cargo dep updates
│   └── ISSUE_TEMPLATE/
│       ├── bug_report.yml
│       └── feature_request.yml
├── docs/                                   # Existing spec docs (from prior session)
├── spec/                                   # Original docx (reference)
├── services/
│   ├── mail-bridge/                        # Python: Stalwart webhook → NATS bridge (PoC)
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   └── src/overmind_mail_bridge/
│   │       ├── __init__.py
│   │       └── server.py                   # FastAPI webhook receiver → publishes to NATS
│   ├── stalwart-sieve-nats/                # Rust: Stalwart Sieve plugin (production target)
│   │   ├── Cargo.toml
│   │   ├── src/
│   │   │   └── lib.rs
│   │   └── README.md
│   ├── ingestion/                          # Python: NATS consumer → normalise → publish
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   ├── src/overmind_ingestion/
│   │   │   ├── __init__.py
│   │   │   ├── worker.py                   # NATS async consumer: normalise and publish
│   │   │   ├── parser.py                   # EML parsing, HTML stripping, truncation
│   │   │   └── schemas.py                  # NormalisedMessage Pydantic model
│   │   └── tests/
│   ├── classifier/                         # Python: consume normalised → LiteLLM → publish
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   ├── src/overmind_classifier/
│   │   │   ├── __init__.py
│   │   │   ├── worker.py                   # NATS async consumer: call LLM, publish results
│   │   │   ├── prompts.py                  # System prompt, simplified fallback prompt
│   │   │   └── schemas.py                  # ClassificationOutput Pydantic model
│   │   └── tests/
│   ├── graph-writer/                       # Python: consume results → PostgreSQL/AGE
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   ├── src/overmind_graph_writer/
│   │   │   ├── __init__.py
│   │   │   ├── worker.py                   # NATS async consumer: upsert graph
│   │   │   └── queries.py                  # Cypher queries for node/edge upsert
│   │   └── tests/
│   └── api/                                # FastAPI: intelligence read API
│       ├── Dockerfile
│       ├── pyproject.toml
│       ├── src/overmind_api/
│       │   ├── __init__.py
│       │   ├── main.py                     # FastAPI app, CORS, lifespan
│       │   ├── routers/
│       │   │   ├── graph.py                # /api/v1/graph/persons, threads
│       │   │   └── metrics.py              # /api/v1/metrics/attention-cost, density
│       │   └── db.py                       # PostgreSQL connection pool
│       └── tests/
├── config/
│   ├── stalwart/                           # Stalwart TOML config (webhook to mail-bridge)
│   ├── nats/                               # nats-server.conf with JetStream streams
│   ├── caddy/                              # Caddyfile
│   └── postgres/
│       ├── Dockerfile                      # FROM postgres:16, install AGE from release tarball
│       └── init.sql                        # Create AGE extension, graph schema, tables
├── scripts/
│   ├── Dockerfile                          # python:3.12-slim, installs smtplib deps
│   ├── seed-emails.py                      # Send ~20 sample business emails via SMTP
│   └── seed-data/                          # Sample email content templates (JSON)
├── docker-compose.yml
├── .env.example
├── .gitignore
├── LICENSE.md                              # BSL-1.1
├── README.md
├── CONTRIBUTING.md
├── CLAUDE.md                               # AI agent context (update from existing)
└── pyproject.toml                          # Workspace root: ruff, mypy, pytest config
```

## 4. Docker Compose Services

### 4.1 Service Definitions

| Service | Image | Ports (host) | Depends On | Health Check |
|---------|-------|-------------|------------|-------------|
| `stalwart` | `stalwartlabs/mail-server:v0.10` | 25, 587, 993, 8080 | — | SMTP EHLO on 587 |
| `mail-bridge` | Build `services/mail-bridge/` | 8025 (internal) | nats | HTTP GET `/health` |
| `nats` | `nats:2.10` | 4222, 8222 | — | `/healthz` on 8222 |
| `postgres` | Build `config/postgres/` | 5432 | — | `pg_isready` |
| `ingestion` | Build `services/ingestion/` | — | nats | — |
| `classifier` | Build `services/classifier/` | — | nats | — |
| `graph-writer` | Build `services/graph-writer/` | — | nats, postgres | — |
| `api` | Build `services/api/` | 8000 | postgres | HTTP GET `/health` |
| `caddy` | `caddy:2-alpine` | 80, 443 | stalwart, api | — |
| `seed` | Build `scripts/` | — | stalwart, mail-bridge | Exit 0 (run-once) |

**Removed from PoC**: Redis and Celery. Workers consume NATS directly via `nats.py` (asyncio). This simplifies the architecture — NATS JetStream already provides durable queuing, consumer groups, and redelivery. Redis/Celery would add a redundant queueing layer. If horizontal worker scaling is needed later, NATS consumer groups handle it natively.

### 4.2 PostgreSQL + Apache AGE

Custom Dockerfile at `config/postgres/Dockerfile`:

```dockerfile
FROM postgres:16
# Install AGE from release tarball
RUN apt-get update && apt-get install -y ... && \
    # download and install apache-age-1.5.0
```

The `config/postgres/init.sql` runs on first boot:
- `CREATE EXTENSION IF NOT EXISTS age;`
- `SELECT create_graph('overmind');`
- Create Cypher-accessible node/edge labels (Person, Thread, Topic, SENT_TO, PARTICIPATED_IN, THREAD_REFERENCES)
- Create relational tables for classification storage and materialised views

### 4.3 NATS JetStream Topology

| Stream | Subjects | Purpose | Consumers |
|--------|----------|---------|-----------|
| `MAIL` | `mail.inbound`, `mail.outbound` | Raw messages from Stalwart | `ingestion` service |
| `ANALYSIS` | `mail.analysis.queue` | Normalised messages for LLM | `classifier` service |
| `RESULTS` | `mail.analysis.results` | Classification output | `graph-writer` service |
| `DLQ` | `mail.analysis.dlq` | Failed messages | Monitoring / manual retry |

Each consumer uses a durable consumer group name matching the service name (e.g., consumer group `ingestion` on stream `MAIL`). This ensures at-least-once delivery and allows horizontal scaling by adding more instances of the same service.

Streams are pre-created via NATS server config at `config/nats/nats-server.conf`.

### 4.4 Networking

All services on a single Docker bridge network (`overmind-net`). Exposed to host:
- Stalwart: 25, 587, 993 (mail), 8080 (JMAP)
- Caddy: 80, 443 (HTTPS)
- API: 8000 (development convenience — Caddy proxies in production)
- NATS: 8222 (monitoring dashboard)

### 4.5 Volumes

| Volume | Mount | Purpose |
|--------|-------|---------|
| `stalwart-data` | `/opt/stalwart-mail` | Mail storage (local filesystem for PoC), DKIM keys, config |
| `postgres-data` | `/var/lib/postgresql/data` | Database persistence |
| `nats-data` | `/data` | JetStream persistence |

**MinIO/S3 deferred**: PoC uses local filesystem storage for Stalwart. MinIO as S3-compatible backend is a production concern (see Section 10).

### 4.6 Caddy Routing

| Route | Backend | Purpose |
|-------|---------|---------|
| `localhost/mail/*` | `stalwart:8080` | JMAP web client access |
| `localhost/api/*` | `api:8000` | Intelligence API |
| `localhost:25` | N/A | SMTP handled directly by Stalwart (not proxied) |
| `localhost:587` | N/A | SMTP submission handled directly by Stalwart |
| `localhost:993` | N/A | IMAPS handled directly by Stalwart |

For PoC, Caddy uses self-signed certs (automatic via `tls internal`). No Let's Encrypt — no public domain required.

## 5. Stalwart → NATS Integration

### 5.1 The Problem

Stalwart Mail Server (v0.10.x) does not expose a shared-library plugin API for custom Sieve extensions. There is no documented `.so` plugin loading mechanism. The original spec's `sieve_nats_emit` action cannot be implemented without forking Stalwart's source.

### 5.2 PoC Approach: Webhook Bridge

Stalwart supports HTTP webhooks triggered on mail events. The PoC uses a lightweight `mail-bridge` service:

1. Stalwart configured to POST to `http://mail-bridge:8025/webhook` on every message delivery
2. `mail-bridge` is a FastAPI app that receives the webhook payload (message envelope + content)
3. `mail-bridge` publishes the raw message to NATS subject `mail.inbound`
4. Fire-and-forget from Stalwart's perspective — webhook failure does not block delivery

This is a clean, production-viable approach (many mail systems use webhooks for event emission). It avoids forking Stalwart while providing the same data flow.

### 5.3 Behaviour

- Stalwart POSTs JSON payload on each delivery event
- `mail-bridge` validates the payload, extracts the raw EML
- Publishes to NATS `mail.inbound` with the full EML as payload
- Returns 200 to Stalwart immediately (before NATS publish completes)
- NATS publish failures are logged but do not cause webhook retry storms

### 5.4 PoC Scope

The bridge must:
- Receive Stalwart webhook events reliably
- Publish messages to NATS when mail is delivered
- Handle NATS unavailability gracefully (log and discard)
- Handle inbound delivery events only (outbound deferred)

### 5.5 Configuration

Stalwart config (`config/stalwart/config.toml`):
```toml
[webhook.nats-bridge]
url = "http://mail-bridge:8025/webhook"
events = ["message-ingest"]
```

### 5.6 Production Target: Sieve Plugin (Future)

The long-term goal remains a native Sieve integration for lower latency and tighter coupling. This requires either:
- **(a) Fork Stalwart** — add `nats_emit` as a native Sieve action in the Rust codebase, contribute upstream. Modifications fall under AGPL-3.0.
- **(b) Upstream proposal** — propose a generic Sieve `notify` action to the Stalwart maintainers that supports NATS as a transport.
- **(c) Milter-style sidecar** — if Stalwart adds milter protocol support in a future release.

The `services/stalwart-sieve-nats/` directory contains the Rust crate skeleton for approach (a). It compiles and has tests, but is not wired into the PoC Docker Compose. It serves as a starting point for the production integration.

## 6. LLM Integration via LiteLLM

### 6.1 Provider Abstraction

The classifier service uses LiteLLM's `completion()` function. Provider is configured via environment variable:

```
OVERMIND_LLM_PROVIDER=anthropic/claude-sonnet-4-20250514   # PoC default
OVERMIND_LLM_PROVIDER=ollama/mistral                  # Local inference
OVERMIND_LLM_PROVIDER=openai/gpt-4o-mini              # Alternative
```

Provider-specific API keys are passed via standard env vars (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, etc.) as per LiteLLM convention.

**Privacy note**: The PoC defaults to a cloud LLM API for fast iteration. This violates the production on-premises constraint documented in the system spec (`docs/components/llm-analysis-engine.md`). Before any deployment with real organisational mail data, the provider MUST be switched to a local model (e.g., `ollama/mistral`). The `.env.example` and README will prominently document this.

### 6.2 Classification Prompt

System prompt and output schema are defined in `services/classifier/src/overmind_classifier/prompts.py`. The prompt requests structured JSON output matching the `ClassificationOutput` Pydantic model (see `docs/data-models/classification-output.md`).

### 6.3 Retry Strategy

1. First attempt: full classification prompt (all output fields per ClassificationOutput schema)
2. On Pydantic validation failure: retry with simplified prompt (3 fields: `message_type`, `information_density`, `action_required`)
3. On LLM API error (rate limit, timeout): exponential backoff (3 retries)
4. After all retries exhausted: publish to NATS subject `mail.analysis.dlq` with error metadata

## 7. GitHub Actions

### 7.1 `ci.yml` — PR & Push Validation

```yaml
triggers: push to main, pull_request to main

jobs:
  lint-and-typecheck:
    runs-on: ubuntu-latest
    steps:
      - ruff check (all services)
      - ruff format --check (all services)
      - mypy (all services, using per-service pyproject.toml)

  test-python:
    runs-on: ubuntu-latest
    services:
      postgres (custom AGE image), nats, redis
    steps:
      - pytest services/ingestion
      - pytest services/classifier
      - pytest services/graph-writer
      - pytest services/api

  build-rust:
    runs-on: ubuntu-latest
    steps:
      - cargo check (services/stalwart-sieve-nats)
      - cargo test (services/stalwart-sieve-nats)

  docker-build:
    runs-on: ubuntu-latest
    steps:
      - docker build each service Dockerfile (no push)
```

### 7.2 `publish.yml` — Image Publishing on Merge

```yaml
triggers: push to main (not PRs)

jobs:
  publish-images:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [mail-bridge, ingestion, classifier, graph-writer, api]
    steps:
      - Build services/${{ matrix.service }}
      - Tag: ghcr.io/manwithacat/overmind/${{ matrix.service }}:latest
      - Tag: ghcr.io/manwithacat/overmind/${{ matrix.service }}:sha-${{ github.sha }}
      - Push to GitHub Container Registry

  publish-sieve-plugin:
    runs-on: ubuntu-latest
    steps:
      - cargo build --release (services/stalwart-sieve-nats)
      - Upload .so as release artefact (not used by PoC, available for contributors)
```

### 7.3 `dependabot.yml`

```yaml
updates:
  - package-ecosystem: pip             # Python deps (pyproject.toml), weekly, grouped per service
    directories:
      - /services/ingestion
      - /services/classifier
      - /services/graph-writer
      - /services/api
      - /services/mail-bridge
  - package-ecosystem: docker          # Base image updates, weekly
  - package-ecosystem: github-actions  # Action version updates, weekly
  - package-ecosystem: cargo           # Rust deps, weekly
    directory: /services/stalwart-sieve-nats
```

Note: Dependabot's `pip` ecosystem supports `pyproject.toml` with setuptools/hatchling backends. Each service's `pyproject.toml` declares dependencies in `[project.dependencies]`.

## 8. Community Artefacts

### 8.1 README.md

Sections:
- One-line description + badge row (licence, CI status, ghcr.io)
- Architecture diagram (ASCII)
- **Quickstart**: `git clone` → `cp .env.example .env` → add API key → `docker compose up` → see results
- What you'll see (example API response output)
- Project status (what works, what's planned)
- Link to docs/ for full spec
- Contributing link

### 8.2 CONTRIBUTING.md

- Development setup (Docker Compose for deps, local Python for service dev)
- How to run tests
- PR process
- Good first issues pointer
- Code style (ruff, mypy strict, Pydantic for all schemas)

### 8.3 Issue Templates

- **Bug report**: steps to reproduce, expected vs actual, Docker/OS info
- **Feature request**: use case, proposed approach, which spec section it relates to

## 9. Stretch Target: OIDC Provider

### 9.1 Concept

OVERMIND as an OpenID Connect identity provider — an OVERMIND account provides SSO for external applications willing to participate. "Your org email IS your identity."

### 9.2 Architecture

```
External App                  OVERMIND
    │                            │
    ├─ OIDC Authorization Req ──►│
    │                            ├─ User authenticates against Stalwart credential store
    │◄─ Authorization Code ──────┤
    │                            │
    ├─ Token Exchange ──────────►│
    │◄─ ID Token + Access Token ─┤
    │                            │
    ├─ UserInfo Request ────────►│
    │◄─ Claims (email, name, ──  │
    │   overmind roles)          │
```

### 9.3 Candidate Components

- **Ory Hydra** (Apache-2.0, Go) — headless OAuth2/OIDC server designed to use your existing user database. Stalwart's credential store becomes the identity backend via a thin consent/login app.
- **Authelia** (Apache-2.0, Go) — more opinionated, includes 2FA, portal UI. Heavier but more turnkey.

Recommendation: **Ory Hydra** — minimal surface area, no duplicate user store, well-documented.

### 9.4 Scope

- Not in PoC scope
- Documented here as future Phase 3/4 work
- Interface boundary: a new `services/identity/` service that talks to Stalwart's user store and exposes standard OIDC endpoints
- OVERMIND roles (`mail_user`, `overmind_viewer`, `overmind_admin`) mapped to OIDC scopes/claims

### 9.5 Implications

- Stalwart must be the authoritative user/credential store (already the case in our architecture)
- Password changes in Stalwart automatically apply to OIDC sessions
- 2FA can be added at the OIDC layer without modifying Stalwart

## 10. What Is Explicitly Deferred

| Item | Reason | When |
|------|--------|------|
| React dashboard | Phase 3 deliverable — API-first for PoC | Phase 3 |
| Mobile client | Phase 4 | Phase 4 |
| k-anonymity enforcement | Needs real multi-user data | Phase 4 |
| Deletion API (GDPR) | Needs populated graph | Phase 4 |
| Webhook notifications | Needs running metrics | Phase 4 |
| Kubernetes/Helm | Docker Compose is sufficient for PoC | Phase 4 |
| Outbound mail classification | Legal review pending | Phase 2+ |
| OIDC provider | Stretch target | Phase 3/4 |
| Outbound NATS emission | Inbound only for PoC | Phase 2 |
| MinIO/S3 storage | PoC uses local filesystem for Stalwart | Phase 1 production |
| Native Sieve plugin | Requires Stalwart fork — webhook bridge used for PoC | Phase 2+ |
| Thread/Topic graph nodes | PoC graph writer implements Person + SENT_TO only | Phase 2 |

## 11. Environment Variables

The `.env.example` file contains the following variables:

| Variable | Example Value | Required | Description |
|----------|--------------|----------|-------------|
| `OVERMIND_LLM_PROVIDER` | `anthropic/claude-sonnet-4-20250514` | Yes | LiteLLM model identifier |
| `ANTHROPIC_API_KEY` | `sk-ant-...` | If using Anthropic | Anthropic API key |
| `OPENAI_API_KEY` | `sk-...` | If using OpenAI | OpenAI API key |
| `POSTGRES_USER` | `overmind` | Yes | PostgreSQL username |
| `POSTGRES_PASSWORD` | `overmind-dev` | Yes | PostgreSQL password |
| `POSTGRES_DB` | `overmind` | Yes | PostgreSQL database name |
| `NATS_URL` | `nats://nats:4222` | Yes | NATS connection string |
| `STALWART_ADMIN_USER` | `admin@overmind.local` | Yes | Stalwart admin account |
| `STALWART_ADMIN_PASSWORD` | `admin-dev` | Yes | Stalwart admin password |

## 12. Success Criteria

After scaffold is complete, the following must be true:

- [ ] `manwithacat/overmind` exists on GitHub, public, BSL-1.1 licence
- [ ] `git clone && cp .env.example .env && docker compose up` starts all services
- [ ] Stalwart accepts SMTP connections and delivers mail to test accounts
- [ ] Stalwart webhook fires on delivery, mail-bridge publishes to NATS `mail.inbound`
- [ ] Ingestion worker normalises messages and publishes to `mail.analysis.queue`
- [ ] Classifier calls LiteLLM and publishes valid classification JSON to `mail.analysis.results`
- [ ] Graph writer populates PostgreSQL/AGE with Person nodes and SENT_TO edges
- [ ] `GET localhost:8000/api/v1/graph/persons` returns populated person data
- [ ] `GET localhost:8000/api/v1/metrics/attention-cost` returns computed metrics
- [ ] CI workflow passes (lint, typecheck, test, docker build)
- [ ] README quickstart is accurate and complete
