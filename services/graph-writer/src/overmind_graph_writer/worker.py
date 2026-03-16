import json
import logging
import os

import nats
import psycopg
from nats.js.api import ConsumerConfig, DeliverPolicy

from .queries import (
    insert_classification_query,
    upsert_attention_cost_query,
    upsert_person_cypher,
    upsert_sent_to_cypher,
)

logger = logging.getLogger(__name__)


def get_db_url() -> str:
    user = os.environ.get("POSTGRES_USER", "overmind")
    password = os.environ.get("POSTGRES_PASSWORD", "overmind-dev")
    host = os.environ.get("POSTGRES_HOST", "localhost")
    db = os.environ.get("POSTGRES_DB", "overmind")
    return f"postgresql://{user}:{password}@{host}:5432/{db}"


async def process_result(data: dict, conn) -> None:
    """Write classification result to graph and relational tables."""
    message_id = data["message_id"]
    sender = data["sender"]
    recipients = data["recipients"]
    classification = data["classification"]

    sender_domain = sender.split("@")[1] if "@" in sender else "unknown"
    sender_name = sender.split("@")[0] if "@" in sender else sender
    is_internal = sender_domain == "overmind.local"

    async with conn.cursor() as cur:
        # Set AGE search path
        await cur.execute("LOAD 'age';")
        await cur.execute('SET search_path = ag_catalog, "$user", public;')

        # Upsert sender Person node
        await cur.execute(upsert_person_cypher(sender, sender_name, sender_domain, is_internal))

        # Upsert recipient Person nodes and SENT_TO edges
        density = classification.get("information_density", 0.5)
        for recipient in recipients:
            r_domain = recipient.split("@")[1] if "@" in recipient else "unknown"
            r_name = recipient.split("@")[0] if "@" in recipient else recipient
            r_internal = r_domain == "overmind.local"

            await cur.execute(upsert_person_cypher(recipient, r_name, r_domain, r_internal))
            await cur.execute(upsert_sent_to_cypher(sender, recipient, density))

        # Insert classification into relational table
        await cur.execute(
            insert_classification_query(),
            {
                "message_id": message_id,
                "message_type": classification["message_type"],
                "information_density": classification["information_density"],
                "action_required": classification["action_required"],
                "action_urgency": classification.get("action_urgency"),
                "automation_candidate": classification["automation_candidate"],
                "automation_type": classification.get("automation_type"),
                "thread_role": classification["thread_role"],
                "key_entities": classification.get("key_entities", []),
                "sentiment_valence": classification["sentiment_valence"],
                "confidence": classification["confidence"],
            },
        )

        # Update attention cost metric
        recipient_count = len(recipients)
        cost = recipient_count * (1.0 - density)
        await cur.execute(
            upsert_attention_cost_query(),
            {
                "email": sender,
                "display_name": sender_name,
                "cost": cost,
                "density": density,
            },
        )

    await conn.commit()
    logger.info("Wrote graph data for message %s", message_id)


async def run():
    """Main worker loop."""
    nats_url = os.environ.get("NATS_URL", "nats://localhost:4222")
    nc = await nats.connect(nats_url)
    js = nc.jetstream()

    try:
        await js.find_stream_name_by_subject("mail.analysis.results")
    except nats.js.errors.NotFoundError:
        await js.add_stream(name="RESULTS", subjects=["mail.analysis.results"])

    sub = await js.pull_subscribe(
        "mail.analysis.results",
        durable="graph-writer",
        config=ConsumerConfig(deliver_policy=DeliverPolicy.ALL),
    )

    conn = await psycopg.AsyncConnection.connect(get_db_url(), autocommit=False)

    logger.info("Graph writer started, consuming from mail.analysis.results")

    while True:
        try:
            msgs = await sub.fetch(batch=10, timeout=5)
            for msg in msgs:
                try:
                    data = json.loads(msg.data)
                    await process_result(data, conn)
                    await msg.ack()
                except Exception:
                    logger.exception("Failed to write graph data")
                    await msg.nak()
        except nats.errors.TimeoutError:
            continue
