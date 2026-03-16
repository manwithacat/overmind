# Data Model: Derived Metrics (Materialised Views)

Updated every 15 minutes by a scheduled aggregation job.

## Metrics

### attention_cost_index

**Per sender**: `sum(recipient_count × message_density_inverse)` across sent messages.

- High score = high attention cost relative to information delivered
- A person who sends many low-density messages to large recipient lists scores highest
- Use: identify individuals/processes imposing disproportionate cognitive load

### communication_centrality

PageRank variant on the SENT_TO graph.

- Identifies informal communication hubs not visible in org chart
- Use: find people who are de facto information bottlenecks or bridges

### thread_entropy

Measures how widely a thread's participants sprawl relative to its information content.

- High entropy + low density = broadcast noise
- Use: flag runaway threads, identify over-distribution

### automation_surface_score

Per `message_type` cluster: fraction flagged as `automation_candidate`.

- Identifies process families ripe for workflow replacement
- Use: prioritise automation investments by volume and regularity

### response_latency_p50_p95

Per person and per department: median and 95th percentile response times.

- Segmented by `action_required=true` messages only
- Use: identify bottlenecks in response chains, department-level SLA tracking

## SQL Schema (indicative)

```sql
-- Materialised view: attention cost index
CREATE MATERIALIZED VIEW mv_attention_cost AS
SELECT
    sender_id,
    SUM(recipient_count * (1.0 - information_density)) AS attention_cost_index,
    COUNT(*) AS message_count,
    AVG(information_density) AS avg_density
FROM classifications c
JOIN normalised_messages m ON c.message_id = m.message_id
WHERE m.received_at > NOW() - INTERVAL '30 days'
GROUP BY sender_id;

-- Refresh schedule: every 15 minutes
```

## Aggregation Windows

| Metric | Default Window | Configurable |
|--------|---------------|-------------|
| attention_cost_index | 30 days rolling | Yes |
| communication_centrality | 90 days rolling | Yes |
| thread_entropy | Per thread lifetime | N/A |
| automation_surface_score | 90 days rolling | Yes |
| response_latency_p50_p95 | 30 days rolling | Yes |
