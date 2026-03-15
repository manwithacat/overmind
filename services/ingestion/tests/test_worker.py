import pytest


@pytest.mark.asyncio
async def test_process_message_returns_normalised():
    from overmind_ingestion.worker import process_message

    eml = (
        b"From: alice@overmind.local\n"
        b"To: bob@overmind.local\n"
        b"Subject: Test\n"
        b"Message-ID: <test-001@overmind.local>\n\n"
        b"Hello Bob, please review the proposal."
    )
    result = await process_message(eml)
    assert result.sender == "alice@overmind.local"
    assert result.message_id == "<test-001@overmind.local>"
