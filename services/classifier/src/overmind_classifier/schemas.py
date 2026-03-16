from enum import StrEnum

from pydantic import BaseModel, Field


class MessageType(StrEnum):
    decision = "decision"
    request = "request"
    status_update = "status_update"
    broadcast = "broadcast"
    acknowledgement = "acknowledgement"
    social = "social"
    unknown = "unknown"


class ActionUrgency(StrEnum):
    immediate = "immediate"
    this_week = "this_week"
    no_deadline = "no_deadline"


class ThreadRole(StrEnum):
    initiating = "initiating"
    contributing = "contributing"
    closing = "closing"
    noise = "noise"


class SentimentValence(StrEnum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"
    urgent = "urgent"


class ClassificationOutput(BaseModel):
    message_type: MessageType
    information_density: float = Field(ge=0.0, le=1.0)
    action_required: bool
    action_urgency: ActionUrgency | None = None
    automation_candidate: bool
    automation_type: str | None = None
    thread_role: ThreadRole
    key_entities: list[str] = Field(default_factory=list)
    sentiment_valence: SentimentValence
    confidence: float = Field(ge=0.0, le=1.0)
