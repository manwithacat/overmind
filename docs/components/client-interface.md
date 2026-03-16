# Component: Client Interface

## Requirements

- Gmail-quality UX without proprietary service dependencies
- Two deployment targets: web (browser) and mobile (iOS/Android)
- Standard IMAP/SMTP access for third-party clients (Outlook, Apple Mail, Thunderbird) must work unmodified

## Web Client

### Primary Option: Roundcube Next

- Under active development, React-based, JMAP-native
- Licence: GPL-3.0
- **Risk**: may not be production-stable within Phase 1 timeline
- Decision checkpoint: Week 3 — evaluate current build status

### Fallback Option: Snappymail

- Mature, PHP-based, less modern UX
- Stable and production-proven
- Suitable fallback if Roundcube Next is not ready

### OVERMIND Sidebar Plugin

The web client is extended with an OVERMIND sidebar panel, injected as a plugin, that displays per-message intelligence annotations:

| Annotation | Source |
|-----------|--------|
| Message type badge | `message_type` from classification |
| Information density indicator | `information_density` from classification |
| Automation flag | `automation_candidate` from classification |
| Action required indicator | `action_required` + `action_urgency` |
| Sentiment indicator | `sentiment_valence` |

Data is sourced from the Intelligence API (read-only, per-message lookup by `message_id`).

## Mobile Client

### Technology

- React Native application
- JMAP client libraries (`jmap-client-ts`)
- Push notifications via web push (no APNS/FCM dependency for content; only notification payloads)

### Features

- Standard operations: compose, read, search, folder management
- Intelligence annotations surfaced as swipe-action metadata
- OVERMIND sidebar equivalent (condensed for mobile)

## Third-Party Client Support

Standard IMAP/SMTP access — no special configuration required for:
- Apple Mail
- Outlook
- Thunderbird
- Any standards-compliant IMAP/SMTP client

Intelligence annotations are NOT available in third-party clients (IMAP does not support custom metadata display).
