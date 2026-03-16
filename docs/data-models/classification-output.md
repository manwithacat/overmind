# Data Model: LLM Classification Output

Produced by the LLM Analysis Engine for each normalised message.

## Schema

```json
{
  "message_type": "enum: decision | request | status_update | broadcast | acknowledgement | social | unknown",
  "information_density": "float 0–1 — 0 = pure noise/acknowledgement; 1 = dense novel information",
  "action_required": "bool — true if recipient action explicitly or implicitly requested",
  "action_urgency": "enum | null: immediate | this_week | no_deadline | null",
  "automation_candidate": "bool — true if pattern suggests human performing machine-substitutable task",
  "automation_type": "string | null — brief label if automation_candidate, e.g. 'approval routing', 'status notification', 'data extraction'",
  "thread_role": "enum: initiating | contributing | closing | noise",
  "key_entities": ["string — named entities: projects, systems, external organisations"],
  "sentiment_valence": "enum: positive | neutral | negative | urgent",
  "confidence": "float 0–1 — model self-reported confidence"
}
```

## Pydantic Model (reference)

```python
from enum import Enum
from pydantic import BaseModel, Field


class MessageType(str, Enum):
    decision = "decision"
    request = "request"
    status_update = "status_update"
    broadcast = "broadcast"
    acknowledgement = "acknowledgement"
    social = "social"
    unknown = "unknown"


class ActionUrgency(str, Enum):
    immediate = "immediate"
    this_week = "this_week"
    no_deadline = "no_deadline"


class ThreadRole(str, Enum):
    initiating = "initiating"
    contributing = "contributing"
    closing = "closing"
    noise = "noise"


class SentimentValence(str, Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"
    urgent = "urgent"


class ClassificationOutput(BaseModel):
    message_type: MessageType
    information_density: float = Field(ge=0.0, le=1.0)
    action_required: bool
    action_urgency: ActionUrgency | None
    automation_candidate: bool
    automation_type: str | None
    thread_role: ThreadRole
    key_entities: list[str]
    sentiment_valence: SentimentValence
    confidence: float = Field(ge=0.0, le=1.0)
```

## Validation Rules

- All enum fields must match exactly (case-sensitive)
- `float` fields must be in [0.0, 1.0] range
- `automation_type` should be non-null only when `automation_candidate` is true
- `action_urgency` should be non-null only when `action_required` is true

## Fallback on Validation Failure

If the LLM output fails Pydantic validation:
1. Log the error with the raw LLM response
2. Retry with a simplified prompt requesting only: `message_type`, `information_density`, `action_required`
3. After max retries, send to dead-letter queue with error metadata
