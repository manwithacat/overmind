# Deployment Strategy

## The Two-Tier Reality

OVERMIND has two fundamentally different infrastructure profiles:

| Tier | Components | Requirements | PaaS Compatible? |
|------|-----------|-------------|-------------------|
| **Mail Tier** | Stalwart Mail Server | Static IP, PTR/rDNS, ports 25/587/993, persistent storage | No — needs a dedicated VM or bare-metal |
| **Intelligence Tier** | Ingestion workers, LLM engine, graph DB, API, dashboard, NATS, Redis | HTTP only, stateless workers, managed DB possible | Yes — containerised PaaS works well |

**Why mail can't run on Heroku/PaaS**: Mail delivery requires port 25 (blocked on all major PaaS), a static IPv4 with a matching PTR record (essential for deliverability reputation), and persistent IMAP storage. No PaaS platform offers this. This isn't a limitation to work around — it's a hard constraint of email infrastructure.

The intelligence tier, however, is a perfect PaaS candidate: HTTP services, stateless workers, and standard databases.

---

## Recommended Approaches

### Approach A: Single VPS + Docker Compose (Simplest)

Everything on one machine. Best for ≤100 users or initial deployment.

```
┌─────────────────────────────────────────────────┐
│  Single VPS (Hetzner/Vultr/OVH)                 │
│  8 vCPU, 32GB RAM, 500GB NVMe                   │
│                                                  │
│  Docker Compose orchestrates all services:       │
│  ┌──────────┐ ┌──────┐ ┌──────┐ ┌────────────┐ │
│  │ Stalwart │ │ NATS │ │Redis │ │ PostgreSQL │ │
│  │ (mail)   │ │      │ │      │ │ + AGE      │ │
│  └──────────┘ └──────┘ └──────┘ └────────────┘ │
│  ┌──────────┐ ┌──────────────┐ ┌─────────────┐ │
│  │ Ollama   │ │ Celery       │ │ FastAPI     │ │
│  │ (LLM)   │ │ workers (×N) │ │ + React SPA │ │
│  └──────────┘ └──────────────┘ └─────────────┘ │
│  ┌──────┐                                       │
│  │Caddy │ ← TLS termination for HTTPS           │
│  └──────┘                                       │
└─────────────────────────────────────────────────┘
```

**Pros**: Simple to operate, no network latency between services, one bill, one machine to secure.

**Cons**: Single point of failure, LLM competes for CPU/RAM with mail, vertical scaling only.

**Cost estimate**: Hetzner AX42 (dedicated, 8-core Ryzen, 64GB RAM, 2×512GB NVMe) ~€54/month. Vultr bare metal comparable. For GPU: Hetzner GPU servers from ~€150/month.

**VPS providers with good mail reputation** (clean IP ranges, easy PTR setup):
- Hetzner (DE/FI) — best value, PTR via Robot panel
- OVH (FR/CA) — good IP reputation, PTR via API
- Vultr — PTR via dashboard, clean IPs if you verify account
- Contabo — cheap but check IP reputation before committing

**Avoid for mail**: AWS EC2 (port 25 blocked by default, requires request to unblock), GCP (port 25 blocked entirely for new projects), Azure (port 25 blocked on newer deployments).

---

### Approach B: VPS for Mail + PaaS for Intelligence (Hybrid)

Mail on a cheap VPS, intelligence tier on a PaaS platform. Best for teams who want managed infrastructure for the application layer.

```
┌──────────────────────┐          ┌─────────────────────────────┐
│  VPS (Hetzner/OVH)   │          │  PaaS (Railway/Fly.io/      │
│  2 vCPU, 4GB RAM     │          │  Render/Heroku)             │
│                       │          │                              │
│  ┌──────────┐         │  NATS    │  ┌──────────────┐           │
│  │ Stalwart │ ────────┼────────► │  │ Ingestion    │           │
│  │ (mail)   │         │          │  │ workers      │           │
│  └──────────┘         │          │  └──────┬───────┘           │
│  ┌──────┐             │          │         │                    │
│  │Caddy │             │          │  ┌──────▼───────┐           │
│  └──────┘             │          │  │ LLM Engine   │           │
│                       │          │  │ (see note)   │           │
└──────────────────────┘          │  └──────┬───────┘           │
                                   │  ┌──────▼───────┐           │
                                   │  │ Graph Writer  │           │
                                   │  └──────┬───────┘           │
                                   │  ┌──────▼───────┐           │
                                   │  │ API+Dashboard │           │
                                   │  └──────────────┘           │
                                   │                              │
                                   │  Managed services:           │
                                   │  PostgreSQL, Redis, NATS     │
                                   └─────────────────────────────┘
```

**PaaS Platform Comparison**:

| Platform | Docker Containers | Managed Postgres | Private Networking | GPU | Persistent Volume | Good Fit? |
|----------|------------------|-----------------|-------------------|-----|-------------------|-----------|
| **Railway** | Yes | Yes (plugin) | Yes | No | Yes | Good for intelligence tier (no GPU) |
| **Fly.io** | Yes | Yes (Fly Postgres) | Yes (WireGuard) | Yes (A100/L40S) | Yes | Best overall — GPU + containers + private net |
| **Render** | Yes | Yes (managed) | Yes | No | Yes (disk) | Good for intelligence tier (no GPU) |
| **Heroku** | Yes (dynos) | Yes (Heroku Postgres) | No (no private net between dynos) | No | No (ephemeral FS) | Weakest — no GPU, no private net, no volumes |
| **Coolify** | Yes (self-hosted PaaS) | Via Docker | Yes | Via host | Yes | Good if you want PaaS UX on your own hardware |

**LLM inference on PaaS**: Most PaaS platforms lack GPU support. Options:
1. **Fly.io GPU Machines** — A100/L40S available, run Ollama directly
2. **Separate GPU VPS** — Hetzner/Lambda/Vast.ai GPU instance running Ollama, accessed over private network
3. **Cloud LLM API with privacy guarantees** — e.g. Azure OpenAI with data processing agreement (compromises the "no data leaves infrastructure" constraint — operator decision)

**NATS between VPS and PaaS**: The Stalwart-to-NATS connection crosses a network boundary. Options:
- NATS on the PaaS side, Stalwart connects outbound (simpler — outbound from VPS is unrestricted)
- WireGuard tunnel between VPS and PaaS private network (Fly.io supports this natively)
- NATS on VPS, PaaS workers connect inbound (requires exposing NATS port — less ideal)

---

### Approach C: Fly.io All-In (Best PaaS Option)

Fly.io is the strongest PaaS candidate because it offers the closest thing to "Heroku but with real infrastructure":

- **Machines API**: run any Docker container
- **Static IPv4/IPv6**: dedicated IPs available (required for mail PTR)
- **Custom ports**: can expose 25, 587, 993 (unlike Heroku/Railway/Render)
- **GPU Machines**: A100, L40S for LLM inference
- **Fly Postgres**: managed PostgreSQL (though AGE extension availability needs verification)
- **Private networking**: WireGuard mesh between all machines
- **Persistent volumes**: for mail storage if not using S3

```
┌─────────────────────────────────────────────────────┐
│  Fly.io Organisation                                 │
│                                                      │
│  ┌──────────┐  Static IP    ┌──────┐                │
│  │ Stalwart │  + PTR        │ NATS │                │
│  │ Machine  │───────────────│      │                │
│  └──────────┘               └──┬───┘                │
│                                 │  private network   │
│  ┌──────────┐  ┌───────────┐  ┌▼──────────┐        │
│  │ Ollama   │  │ Celery    │  │ PostgreSQL │        │
│  │ GPU      │  │ workers   │  │ + AGE      │        │
│  │ Machine  │  │ (×N)      │  └────────────┘        │
│  └──────────┘  └───────────┘                         │
│  ┌──────────────────────┐                            │
│  │ FastAPI + Dashboard  │  ← public HTTPS            │
│  └──────────────────────┘                            │
└─────────────────────────────────────────────────────┘
```

**Caveat**: Running a mail server on Fly.io is possible but unconventional. Deliverability reputation depends on IP cleanliness — Fly's IP ranges may not have the same reputation as dedicated mail hosting IPs. Test thoroughly before committing.

**Caveat**: Fly Postgres is community-maintained and doesn't support AGE out of the box. You'd need a custom Postgres Docker image with AGE installed, running on a Fly Machine with a persistent volume.

---

### Approach D: Coolify / CapRover (Self-Hosted PaaS)

If you want the PaaS developer experience but on your own hardware (keeping the "all data on operator infrastructure" promise clean):

- **Coolify** — open-source, self-hosted PaaS (Heroku-like UI, Docker-based)
- **CapRover** — similar, slightly more mature

Deploy Coolify on a VPS, then deploy all OVERMIND services through its UI. You get:
- Git push to deploy
- Automatic TLS (Let's Encrypt)
- Service scaling via UI
- Log aggregation
- One-click database provisioning

This preserves the single-VPS simplicity of Approach A but adds PaaS ergonomics for the development team.

---

## Recommendation Matrix

| Scenario | Recommended Approach |
|----------|---------------------|
| Solo developer / MVP / ≤50 users | **A** — Single VPS + Docker Compose |
| Small team, want managed services, ≤100 users | **B** — VPS (mail) + Railway or Render (intelligence) |
| Need GPU on PaaS, want single platform | **C** — Fly.io all-in |
| Must keep all data on own infrastructure + want PaaS UX | **D** — Coolify on dedicated server |
| 100–2,000 users, production | **A** scaled to multiple VPS, or Kubernetes on bare metal |

## Docker Compose as the Universal Artefact

Regardless of deployment target, **Docker Compose is the canonical service definition**. All approaches above consume the same container images:

- Approach A runs `docker compose up` directly
- Approach B/C translate compose services to platform-specific config (Fly.toml, railway.json, render.yaml)
- Approach D deploys compose services through the PaaS UI

The `docker-compose.yml` should be the single source of truth for service definitions, environment variables, and inter-service dependencies. Platform-specific deployment configs are generated from or reference it.

---

## LLM Inference: The GPU Question

The spec requires on-premises inference. Practical options by deployment approach:

| Approach | GPU Option | CPU Fallback |
|----------|-----------|-------------|
| A (Single VPS) | Hetzner GPU server (~€150/mo), or CPU-only on 8+ cores | 4–8 msg/min, adequate for ≤50 users |
| B (Hybrid) | Separate GPU VPS (Lambda, Vast.ai, Hetzner) | Run Ollama CPU-only on PaaS |
| C (Fly.io) | Fly GPU Machine (A100/L40S, ~$2.50/hr) | Fly Machine with high CPU |
| D (Coolify) | Host machine GPU (pass through to Docker) | CPU-only on host |

**For MVP / Phase 1–2**: CPU-only inference is fine. Mistral 7B Q4 on 8 CPU cores processes 4–8 messages/minute — adequate for development and small-scale testing. Add GPU when message volume demands it.
