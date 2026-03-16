from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class MessageDirection(str, Enum):
    inbound = "inbound"
    outbound = "outbound"
    internal = "internal"


class NormalisedMessage(BaseModel):
    message_id: str
    thread_id: str | None
    sender: str
    recipients: list[str]
    bcc_count: int
    subject: str
    body_text: str
    body_hash: str
    has_attachments: bool
    attachment_types: list[str]
    received_at: datetime
    direction: MessageDirection
