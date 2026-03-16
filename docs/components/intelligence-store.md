# Component: Intelligence Store & Graph

## Responsibility

Persist the communication graph, store classification results, maintain materialised metrics, and expose a query interface via the Intelligence API.

## Technology

- **PostgreSQL 16** with **Apache AGE 1.5.x** extension
- Apache AGE provides Cypher query language on top of standard Postgres
- Avoids operational complexity of separate graph database (Neo4j)

## Graph Model

See [Graph Model](../data-models/graph-model.md) for full node/edge type specifications.

### Summary

**Node Types**: Person, Thread, Topic

**Edge Types**: SENT_TO, PARTICIPATED_IN, THREAD_REFERENCES, REPORTS_TO

## Intelligence API

- **Framework**: FastAPI
- **Protocol**: REST, JSON:API compliant
- **Access**: Read-only (no mutations via API — all writes come from pipeline workers)
- **Authentication**: Role-based — see [Access Control](../compliance/access-control.md)

### API Endpoints (indicative)

| Endpoint | Method | Description | Required Role |
|----------|--------|-------------|---------------|
| `/api/v1/graph/persons` | GET | List persons with metrics | OVERMIND_viewer+ |
| `/api/v1/graph/persons/{id}` | GET | Person detail + connections | OVERMIND_viewer+ |
| `/api/v1/graph/persons/{id}/self` | GET | Self-service own metrics | OVERMIND_self |
| `/api/v1/graph/threads` | GET | Thread listing with entropy | OVERMIND_viewer+ |
| `/api/v1/metrics/attention-cost` | GET | Attention cost leaderboard | OVERMIND_viewer+ |
| `/api/v1/metrics/density` | GET | Information density heatmap data | OVERMIND_viewer+ |
| `/api/v1/metrics/automation` | GET | Automation opportunity queue | OVERMIND_viewer+ |
| `/api/v1/metrics/latency` | GET | Response latency map | OVERMIND_viewer+ |
| `/api/v1/messages/{id}/classification` | GET | Per-message classification | OVERMIND_self+ |
| `/api/v1/admin/delete-person/{id}` | DELETE | GDPR erasure | OVERMIND_admin |
| `/api/v1/export/csv/{metric}` | GET | CSV export | OVERMIND_viewer+ |
| `/api/v1/webhooks` | POST/GET/DELETE | Webhook configuration | OVERMIND_admin |

### k-Anonymity Enforcement

For `OVERMIND_viewer` role: individual data is suppressed when the group size is below the k-anonymity threshold (default k=5). Only aggregate/department-level data is returned.

## Materialised View Aggregation

- Runs every 15 minutes as a scheduled job
- See [Derived Metrics](../data-models/derived-metrics.md) for metric definitions

## Retention

- Graph nodes and edges retained for configurable period (default: 24 months rolling)
- Deletion API removes all associated nodes, edges, and materialised metrics for a given person
- Audit log: 12 months, immutable (append-only Postgres table with row-level security)
