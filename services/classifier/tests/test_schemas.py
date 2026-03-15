def test_classification_output_valid():
    from overmind_classifier.schemas import ClassificationOutput

    output = ClassificationOutput(
        message_type="request",
        information_density=0.7,
        action_required=True,
        action_urgency="this_week",
        automation_candidate=False,
        automation_type=None,
        thread_role="initiating",
        key_entities=["Q3 Budget", "Finance Team"],
        sentiment_valence="neutral",
        confidence=0.85,
    )
    assert output.message_type == "request"
    assert output.action_required is True


def test_classification_output_rejects_out_of_range_density():
    import pytest
    from pydantic import ValidationError

    from overmind_classifier.schemas import ClassificationOutput

    with pytest.raises(ValidationError):
        ClassificationOutput(
            message_type="request",
            information_density=1.5,  # out of range
            action_required=False,
            action_urgency=None,
            automation_candidate=False,
            automation_type=None,
            thread_role="noise",
            key_entities=[],
            sentiment_valence="neutral",
            confidence=0.5,
        )
