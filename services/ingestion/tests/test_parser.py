"""Tests for the EML parser module."""

from datetime import datetime, timezone


def test_parse_simple_eml():
    from overmind_ingestion.parser import parse_eml

    eml = (
        b"From: alice@overmind.local\n"
        b"To: bob@overmind.local\n"
        b"Subject: Hello\n"
        b"Message-ID: <msg-001@overmind.local>\n"
        b"Date: Thu, 01 Jan 2026 12:00:00 +0000\n\n"
        b"Hello Bob."
    )
    msg = parse_eml(eml)
    assert msg.sender == "alice@overmind.local"
    assert msg.recipients == ["bob@overmind.local"]
    assert msg.subject == "Hello"
    assert msg.message_id == "<msg-001@overmind.local>"
    assert msg.body_text == "Hello Bob."
    assert msg.has_attachments is False
    assert msg.bcc_count == 0


def test_parse_eml_multiple_recipients():
    from overmind_ingestion.parser import parse_eml

    eml = (
        b"From: alice@overmind.local\n"
        b"To: bob@overmind.local, carol@overmind.local\n"
        b"Cc: dave@overmind.local\n"
        b"Subject: Group\n"
        b"Message-ID: <msg-002@overmind.local>\n\n"
        b"Group message."
    )
    msg = parse_eml(eml)
    assert len(msg.recipients) == 3
    assert "dave@overmind.local" in msg.recipients


def test_parse_eml_missing_date_defaults_to_utc_now():
    from overmind_ingestion.parser import parse_eml

    eml = (
        b"From: alice@overmind.local\n"
        b"To: bob@overmind.local\n"
        b"Subject: No date\n"
        b"Message-ID: <msg-003@overmind.local>\n\n"
        b"Body."
    )
    msg = parse_eml(eml)
    assert msg.received_at.tzinfo is not None
