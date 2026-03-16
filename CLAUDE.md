# OVERMIND Mail

## What Is This

OVERMIND Mail is a self-hosted email platform with an LLM-powered organisational intelligence layer. See `docs/OVERVIEW.md` for the full specification index.

## Specification Structure

```
docs/
├── OVERVIEW.md                          # Start here — system summary + index
├── OPEN-QUESTIONS.md                    # Unresolved design decisions
├── EXCLUDED-SCOPE.md                    # Explicitly out of scope
├── architecture/
│   └── README.md                        # Layers, message flow, NATS topology
├── components/
│   ├── mail-server.md                   # Stalwart Mail Server
│   ├── client-interface.md              # Web + mobile + third-party clients
│   ├── ingestion-pipeline.md            # Python/Celery normalisation workers
│   ├── llm-analysis-engine.md           # Ollama + model selection + prompts
│   ├── intelligence-store.md            # PostgreSQL/AGE graph + API
│   └── analytics-dashboard.md           # React dashboard views
├── data-models/
│   ├── normalised-message.md            # Ingestion output schema (Pydantic)
│   ├── classification-output.md         # LLM output schema (Pydantic)
│   ├── graph-model.md                   # Node/edge types + properties
│   └── derived-metrics.md               # Materialised view definitions
├── deployment/
│   ├── strategy.md                      # Deployment approach comparison (VPS, PaaS, hybrid, Fly.io)
│   ├── infrastructure.md                # Topology, containers, scaling
│   ├── prerequisites.md                 # Pre-deployment checklist
│   └── oss-components.md                # Licence + version register
├── compliance/
│   ├── privacy-architecture.md          # UK GDPR, data minimisation, DPIA
│   └── access-control.md               # Roles, k-anonymity, audit log
└── roadmap/
    ├── phase-1-mail-platform.md         # Weeks 1–6: working mail server
    ├── phase-2-ingestion-llm.md         # Weeks 7–12: pipeline + classification
    ├── phase-3-intelligence-dashboard.md # Weeks 13–20: API + dashboard
    └── phase-4-hardening.md             # Weeks 21–28: production hardening
```

## Key Constraints

- All LLM inference must be on-premises — no message content leaves operator infrastructure
- Message body is NOT stored in intelligence layer — only classification output
- UK GDPR compliant — DPIA required, k-anonymity enforced, right to erasure supported
- AGPL-3.0 components (Stalwart, MinIO) — modifications must be released under AGPL

## Tech Stack Summary

Mail: Stalwart | Bus: NATS JetStream | Pipeline: Python/Celery/Redis | LLM: Ollama/Mistral 7B | DB: PostgreSQL + Apache AGE | API: FastAPI | UI: React + Roundcube Next

## Running Tests

Per Python service:
```bash
cd services/<name>
pip install -e ".[dev]"
pytest tests/ -v
```

Rust (stalwart-sieve-nats):
```bash
cd services/stalwart-sieve-nats
cargo test
```

## Docker Compose

```bash
# Full stack
docker compose up --build

# Infrastructure only (Stalwart, NATS, Postgres)
docker compose up -d stalwart nats postgres

# With seed data
docker compose --profile seed up --build

# Clean restart (wipes volumes)
docker compose down -v && docker compose up --build
```

## Service Architecture

| Service | Port | Role |
|---|---|---|
| mail-bridge | 8025 | Receives Stalwart webhook → publishes to NATS |
| ingestion | — | Subscribes `mail.inbound` → normalises → publishes `mail.analysis.queue` |
| classifier | — | Subscribes `mail.analysis.queue` → LiteLLM → publishes `mail.analysis.results` |
| graph-writer | — | Subscribes `mail.analysis.results` → writes to PostgreSQL/AGE |
| api | 8000 | FastAPI read API for graph data and metrics |

## Environment Variables

Copy `.env.example` to `.env` and fill in values before running. See `.env.example` for all required variables.

## Important Conventions

- All Python services use **hatchling** build backend with a `src/` layout.
- AGE Cypher queries use **string interpolation** (NOT parameterised queries) — see `graph-writer/queries.py` for the pattern.
- NATS streams are created **programmatically** at service startup, not via config files.
- The Stalwart webhook event name is `store.ingest` (not `message-ingest`).

Full specs live in `docs/` — see `docs/OVERVIEW.md` for the index.
