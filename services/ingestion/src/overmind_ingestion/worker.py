"""NATS JetStream worker — consumes from MAIL stream, normalises, publishes to ANALYSIS."""

import logging
import os

import nats
from nats.js.api import ConsumerConfig, DeliverPolicy

from .parser import parse_eml
from .schemas import NormalisedMessage

logger = logging.getLogger(__name__)


async def process_message(raw: bytes) -> NormalisedMessage:
    """Parse raw EML and return normalised message."""
    return parse_eml(raw)


async def run():
    """Main worker loop: consume from NATS MAIL stream, normalise, publish to ANALYSIS."""
    nats_url = os.environ.get("NATS_URL", "nats://localhost:4222")
    nc = await nats.connect(nats_url)
    js = nc.jetstream()

    # Ensure streams exist
    try:
        await js.find_stream_name_by_subject("mail.inbound")
    except nats.js.errors.NotFoundError:
        await js.add_stream(name="MAIL", subjects=["mail.inbound", "mail.outbound"])

    try:
        await js.find_stream_name_by_subject("mail.analysis.queue")
    except nats.js.errors.NotFoundError:
        await js.add_stream(name="ANALYSIS", subjects=["mail.analysis.queue"])

    # Subscribe with durable consumer
    sub = await js.pull_subscribe(
        "mail.inbound",
        durable="ingestion",
        config=ConsumerConfig(deliver_policy=DeliverPolicy.ALL),
    )

    logger.info("Ingestion worker started, consuming from mail.inbound")

    while True:
        try:
            msgs = await sub.fetch(batch=10, timeout=5)
            for msg in msgs:
                try:
                    normalised = await process_message(msg.data)
                    payload = normalised.model_dump_json().encode()
                    await js.publish("mail.analysis.queue", payload)
                    await msg.ack()
                    logger.info("Normalised message %s", normalised.message_id)
                except Exception:
                    logger.exception("Failed to process message")
                    await msg.nak()
        except nats.errors.TimeoutError:
            continue  # No messages, loop back
