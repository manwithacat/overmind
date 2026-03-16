import json
from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_classify_message_returns_valid_output():
    from overmind_classifier.worker import classify_message

    mock_response = AsyncMock()
    mock_response.choices = [
        AsyncMock(
            message=AsyncMock(
                content=json.dumps(
                    {
                        "message_type": "request",
                        "information_density": 0.7,
                        "action_required": True,
                        "action_urgency": "this_week",
                        "automation_candidate": False,
                        "automation_type": None,
                        "thread_role": "initiating",
                        "key_entities": ["Q3 Budget"],
                        "sentiment_valence": "neutral",
                        "confidence": 0.85,
                    }
                )
            )
        )
    ]

    with patch("overmind_classifier.worker.litellm.acompletion", return_value=mock_response):
        result = await classify_message(
            subject="Q3 Budget Review",
            body="Please review the budget proposal.",
            sender="alice@overmind.local",
            recipients=["bob@overmind.local"],
        )

    assert result.message_type == "request"
    assert result.action_required is True


@pytest.mark.asyncio
async def test_classify_with_retry_falls_back_on_validation_error():
    """Test that classify_with_retry falls back to simplified prompt on validation failure."""
    from overmind_classifier.worker import classify_with_retry

    # First call returns invalid JSON (bad density value)
    bad_response = AsyncMock()
    bad_response.choices = [
        AsyncMock(
            message=AsyncMock(
                content=json.dumps(
                    {
                        "message_type": "request",
                        "information_density": 5.0,  # invalid: > 1.0
                        "action_required": True,
                    }
                )
            )
        )
    ]

    # Second call (simplified) returns valid subset
    good_response = AsyncMock()
    good_response.choices = [
        AsyncMock(
            message=AsyncMock(
                content=json.dumps(
                    {
                        "message_type": "status_update",
                        "information_density": 0.3,
                        "action_required": False,
                    }
                )
            )
        )
    ]

    with patch(
        "overmind_classifier.worker.litellm.acompletion",
        side_effect=[bad_response, good_response],
    ):
        result = await classify_with_retry(
            subject="Update",
            body="Status update.",
            sender="alice@overmind.local",
            recipients=["bob@overmind.local"],
        )

    assert result.message_type == "status_update"
    assert result.confidence == 0.5  # default from simplified fallback
