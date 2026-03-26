# Component: Mail Server (Stalwart)

## Selection Rationale

- Written in Rust (memory-safe, high throughput)
- Unified SMTP/IMAP/POP3/JMAP server
- Native Sieve scripting with extension support
- Built-in webhook engine for event-driven integrations
- Actively maintained, AGPL-3.0

## Required Capabilities

| Capability | Detail |
|-----------|--------|
| MX record handling | Receive mail for configured domains |
| SMTP submission | Port 587, STARTTLS mandatory |
| IMAP4rev2 | Port 993, TLS |
| JMAP | Modern client integration support |
| DKIM signing | Outbound mail — RSA-2048 or Ed25519 |
| SPF validation | Inbound |
| DMARC validation | Inbound |
| Webhook engine | Emit events on message delivery to external HTTP endpoint |
| S3 storage backend | S3-compatible mail storage (MinIO self-hosted or cloud S3) |

## NATS Emission via Webhook + mail-bridge

Stalwart's built-in webhook engine fires a `store.ingest` event on every message delivery. The `mail-bridge` service (FastAPI, port 8025) receives these webhooks and publishes the raw EML to NATS JetStream.

### Behaviour

- Stalwart POSTs webhook payload to `http://mail-bridge:8025/webhook`
- mail-bridge extracts the message and publishes to NATS stream `mail.inbound` (or `mail.outbound`)
- **Fire-and-forget** — delivery to recipient mailbox is NOT contingent on successful NATS emission
- Webhook failure does not block or delay mail delivery

### Why Webhooks Instead of Sieve

The original spec described a custom Rust Sieve extension (`sieve_nats_emit`). Stalwart v0.10 does not expose a public plugin API for Sieve extensions, making this approach impractical without forking Stalwart (triggering AGPL obligations). The webhook approach:

- Uses Stalwart's built-in, supported webhook engine
- Requires no Stalwart source modification
- Is simpler to operate and debug (HTTP vs. embedded plugin)
- Achieves identical fire-and-forget semantics

A skeleton Rust crate (`stalwart-sieve-nats`) exists in the repo for future use if Stalwart exposes a plugin API.

### Configuration

Webhook configured in `config/stalwart/config.toml`:

```toml
[webhook."nats-bridge"]
url = "http://mail-bridge:8025/webhook"
events = ["store.ingest"]
```

## Version Target

- Stalwart Mail Server 0.10.x
- Licence: AGPL-3.0
