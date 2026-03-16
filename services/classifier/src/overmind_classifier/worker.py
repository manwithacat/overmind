import json
import logging
import os

import litellm
import nats
from nats.js.api import ConsumerConfig, DeliverPolicy
from pydantic import ValidationError

from .prompts import SIMPLIFIED_PROMPT, SYSTEM_PROMPT, build_user_prompt
from .schemas import ClassificationOutput

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


async def classify_message(
    subject: str, body: str, sender: str, recipients: list[str]
) -> ClassificationOutput:
    """Classify a single message via LiteLLM."""
    model = os.environ.get("OVERMIND_LLM_PROVIDER", "anthropic/claude-sonnet-4-20250514")
    user_prompt = build_user_prompt(subject, body, sender, recipients)

    response = await litellm.acompletion(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    raw_json = response.choices[0].message.content
    data = json.loads(raw_json)
    return ClassificationOutput(**data)


async def classify_with_retry(
    subject: str, body: str, sender: str, recipients: list[str]
) -> ClassificationOutput:
    """Classify with fallback to simplified prompt on validation failure."""
    try:
        return await classify_message(subject, body, sender, recipients)
    except (ValidationError, json.JSONDecodeError) as e:
        logger.warning("Full classification failed, trying simplified: %s", e)

    # Simplified fallback
    model = os.environ.get("OVERMIND_LLM_PROVIDER", "anthropic/claude-sonnet-4-20250514")
    user_prompt = build_user_prompt(subject, body, sender, recipients)

    response = await litellm.acompletion(
        model=model,
        messages=[
            {"role": "system", "content": SIMPLIFIED_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    raw_json = response.choices[0].message.content
    data = json.loads(raw_json)
    # Fill in defaults for missing fields
    data.setdefault("action_urgency", None)
    data.setdefault("automation_candidate", False)
    data.setdefault("automation_type", None)
    data.setdefault("thread_role", "noise")
    data.setdefault("key_entities", [])
    data.setdefault("sentiment_valence", "neutral")
    data.setdefault("confidence", 0.5)
    return ClassificationOutput(**data)


async def run():
    """Main worker loop: consume from ANALYSIS stream, classify, publish to RESULTS."""
    nats_url = os.environ.get("NATS_URL", "nats://localhost:4222")
    nc = await nats.connect(nats_url)
    js = nc.jetstream()

    # Ensure streams exist
    try:
        await js.find_stream_name_by_subject("mail.analysis.queue")
    except nats.js.errors.NotFoundError:
        await js.add_stream(name="ANALYSIS", subjects=["mail.analysis.queue"])

    try:
        await js.find_stream_name_by_subject("mail.analysis.results")
    except nats.js.errors.NotFoundError:
        await js.add_stream(name="RESULTS", subjects=["mail.analysis.results"])

    try:
        await js.find_stream_name_by_subject("mail.analysis.dlq")
    except nats.js.errors.NotFoundError:
        await js.add_stream(name="DLQ", subjects=["mail.analysis.dlq"])

    sub = await js.pull_subscribe(
        "mail.analysis.queue",
        durable="classifier",
        config=ConsumerConfig(deliver_policy=DeliverPolicy.ALL),
    )

    logger.info("Classifier worker started, consuming from mail.analysis.queue")

    while True:
        try:
            msgs = await sub.fetch(batch=1, timeout=5)
            for msg in msgs:
                try:
                    payload = json.loads(msg.data)
                    result = await classify_with_retry(
                        subject=payload["subject"],
                        body=payload["body_text"],
                        sender=payload["sender"],
                        recipients=payload["recipients"],
                    )
                    output = {
                        "message_id": payload["message_id"],
                        "sender": payload["sender"],
                        "recipients": payload["recipients"],
                        "classification": result.model_dump(),
                    }
                    await js.publish("mail.analysis.results", json.dumps(output).encode())
                    await msg.ack()
                    logger.info(
                        "Classified message %s as %s",
                        payload["message_id"],
                        result.message_type,
                    )
                except Exception:
                    logger.exception("Failed to classify message")
                    try:
                        await js.publish("mail.analysis.dlq", msg.data)
                    except Exception:
                        logger.exception("Failed to publish to DLQ")
                    await msg.ack()
        except nats.errors.TimeoutError:
            continue
