-- Enable Apache AGE extension
CREATE EXTENSION IF NOT EXISTS age;
LOAD 'age';

-- Set search path to include ag_catalog
SET search_path = ag_catalog, "$user", public;

-- Create the overmind graph
SELECT create_graph('overmind');

-- Create vertex labels (node types)
SELECT create_vlabel('overmind', 'Person');
SELECT create_vlabel('overmind', 'Thread');
SELECT create_vlabel('overmind', 'Topic');

-- Create edge labels
SELECT create_elabel('overmind', 'SENT_TO');
SELECT create_elabel('overmind', 'PARTICIPATED_IN');
SELECT create_elabel('overmind', 'THREAD_REFERENCES');
SELECT create_elabel('overmind', 'REPORTS_TO');

-- Classification results storage (relational, for fast lookup)
CREATE TABLE IF NOT EXISTS classifications (
    id SERIAL PRIMARY KEY,
    message_id TEXT UNIQUE NOT NULL,
    message_type TEXT NOT NULL,
    information_density FLOAT NOT NULL,
    action_required BOOLEAN NOT NULL,
    action_urgency TEXT,
    automation_candidate BOOLEAN NOT NULL,
    automation_type TEXT,
    thread_role TEXT NOT NULL,
    key_entities TEXT[] DEFAULT '{}',
    sentiment_valence TEXT NOT NULL,
    confidence FLOAT NOT NULL,
    classified_at TIMESTAMPTZ DEFAULT NOW()
);

-- Materialised view: attention cost index (placeholder, populated by aggregation job)
CREATE TABLE IF NOT EXISTS metrics_attention_cost (
    person_email TEXT PRIMARY KEY,
    display_name TEXT,
    attention_cost_index FLOAT NOT NULL DEFAULT 0,
    message_count INT NOT NULL DEFAULT 0,
    avg_density FLOAT NOT NULL DEFAULT 0,
    computed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit log (append-only)
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    ts TIMESTAMPTZ DEFAULT NOW(),
    user_id TEXT,
    action TEXT NOT NULL,
    detail JSONB
);
