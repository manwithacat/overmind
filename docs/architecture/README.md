# System Architecture

## Design Principles

- All inter-service communication via NATS JetStream message bus
- No layer has a hard dependency on another except through the bus and shared PostgreSQL/graph storage
- Each layer is independently deployable as a containerised service
- All LLM inference occurs within the operator's infrastructure boundary

## Message Flow — Inbound Message Lifecycle

```
1. RECEIPT
   Stalwart receives SMTP → validates SPF/DKIM/DMARC → delivers to mailbox
   Simultaneously: Sieve plugin emits raw message (headers + body) to NATS stream `mail.inbound`
   Emission is fire-and-forget — mailbox delivery is NOT contingent on NATS success

2. NORMALISATION
   Python Celery worker consumes from NATS →
   Parses EML (headers, MIME parts, attachment metadata) →
   Strips HTML to plain text →
   Truncates body to configurable token limit →
   Publishes normalised JSON to `mail.analysis.queue`

3. LLM CLASSIFICATION
   LLM Analysis Engine consumes normalised message →
   Runs structured extraction prompt against local model →
   Returns JSON: message_type, information_density, action_required,
   automation_candidate, thread_summary, key_entities →
   Validates against Pydantic schema →
   Failures: logged + queued for retry with simplified prompt

4. GRAPH WRITE
   Classification output written to PostgreSQL via Apache AGE →
   Nodes: persons (canonical identities), threads, topics →
   Edges: SENT_TO, REPLIED_TO, CC'd, FORWARDED_TO (typed, weighted by frequency + recency)

5. METRICS AGGREGATION
   Scheduled job (every 15 minutes) updates materialised views:
   - per-sender information density scores
   - attention cost index per recipient group
   - thread entropy metrics
   - automation candidate queues
```

Outbound messages follow an equivalent path initiated from the client layer.

## NATS Stream Topology

| Stream | Publisher | Consumer | Payload |
|--------|-----------|----------|---------|
| `mail.inbound` | Stalwart Sieve plugin | Ingestion Pipeline | Raw EML (headers + body) |
| `mail.outbound` | Stalwart Sieve plugin | Ingestion Pipeline | Raw EML (headers + body) |
| `mail.analysis.queue` | Ingestion Pipeline | LLM Analysis Engine | Normalised JSON message |
| `mail.analysis.results` | LLM Analysis Engine | Graph Writer | Classification JSON output |
| `mail.analysis.dlq` | Any worker | Monitoring/retry | Failed messages (dead letter) |

## Layer Dependency Map

```
Stalwart Mail Server
  └─► NATS JetStream
        └─► Ingestion Pipeline (Celery workers)
              └─► NATS JetStream
                    └─► LLM Analysis Engine (Ollama)
                          └─► NATS JetStream
                                └─► Graph Writer
                                      └─► PostgreSQL + Apache AGE
                                            └─► Materialised View Aggregation (cron)
                                                  └─► Intelligence API (FastAPI)
                                                        └─► Dashboard (React SPA)

Client Interface (Roundcube/Snappymail/Mobile)
  └─► Stalwart (IMAP/JMAP/SMTP)
  └─► Intelligence API (for annotation sidebar)
```
