# Open Source Component Register

## Components

| Component | Licence | Version Target | Notes |
|-----------|---------|---------------|-------|
| Stalwart Mail Server | AGPL-3.0 | 0.10.x | MX/SMTP/IMAP/JMAP |
| PostgreSQL | PostgreSQL Licence | 16.x | Primary database |
| Apache AGE | Apache-2.0 | 1.5.x | Graph extension for PostgreSQL |
| Ollama | MIT | Latest stable | LLM inference runtime |
| Mistral 7B Instruct | Apache-2.0 | v0.3 | Primary LLM model |
| Llama 3.1 8B | Llama 3 Community Licence | 8B Instruct | Alternative LLM model |
| NATS JetStream | Apache-2.0 | 2.10.x | Message bus |
| Celery | BSD-3 | 5.x | Task queue |
| Redis | RSALv2/SSPLv1 (self-host) | 7.x | Celery broker + result backend |
| FastAPI | MIT | 0.115.x | Intelligence API framework |
| Pydantic | MIT | v2 | Schema validation |
| Roundcube Next | GPL-3.0 | dev/main | Web client (primary option) |
| Caddy | Apache-2.0 | 2.x | Reverse proxy, TLS |
| React | MIT | 18.x | Dashboard SPA |
| MinIO | AGPL-3.0 | Latest stable | S3-compatible storage |
| Docker / Kubernetes | Apache-2.0 | — | Container runtime |

## Licensing Notes

**AGPL-3.0 components** (Stalwart, MinIO): modifications to those components must be released under AGPL-3.0.

**OVERMIND-specific components** (ingestion pipeline, LLM engine, intelligence API, dashboard) are separate works and may be licensed independently.

**Recommendation**: Legal review required if commercial distribution of the full stack is intended.
