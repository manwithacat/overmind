import json
from unittest.mock import patch

import pytest
from langchain_core.messages import AIMessage


@pytest.mark.asyncio
async def test_classify_message_returns_valid_output():
    from overmind_classifier.worker import classify_message

    mock_response = AIMessage(
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

    with patch("overmind_classifier.worker._call_llm", return_value=mock_response.content):
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

    bad_json = json.dumps(
        {
            "message_type": "request",
            "information_density": 5.0,  # invalid: > 1.0
            "action_required": True,
        }
    )

    good_json = json.dumps(
        {
            "message_type": "status_update",
            "information_density": 0.3,
            "action_required": False,
        }
    )

    with patch(
        "overmind_classifier.worker._call_llm",
        side_effect=[bad_json, good_json],
    ):
        result = await classify_with_retry(
            subject="Update",
            body="Status update.",
            sender="alice@overmind.local",
            recipients=["bob@overmind.local"],
        )

    assert result.message_type == "status_update"
    assert result.confidence == 0.5  # default from simplified fallback
