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
    action_urgency: ActionUrgency | None = None
    automation_candidate: bool
    automation_type: str | None = None
    thread_role: ThreadRole
    key_entities: list[str] = Field(default_factory=list)
    sentiment_valence: SentimentValence
    confidence: float = Field(ge=0.0, le=1.0)
