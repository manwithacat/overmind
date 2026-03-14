import asyncio
import logging
import os

import nats
from fastapi import FastAPI, Request, Response
from pydantic import BaseModel

logger = logging.getLogger(__name__)

app = FastAPI(title="OVERMIND Mail Bridge")

# NATS connection (lazy init)
_nc = None

NATS_TIMEOUT = float(os.environ.get("NATS_TIMEOUT", "5"))


class WebhookPayload(BaseModel):
    """Stalwart webhook payload for message delivery events."""
    event: str
    message: str  # Raw EML content


async def get_nats():
    global _nc
    if _nc is None or not _nc.is_connected:
        nats_url = os.environ.get("NATS_URL", "nats://localhost:4222")
        _nc = await nats.connect(
            nats_url,
            connect_timeout=2,
            max_reconnect_attempts=0,
        )
        js = _nc.jetstream()
        # Ensure stream exists
        try:
            await js.find_stream_name_by_subject("mail.inbound")
        except nats.js.errors.NotFoundError:
            await js.add_stream(name="MAIL", subjects=["mail.inbound", "mail.outbound"])
    return _nc


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/webhook")
async def webhook(payload: WebhookPayload, response: Response):
    """Receive Stalwart webhook and publish to NATS."""
    if payload.event != "store.ingest":
        return {"status": "ignored", "reason": f"event type {payload.event}"}

    try:
        nc = await asyncio.wait_for(get_nats(), timeout=NATS_TIMEOUT)
        js = nc.jetstream()
        await asyncio.wait_for(
            js.publish("mail.inbound", payload.message.encode()),
            timeout=NATS_TIMEOUT,
        )
        logger.info("Published message to mail.inbound")
    except Exception:
        # Fire-and-forget: log but don't fail the webhook
        logger.exception("Failed to publish to NATS")

    return {"status": "accepted"}
