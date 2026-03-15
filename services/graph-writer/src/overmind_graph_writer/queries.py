"""Cypher queries for Apache AGE graph operations.

Apache AGE executes Cypher via ag_catalog.cypher(graph_name, query).
AGE does NOT support Cypher parameterisation through the SQL wrapper —
values must be interpolated into the Cypher string. We use Python string
formatting with proper escaping to prevent injection.
"""


def _age_escape(value: str) -> str:
    """Escape a string value for embedding in AGE Cypher."""
    return value.replace("\\", "\\\\").replace("'", "\\'")


def upsert_person_cypher(email: str, display_name: str, domain: str, internal: bool) -> str:
    """Generate full SQL to create or update a Person node."""
    e = _age_escape(email)
    dn = _age_escape(display_name)
    d = _age_escape(domain)
    i = "true" if internal else "false"
    return f"""
    SELECT * FROM ag_catalog.cypher('overmind', $$
        MERGE (p:Person {{email: '{e}'}})
        ON CREATE SET p.display_name = '{dn}', p.domain = '{d}',
                      p.internal = {i}, p.first_seen = timestamp(), p.last_seen = timestamp()
        ON MATCH SET p.last_seen = timestamp(), p.display_name = '{dn}'
        RETURN p
    $$) AS (v ag_catalog.agtype);
    """


def upsert_sent_to_cypher(sender: str, recipient: str, density: float) -> str:
    """Generate full SQL to create or update a SENT_TO edge."""
    s = _age_escape(sender)
    r = _age_escape(recipient)
    return f"""
    SELECT * FROM ag_catalog.cypher('overmind', $$
        MATCH (s:Person {{email: '{s}'}}), (r:Person {{email: '{r}'}})
        MERGE (s)-[e:SENT_TO]->(r)
        ON CREATE SET e.count = 1, e.last_at = timestamp(), e.avg_density = {density},
                      e.avg_response_latency_hrs = 0.0
        ON MATCH SET e.count = e.count + 1, e.last_at = timestamp(),
                     e.avg_density = (e.avg_density * (e.count - 1) + {density}) / e.count
        RETURN e
    $$) AS (e ag_catalog.agtype);
    """


def insert_classification_query() -> str:
    """SQL to insert classification result (uses psycopg parameterisation)."""
    return """
    INSERT INTO classifications (
        message_id, message_type, information_density, action_required,
        action_urgency, automation_candidate, automation_type, thread_role,
        key_entities, sentiment_valence, confidence
    ) VALUES (
        %(message_id)s, %(message_type)s, %(information_density)s, %(action_required)s,
        %(action_urgency)s, %(automation_candidate)s, %(automation_type)s, %(thread_role)s,
        %(key_entities)s, %(sentiment_valence)s, %(confidence)s
    ) ON CONFLICT (message_id) DO NOTHING;
    """


def upsert_attention_cost_query() -> str:
    """SQL to update the attention cost metric for a sender.

    Note: This is an incremental accumulator for the PoC. The production
    version should use a proper 30-day rolling window materialised view.
    """
    return """
    INSERT INTO metrics_attention_cost (person_email, display_name, attention_cost_index, message_count, avg_density)
    VALUES (%(email)s, %(display_name)s, %(cost)s, 1, %(density)s)
    ON CONFLICT (person_email) DO UPDATE SET
        attention_cost_index = metrics_attention_cost.attention_cost_index + %(cost)s,
        message_count = metrics_attention_cost.message_count + 1,
        avg_density = (metrics_attention_cost.avg_density * metrics_attention_cost.message_count + %(density)s)
                      / (metrics_attention_cost.message_count + 1),
        computed_at = NOW();
    """
