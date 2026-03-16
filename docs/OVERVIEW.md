# OVERMIND Mail — System Specification

## What Is This

OVERMIND Mail is a self-hosted email platform with an integrated LLM-powered organisational intelligence layer. It provides full MX capabilities (SMTP, IMAP, DKIM, SPF, DMARC) and continuously analyses all message traffic through a local LLM pipeline to produce structured communication analytics.

## Target Deployment

- Mid-market organisations: 50–2,000 employees
- Single domain or small number of related domains
- Single cloud tenant, operator-controlled — no SaaS, no multi-tenancy
- All LLM inference on-premises or within operator's cloud boundary — no message content leaves infrastructure

## Primary Use Cases

1. **Organisational graph construction** — map actual communication topology against nominal org chart
2. **Information density scoring** — classify messages by informational value (decision, request, status, broadcast noise, social)
3. **Attention cost attribution** — identify individuals/processes imposing disproportionate cognitive load
4. **Automation surface detection** — flag recurring patterns that are candidates for workflow automation
5. **Human refactoring signals** — surface structural communication inefficiencies for management action

## What This Is NOT

- Not a security/threat detection product
- Not a surveillance/individual performance monitoring tool
- Not a SaaS platform — no multi-tenancy, no external data egress

## Architecture Summary

Five independently deployable containerised layers, communicating via NATS JetStream:

| Layer | Responsibility | Key Component |
|-------|---------------|---------------|
| MX/SMTP | Receive/deliver mail, DKIM/SPF/DMARC | Stalwart Mail Server |
| Client Interface | Web, mobile, IMAP/SMTP access | Roundcube Next / Snappymail + React Native |
| Ingestion Pipeline | Parse, normalise, enqueue for LLM | Python (FastAPI + Celery + Redis) |
| LLM Analysis Engine | Classify, score, extract structured data | Ollama + Mistral 7B / Llama 3 (local) |
| Intelligence Store & API | Graph, metrics, dashboard API | PostgreSQL + Apache AGE + FastAPI |

## Specification Index

- [Architecture](architecture/README.md) — system layers, message flow, infrastructure topology
- [Components](components/) — per-component specifications
  - [Mail Server (Stalwart)](components/mail-server.md)
  - [Client Interface](components/client-interface.md)
  - [Ingestion Pipeline](components/ingestion-pipeline.md)
  - [LLM Analysis Engine](components/llm-analysis-engine.md)
  - [Intelligence Store & Graph](components/intelligence-store.md)
  - [Analytics Dashboard](components/analytics-dashboard.md)
- [Data Models](data-models/) — schemas, graph model, classification output
  - [Normalised Message Schema](data-models/normalised-message.md)
  - [LLM Classification Output](data-models/classification-output.md)
  - [Graph Model](data-models/graph-model.md)
  - [Derived Metrics](data-models/derived-metrics.md)
- [Deployment](deployment/) — infrastructure, prerequisites, scaling
  - [Deployment Strategy](deployment/strategy.md) — approach comparison (VPS, hybrid PaaS, Fly.io, self-hosted PaaS)
  - [Infrastructure Topology](deployment/infrastructure.md)
  - [Prerequisites](deployment/prerequisites.md)
  - [OSS Component Register](deployment/oss-components.md)
- [Compliance](compliance/) — privacy, access control, legal
  - [Privacy Architecture](compliance/privacy-architecture.md)
  - [Access Control Model](compliance/access-control.md)
- [Roadmap](roadmap/) — phased build plan
  - [Phase 1: Functional Mail Platform](roadmap/phase-1-mail-platform.md)
  - [Phase 2: Ingestion & LLM](roadmap/phase-2-ingestion-llm.md)
  - [Phase 3: Intelligence & Dashboard](roadmap/phase-3-intelligence-dashboard.md)
  - [Phase 4: Hardening & Extended Analytics](roadmap/phase-4-hardening.md)
- [Open Questions](OPEN-QUESTIONS.md) — unresolved design decisions
- [Excluded Scope](EXCLUDED-SCOPE.md) — explicitly out of scope items
