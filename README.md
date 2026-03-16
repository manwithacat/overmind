# OVERMIND Mail

Self-hosted email platform with LLM-powered organisational intelligence.

[![License: BSL-1.1](https://img.shields.io/badge/License-BSL--1.1-blue.svg)](LICENSE.md)
[![CI](https://github.com/manwithacat/overmind/actions/workflows/ci.yml/badge.svg)](https://github.com/manwithacat/overmind/actions/workflows/ci.yml)

---

## Architecture

```
┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│   Stalwart   │────►│ Mail Bridge │────►│     NATS     │
│  Mail Server │     │  (webhook)  │     │  JetStream   │
└──────────────┘     └─────────────┘     └──────┬───────┘
                                                │
                          ┌─────────────────────┼─────────────────────┐
                          │                     │                     │
                          ▼                     ▼                     ▼
                   ┌─────────────┐     ┌──────────────┐     ┌──────────────┐
                   │  Ingestion  │────►│  Classifier  │────►│ Graph Writer │
                   │   Worker    │     │  (LiteLLM)   │     │ (AGE/Cypher) │
                   └─────────────┘     └──────────────┘     └──────┬───────┘
                                                                   │
                                                                   ▼
                                                          ┌──────────────┐
                                                          │ PostgreSQL   │
                                                          │ + Apache AGE │
                                                          └──────┬───────┘
                                                                 │
                                                                 ▼
                                                          ┌──────────────┐
                                                          │  FastAPI     │
                                                          │  Intel API   │
                                                          └──────────────┘
```

Stalwart receives mail and fires a webhook to the Mail Bridge, which publishes normalised messages onto NATS JetStream. Three workers consume the stream in sequence: **Ingestion** parses and normalises, the **Classifier** extracts entities and intent via an LLM, and the **Graph Writer** persists classification output (never message bodies) into a PostgreSQL + Apache AGE graph. The **FastAPI Intel API** exposes graph queries and derived metrics.

---

## Quickstart

```bash
git clone https://github.com/manwithacat/overmind.git
cd overmind
cp .env.example .env
# Edit .env to add your ANTHROPIC_API_KEY (or switch to ollama/mistral)
docker compose up --build
```

Once all containers are healthy, the Intel API is available at `http://localhost:8000`.

---

## What you'll see

**People discovered from email headers and content:**

```bash
curl http://localhost:8000/api/v1/graph/persons | python -m json.tool
```

```json
{
  "persons": [
    {"id": "p-0a1b", "name": "Alice Chen", "email": "alice@example.com", "message_count": 42},
    {"id": "p-9c3d", "name": "Bob Martinez", "email": "bob@example.com", "message_count": 17}
  ]
}
```

**Attention cost — how much time each topic is consuming:**

```bash
curl http://localhost:8000/api/v1/metrics/attention-cost | python -m json.tool
```

```json
{
  "window_days": 30,
  "topics": [
    {"topic": "Q3 Budget Review", "thread_count": 8, "participant_count": 5, "estimated_hours": 3.2},
    {"topic": "Office Move Logistics", "thread_count": 14, "participant_count": 9, "estimated_hours": 6.7}
  ]
}
```

---

## Privacy note

The default `.env` uses the Anthropic cloud API for convenience during proof-of-concept development. **For production use with real organisational email, switch to a local model** (e.g., `ollama/mistral`) to ensure no message content leaves your infrastructure. Set `OVERMIND_LLM_PROVIDER` in `.env` accordingly.

Message bodies are never stored in the intelligence layer — only classification output (entities, topics, intent).

---

## Project status

**Proof of concept** — the full pipeline works end-to-end:

- Stalwart mail server receiving and storing mail
- Webhook-driven ingestion into NATS JetStream
- LLM classification (entity extraction, topic detection, intent)
- Graph persistence via Apache AGE with Cypher queries
- FastAPI intelligence API serving graph and metric endpoints
- CI pipeline (lint, typecheck, test, Docker build)

**Planned:**

- React analytics dashboard
- k-anonymity enforcement on derived metrics
- OIDC authentication for the API and dashboard
- Production hardening (rate limiting, alerting, backup automation)

---

## Documentation

The full specification lives in [`docs/`](docs/):

| Document | What it covers |
|---|---|
| [Overview](docs/OVERVIEW.md) | System summary and spec index |
| [Architecture](docs/architecture/README.md) | Layers, message flow, NATS topology |
| [Roadmap](docs/roadmap/) | Four-phase delivery plan |
| [Privacy](docs/compliance/privacy-architecture.md) | UK GDPR, data minimisation, DPIA |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on submitting patches and reporting issues.

---

## Licence

[Business Source License 1.1](LICENSE.md) — free for non-production use and production use by organisations with fewer than 50 employees. Converts to Apache 2.0 on the change date (2029-03-14).
