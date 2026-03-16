# Component: Mail Server (Stalwart)

## Selection Rationale

- Written in Rust (memory-safe, high throughput)
- Unified SMTP/IMAP/POP3/JMAP server
- Native Sieve scripting with extension support
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
| Sieve scripting | Execute at delivery time — used to emit copy to NATS |
| S3 storage backend | S3-compatible mail storage (MinIO self-hosted or cloud S3) |

## NATS Emission via Sieve

A custom Sieve action `sieve_nats_emit` is implemented as a Stalwart plugin (Rust) registered as a Sieve extension.

### Behaviour

- Serialises message envelope and body to NATS JetStream
- Publishes to stream `mail.inbound` (or `mail.outbound` for sent messages)
- **Fire-and-forget** — delivery to recipient mailbox is NOT contingent on successful NATS emission
- NATS failure must not block or delay mail delivery

### Implementation Notes

- Plugin must be written in Rust as a Stalwart Sieve extension
- Must handle NATS connection failures gracefully (log and skip)
- Must serialise full EML including all headers
- Consider backpressure: if NATS is unreachable for extended period, log to local file as fallback

## Version Target

- Stalwart Mail Server 0.10.x
- Licence: AGPL-3.0
