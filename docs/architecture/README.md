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
   Simultaneously: Stalwart webhook (store.ingest) POSTs raw message to mail-bridge
   mail-bridge publishes to NATS stream `mail.inbound`
   Emission is fire-and-forget — mailbox delivery is NOT contingent on NATS success

2. NORMALISATION
   Ingestion worker (asyncio) consumes from NATS `mail.inbound` →
   Parses EML (headers, MIME parts, attachment metadata) →
   Strips HTML to plain text →
   Truncates body to configurable token limit →
   Publishes normalised JSON to `mail.analysis.queue`

3. LLM CLASSIFICATION
   Classifier worker consumes normalised message →
   Runs structured extraction prompt via LangChain (local or remote model) →
   Returns JSON: message_type, information_density, action_required,
   automation_candidate, thread_role, key_entities →
   Validates against Pydantic schema →
   Failures: logged + retried with simplified prompt, then DLQ

4. GRAPH WRITE
   Classification output written to PostgreSQL via Apache AGE →
   Nodes: Person (canonical identities), Thread, Topic →
   Edges: SENT_TO (typed, weighted by frequency + recency)
   Classification also stored in relational table for fast lookup

5. METRICS AGGREGATION
   Attention cost index updated incrementally per message (PoC)
   Production: scheduled job (every 15 minutes) updates materialised views:
   - per-sender information density scores
   - attention cost index per recipient group
   - thread entropy metrics
   - automation candidate queues
```

Outbound messages follow an equivalent path initiated from the client layer.

## NATS Stream Topology

| Stream | Publisher | Consumer | Payload |
|--------|-----------|----------|---------|
| `mail.inbound` | mail-bridge (Stalwart webhook) | Ingestion worker | Raw EML (headers + body) |
| `mail.outbound` | mail-bridge (Stalwart webhook) | Ingestion worker | Raw EML (headers + body) |
| `mail.analysis.queue` | Ingestion worker | Classifier worker | Normalised JSON message |
| `mail.analysis.results` | Classifier worker | Graph Writer | Classification JSON output |
| `mail.analysis.dlq` | Any worker | Monitoring/retry | Failed messages (dead letter) |

## Layer Dependency Map

```
Stalwart Mail Server
  └─► Stalwart webhook (store.ingest event)
        └─► mail-bridge (FastAPI, port 8025)
              └─► NATS JetStream
                    └─► Ingestion worker (asyncio)
                          └─► NATS JetStream
                                └─► Classifier worker (LangChain)
                                      └─► NATS JetStream
                                            └─► Graph Writer
                                                  └─► PostgreSQL + Apache AGE
                                                        └─► Intelligence API (FastAPI)
                                                              └─► Dashboard (React SPA)

Client Interface (Roundcube/Snappymail/Mobile)
  └─► Stalwart (IMAP/JMAP/SMTP)
  └─► Intelligence API (for annotation sidebar)
```
