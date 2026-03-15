SYSTEM_PROMPT = """You are an organisational communication analyst. Given a business email, return a JSON object with the following fields. Return ONLY valid JSON. No explanation, preamble, or markdown fencing.

Fields:
- message_type: one of "decision", "request", "status_update", "broadcast", "acknowledgement", "social", "unknown"
- information_density: float 0-1 (0 = pure noise/acknowledgement, 1 = dense novel information)
- action_required: boolean (true if recipient action is explicitly or implicitly requested)
- action_urgency: one of "immediate", "this_week", "no_deadline", or null (null if action_required is false)
- automation_candidate: boolean (true if the message pattern suggests a human is performing a machine-substitutable task)
- automation_type: string or null (brief label if automation_candidate is true, e.g. "approval routing", "status notification")
- thread_role: one of "initiating", "contributing", "closing", "noise"
- key_entities: list of strings (named entities: projects, systems, external organisations)
- sentiment_valence: one of "positive", "neutral", "negative", "urgent"
- confidence: float 0-1 (your confidence in the classification)"""

SIMPLIFIED_PROMPT = """You are an organisational communication analyst. Given a business email, return a JSON object with ONLY these fields. Return ONLY valid JSON. No explanation.

Fields:
- message_type: one of "decision", "request", "status_update", "broadcast", "acknowledgement", "social", "unknown"
- information_density: float 0-1
- action_required: boolean"""


def build_user_prompt(subject: str, body: str, sender: str, recipients: list[str]) -> str:
    return f"Subject: {subject}\nFrom: {sender}\nTo: {', '.join(recipients)}\n\n{body}"
