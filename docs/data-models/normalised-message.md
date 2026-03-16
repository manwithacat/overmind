# Data Model: Normalised Message

Published to NATS stream `mail.analysis.queue` by the Ingestion Pipeline.

## Schema

```json
{
  "message_id": "string — RFC 2822 Message-ID, canonical",
  "thread_id": "string | null — computed from In-Reply-To chain; null if new thread",
  "sender": "EmailAddress — normalised to canonical identity if known",
  "recipients": ["EmailAddress — To + CC combined; BCC suppressed"],
  "bcc_count": "int — count only, BCC addresses NOT stored",
  "subject": "string — decoded, normalised (Re:/Fwd: stripped for thread grouping)",
  "body_text": "string — plain text, truncated at 2,048 tokens",
  "body_hash": "string — SHA-256 of full body for deduplication",
  "has_attachments": "bool — true if any MIME attachment present",
  "attachment_types": ["string — MIME types only, no attachment content stored"],
  "received_at": "datetime — UTC, from Received header",
  "direction": "enum: inbound | outbound | internal"
}
```

## Pydantic Model (reference)

```python
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr


class MessageDirection(str, Enum):
    inbound = "inbound"
    outbound = "outbound"
    internal = "internal"


class NormalisedMessage(BaseModel):
    message_id: str
    thread_id: str | None
    sender: EmailStr
    recipients: list[EmailStr]
    bcc_count: int
    subject: str
    body_text: str  # max 2,048 tokens
    body_hash: str  # SHA-256
    has_attachments: bool
    attachment_types: list[str]
    received_at: datetime
    direction: MessageDirection
```

## Privacy Constraints

- BCC addresses are NEVER stored — only the count
- Attachment content is NEVER analysed or stored — only MIME types
- Body text is truncated; full body exists only in mail store
