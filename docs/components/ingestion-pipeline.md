# Component: Ingestion Pipeline

## Responsibility

Consume raw EML messages from NATS, parse and normalise them, and publish structured JSON to the analysis queue for LLM processing.

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Python | 3.12 |
| Async Runtime | asyncio | stdlib |
| Message Bus Client | nats.py (asyncio) | Latest |
| EML Parsing | mail-parser | Latest |
| HTML Stripping | BeautifulSoup4 | Latest |
| Schema Validation | Pydantic v2 | v2 |

> **Note:** The original spec described Celery + Redis for task orchestration. The implementation uses NATS JetStream durable consumers directly, which provides equivalent at-least-once delivery semantics without the operational overhead of a separate task queue and broker. Redis is not required.

## Processing Steps

```
NATS `mail.inbound` / `mail.outbound`
  │
  ▼
Asyncio worker pulls batch (10 messages, 5s timeout)
  │
  ├─ 1. Parse EML (headers, MIME parts, attachment metadata)
  ├─ 2. Extract sender, recipients (To + CC), BCC count only
  ├─ 3. Strip HTML to plain text (BeautifulSoup4)
  ├─ 4. Truncate body to configurable character limit (default: 8,192 chars)
  ├─ 5. Compute body_hash (SHA-256 of full body, for deduplication)
  ├─ 6. Compute thread_id from In-Reply-To chain (null if new thread)
  ├─ 7. Normalise subject (strip Re:/Fwd: prefixes for thread grouping)
  ├─ 8. Determine direction (inbound | outbound | internal)
  ├─ 9. Validate against Pydantic schema
  │
  ▼
Publish normalised JSON to NATS `mail.analysis.queue`
Ack original message on success; Nack (requeue) on error
```

## Output Schema

See [Normalised Message Schema](../data-models/normalised-message.md) for the full field specification.

## Error Handling

| Scenario | Behaviour |
|----------|----------|
| Parse failure (corrupt EML) | Log error, Nack message for redelivery |
| Schema validation failure | Log, Nack message |
| NATS publish failure | Nack original message (redelivered by JetStream) |
| Repeated failure (>max redeliveries) | Message expires per stream retention policy |

## Scaling

- Multiple worker instances can subscribe to the same durable consumer group
- NATS JetStream distributes messages across consumers automatically
- Stateless workers — horizontal scaling is straightforward

## Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `BODY_CHAR_LIMIT` | 8192 | Max characters in body_text |
| `BATCH_SIZE` | 10 | Messages fetched per pull |
| `FETCH_TIMEOUT` | 5 | Seconds to wait for messages |
| `NATS_URL` | `nats://localhost:4222` | NATS connection string |
