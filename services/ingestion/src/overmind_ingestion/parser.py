"""EML parser — converts raw RFC 5322 bytes into a NormalisedMessage."""

import email
import email.policy
import email.utils
import hashlib
import re
from datetime import UTC, datetime

from bs4 import BeautifulSoup

from .schemas import MessageDirection, NormalisedMessage

MAX_BODY_CHARS = 8192  # ~2048 tokens at ~4 chars/token


def _strip_html(html: str) -> str:
    """Strip HTML tags, return plain text."""
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def _extract_address(header_value: str) -> str:
    """Extract a single email address from a header value."""
    _name, addr = email.utils.parseaddr(header_value)
    return addr or header_value.strip()


def _extract_addresses(header_value: str) -> list[str]:
    """Extract multiple email addresses from a header value."""
    if not header_value:
        return []
    pairs = email.utils.getaddresses([header_value])
    return [addr for _name, addr in pairs if addr]


def _extract_body(msg: email.message.EmailMessage) -> str:
    """Extract plain-text body, stripping HTML if needed, and truncate."""
    # Prefer plain text
    plain_body = msg.get_body(preferencelist=("plain",))
    if plain_body is not None:
        content = plain_body.get_content()
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")
        return content.strip()[:MAX_BODY_CHARS]

    # Fall back to HTML, strip tags
    html_body = msg.get_body(preferencelist=("html",))
    if html_body is not None:
        content = html_body.get_content()
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")
        return _strip_html(content)[:MAX_BODY_CHARS]

    return ""


def _extract_attachment_types(msg: email.message.EmailMessage) -> list[str]:
    """Return a list of MIME types for attachments."""
    types = []
    for part in msg.iter_attachments():
        ct = part.get_content_type()
        if ct:
            types.append(ct)
    return types


def _parse_date(date_str: str | None) -> datetime:
    """Parse an email Date header, falling back to now(UTC)."""
    if date_str:
        parsed = email.utils.parsedate_to_datetime(date_str)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed
    return datetime.now(UTC)


def _determine_direction(
    sender: str, recipients: list[str], local_domain: str = "overmind.local"
) -> MessageDirection:
    """Determine message direction based on sender/recipient domains."""
    sender_internal = sender.endswith(f"@{local_domain}")
    all_recipients_internal = all(r.endswith(f"@{local_domain}") for r in recipients)

    if sender_internal and all_recipients_internal:
        return MessageDirection.internal
    elif sender_internal:
        return MessageDirection.outbound
    else:
        return MessageDirection.inbound


def parse_eml(raw: bytes) -> NormalisedMessage:
    """Parse raw EML bytes and return a NormalisedMessage."""
    msg = email.message_from_bytes(raw, policy=email.policy.default)

    sender = _extract_address(msg.get("From", ""))
    recipients = _extract_addresses(msg.get("To", ""))
    cc = _extract_addresses(msg.get("Cc", ""))
    recipients = recipients + cc

    bcc_raw = msg.get("Bcc", "")
    bcc_addresses = _extract_addresses(bcc_raw) if bcc_raw else []
    bcc_count = len(bcc_addresses)

    # Subject normalisation — strip Re:/Fwd: prefixes
    subject = msg.get("Subject", "")
    subject = re.sub(r"^(Re|Fwd|Fw)\s*:\s*", "", subject, flags=re.IGNORECASE).strip()

    message_id = msg.get("Message-ID", "")
    thread_id = msg.get("In-Reply-To") or msg.get("References") or None

    body_text = _extract_body(msg)
    body_hash = hashlib.sha256(body_text.encode()).hexdigest()

    attachments = _extract_attachment_types(msg)
    received_at = _parse_date(msg.get("Date"))
    direction = _determine_direction(sender, recipients)

    return NormalisedMessage(
        message_id=message_id or f"<generated-{body_hash[:8]}@overmind>",
        thread_id=thread_id if thread_id != message_id else None,
        sender=sender,
        recipients=recipients,
        bcc_count=bcc_count,
        subject=subject,
        body_text=body_text,
        body_hash=body_hash,
        has_attachments=len(attachments) > 0,
        attachment_types=attachments,
        received_at=received_at,
        direction=direction,
    )
