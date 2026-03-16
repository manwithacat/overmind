# Component: Ingestion Pipeline

## Responsibility

Consume raw EML messages from NATS, parse and normalise them, and publish structured JSON to the analysis queue for LLM processing.

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Python | 3.12 |
| Task Queue | Celery 5 | 5.x |
| Queue Broker | Redis | 7.x |
| Message Bus Client | nats.py (asyncio) | Latest |
| EML Parsing | mail-parser | Latest |
| HTML Stripping | BeautifulSoup4 | Latest |
| Schema Validation | Pydantic v2 | v2 |

## Processing Steps

```
NATS `mail.inbound` / `mail.outbound`
  │
  ▼
Celery Worker picks up message
  │
  ├─ 1. Parse EML (headers, MIME parts, attachment metadata)
  ├─ 2. Extract sender, recipients (To + CC), BCC count only
  ├─ 3. Strip HTML to plain text (BeautifulSoup4)
  ├─ 4. Truncate body to configurable token limit (default: 2,048 tokens)
  ├─ 5. Compute body_hash (SHA-256 of full body, for deduplication)
  ├─ 6. Compute thread_id from In-Reply-To chain (null if new thread)
  ├─ 7. Normalise subject (strip Re:/Fwd: prefixes for thread grouping)
  ├─ 8. Determine direction (inbound | outbound | internal)
  ├─ 9. Validate against Pydantic schema
  │
  ▼
Publish normalised JSON to NATS `mail.analysis.queue`
```

## Output Schema

See [Normalised Message Schema](../data-models/normalised-message.md) for the full field specification.

## Error Handling

| Scenario | Behaviour |
|----------|----------|
| Parse failure (corrupt EML) | Log error, send to `mail.analysis.dlq` |
| Schema validation failure | Log, send to DLQ |
| NATS publish failure | Celery retry with exponential backoff |
| Repeated failure (>3 retries) | Send to NATS dead-letter stream `mail.analysis.dlq` |

## Scaling

- Celery workers scaled via Kubernetes HPA based on NATS queue depth
- Stateless workers — horizontal scaling is straightforward
- Redis broker handles task distribution

## Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `BODY_TOKEN_LIMIT` | 2048 | Max tokens in body_text |
| `MAX_RETRIES` | 3 | Retry attempts before DLQ |
| `RETRY_BACKOFF_BASE` | 60 | Base seconds for exponential backoff |
| `NATS_URL` | `nats://localhost:4222` | NATS connection string |
| `REDIS_URL` | `redis://localhost:6379` | Redis broker URL |
