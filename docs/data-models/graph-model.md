# Data Model: Communication Graph

Stored in PostgreSQL with Apache AGE extension (Cypher query support).

## Node Types

### Person

Canonical identity — one per email address cluster.

| Property | Type | Description |
|----------|------|-------------|
| `display_name` | string | Best-known display name |
| `domain` | string | Primary email domain |
| `first_seen` | datetime | First message involving this person |
| `last_seen` | datetime | Most recent message |
| `internal` | bool | True if domain matches operator's domain(s) |

### Thread

Email conversation.

| Property | Type | Description |
|----------|------|-------------|
| `thread_id` | string | Computed from In-Reply-To chain |
| `subject_normalised` | string | Subject with Re:/Fwd: stripped |
| `start_date` | datetime | First message in thread |
| `message_count` | int | Total messages in thread |
| `participant_count` | int | Unique persons in thread |

### Topic

Extracted entity cluster (project/system/organisation names).

| Property | Type | Description |
|----------|------|-------------|
| `label` | string | Entity name |
| `first_seen` | datetime | First mention |
| `frequency` | int | Total mention count |

## Edge Types

### SENT_TO (Person → Person)

| Property | Type | Description |
|----------|------|-------------|
| `count` | int | Total messages sent from A to B |
| `last_at` | datetime | Most recent message |
| `avg_density` | float | Average information_density of messages A→B |
| `avg_response_latency_hrs` | float | Average response time in hours |

### PARTICIPATED_IN (Person → Thread)

| Property | Type | Description |
|----------|------|-------------|
| `message_count` | int | Messages this person sent in thread |
| `role` | enum | `initiator` or `contributor` |

### THREAD_REFERENCES (Thread → Topic)

| Property | Type | Description |
|----------|------|-------------|
| `mention_count` | int | Times topic mentioned in thread |

### REPORTS_TO (Person → Person)

| Property | Type | Description |
|----------|------|-------------|
| `source` | enum | `hr_feed` or `inferred` |
| `confidence` | float | 1.0 for HR feed, variable for inferred |

Populated from HR feed or inferred from signature parsing. See [Open Questions](../OPEN-QUESTIONS.md) — identity resolution.

## Identity Resolution (Open)

Multiple email addresses may represent the same person. A canonical identity resolver is needed before the graph is meaningful. Approaches:
- Display name matching + domain heuristics
- Reply-chain analysis
- HR feed integration

Scope and accuracy threshold TBD. See [Open Questions](../OPEN-QUESTIONS.md).
