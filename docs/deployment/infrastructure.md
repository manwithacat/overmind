# Deployment: Infrastructure Topology

See [Deployment Strategy](strategy.md) for a full comparison of deployment approaches (single VPS, hybrid PaaS, Fly.io, self-hosted PaaS) and platform-specific guidance.

## Minimum Viable Single-Node (≤100 users)

| Resource | Specification |
|----------|--------------|
| Compute | 1× VM: 8 vCPU, 32GB RAM, 500GB SSD (NVMe preferred) |
| LLM Model | Mistral 7B Q4 (Ollama) — fits in 8GB VRAM or runs CPU-only at reduced throughput |
| Database | PostgreSQL 16 with Apache AGE extension |
| Message Bus | NATS JetStream (single node) |
| Container Runtime | Docker Compose (dev) / Kubernetes (production) |
| Reverse Proxy | Caddy (automatic TLS via Let's Encrypt) |

## Scaled Deployment (100–2,000 users)

| Resource | Specification |
|----------|--------------|
| LLM Inference | Dedicated GPU node (RTX 4090 or A10G) running Ollama; horizontally scalable |
| Database | PostgreSQL with read replicas; AGE graph queries isolated to replica |
| Message Bus | NATS JetStream cluster (3 nodes) |
| Worker Pool | Celery workers scaled via Kubernetes HPA based on NATS queue depth |
| Mail Storage | Stalwart with S3-compatible backend (MinIO self-hosted or cloud S3) |

## Container Architecture

All services run as containers orchestrated by Docker Compose (dev/small) or Kubernetes (production).

### Services

| Service | Container | Ports |
|---------|-----------|-------|
| Stalwart Mail | stalwart/mail-server | 25, 587, 993, 8080 (JMAP) |
| Web Client | roundcube-next or snappymail | 8081 (HTTP) |
| NATS JetStream | nats:latest | 4222, 8222 (monitoring) |
| Redis | redis:7 | 6379 |
| PostgreSQL + AGE | postgres-age | 5432 |
| Ollama | ollama/ollama | 11434 |
| Ingestion Workers | custom (Python) | — |
| LLM Analysis Workers | custom (Python) | — |
| Graph Writer | custom (Python) | — |
| Intelligence API | custom (FastAPI) | 8000 |
| Dashboard | custom (React SPA) | — (served by Caddy) |
| Caddy | caddy:2 | 443, 80 |
| MinIO (optional) | minio/minio | 9000, 9001 |

## Network Topology

- Caddy terminates TLS for all HTTPS services (web client, dashboard, API)
- Stalwart handles TLS directly for SMTP/IMAP ports
- All inter-service communication is internal (not exposed to public internet)
- NATS, Redis, PostgreSQL are on internal network only
