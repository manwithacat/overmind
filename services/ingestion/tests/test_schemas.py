from datetime import datetime, timezone


def test_normalised_message_valid():
    from overmind_ingestion.schemas import MessageDirection, NormalisedMessage

    msg = NormalisedMessage(
        message_id="<abc123@overmind.example.com>",
        thread_id=None,
        sender="alice@overmind.example.com",
        recipients=["bob@overmind.example.com"],
        bcc_count=0,
        subject="Test subject",
        body_text="Hello world",
        body_hash="abc123",
        has_attachments=False,
        attachment_types=[],
        received_at=datetime.now(timezone.utc),
        direction=MessageDirection.internal,
    )
    assert msg.message_id == "<abc123@overmind.example.com>"
    assert msg.direction == MessageDirection.internal


def test_normalised_message_rejects_invalid_direction():
    import pytest
    from pydantic import ValidationError

    from overmind_ingestion.schemas import NormalisedMessage

    with pytest.raises(ValidationError):
        NormalisedMessage(
            message_id="<abc@test>",
            thread_id=None,
            sender="a@b.com",
            recipients=["c@d.com"],
            bcc_count=0,
            subject="x",
            body_text="y",
            body_hash="z",
            has_attachments=False,
            attachment_types=[],
            received_at=datetime.now(timezone.utc),
            direction="invalid",
        )
