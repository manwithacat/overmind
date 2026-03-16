# Component: Analytics Dashboard

## Responsibility

Visual interface for querying and exploring organisational communication intelligence.

## Technology

- **React SPA** (React 18.x, MIT licence)
- Served by Caddy (same reverse proxy as mail)
- Consumes Intelligence API (read-only, JSON:API)

## Access Control

- `OVERMIND_admin` — full dashboard including individual-level metrics
- `OVERMIND_viewer` — aggregate and department-level only (k-anonymity enforced)
- See [Access Control](../compliance/access-control.md)

## Dashboard Views

### 1. Org Communication Graph

- **Primary metric**: Edge weight / centrality
- Force-directed graph of SENT_TO relationships
- Filterable by: date range, domain boundary (internal/external), department
- Interactive: click node to drill into person detail

### 2. Attention Cost Leaderboard

- **Primary metric**: `attention_cost_index`
- Ranked list of senders by attention cost imposed
- Drilldown to message samples (classification data, not message content)

### 3. Information Density Heatmap

- **Primary metric**: average `information_density`
- Per-sender and per-department density scores over time
- Identifies structural noise sources

### 4. Automation Opportunity Queue

- **Primary metric**: `automation_surface_score`
- Clustered view of `automation_candidate` messages grouped by `automation_type`
- Shows estimated volume and regularity per cluster

### 5. Thread Health Monitor

- **Primary metric**: `thread_entropy`
- Flags runaway threads: high participant count + low information density
- Sortable by entropy, participant count, message count

### 6. Response Latency Map

- **Primary metric**: `latency_p50` / `latency_p95`
- Department-level response time matrix for `action_required=true` messages
- Identifies bottlenecks in response chains

## Export & Integration

| Feature | Description |
|---------|-------------|
| CSV export | All materialised metrics — for BI tools (Metabase, Superset) |
| Webhook notifications | Configurable alerts when `attention_cost_index` or `automation_surface_score` crosses thresholds |
| REST API | Full read access to graph and metrics for custom tooling |
| Slack/Teams digest | Weekly digest notification to nominated channel (optional) |
