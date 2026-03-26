# Phase 1: Functional Mail Platform (Weeks 1–6)

## Goal

A working mail server with full MX, DKIM, IMAP, and web client. No intelligence layer yet.

## Tasks

### 1.1 Deploy Stalwart Mail Server
- Deploy Stalwart on cloud VM
- Configure Caddy as TLS termination reverse proxy
- Verify SMTP, IMAP, JMAP listeners active

### 1.2 Configure DNS Records
- MX record → mail hostname
- SPF TXT record
- DKIM TXT record (generate via Stalwart)
- DMARC TXT record
- PTR/rDNS record for VM IP

### 1.3 Deploy Web Client
- Deploy Roundcube Next or Snappymail
- **Decision checkpoint (Week 3)**: evaluate Roundcube Next maturity
- If not production-stable → fall back to Snappymail
- Configure to connect to Stalwart via IMAP/JMAP

### 1.4 Configure S3/MinIO Mail Storage
- Deploy MinIO (self-hosted) or configure cloud S3
- Configure Stalwart to use S3-compatible storage backend

### 1.5 End-to-End Testing
- Send mail (external → system)
- Receive mail (system → external)
- Reply chains
- Mobile IMAP access (test with Apple Mail, Outlook)
- DKIM/SPF/DMARC validation on inbound
- DKIM signing on outbound
- Verify delivery reputation (check blacklists, test with mail-tester.com)

### 1.6 Webhook Integration Skeleton
- Configure Stalwart `store.ingest` webhook to POST to mail-bridge
- Deploy mail-bridge service (FastAPI, port 8025)
- **No NATS deployed yet** — mail-bridge logs webhook payloads as placeholder
- Validate that webhook fires on every message delivery
- Ensure it does not affect delivery latency or reliability

## Acceptance Criteria

- [ ] Mail send/receive works for configured domain
- [ ] DKIM/SPF/DMARC all passing
- [ ] Web client accessible via HTTPS
- [ ] IMAP access works from third-party clients
- [ ] Webhook fires and mail-bridge receives events on every delivery
- [ ] S3 storage backend operational
