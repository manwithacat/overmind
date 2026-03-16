# Phase 3: Intelligence Layer & Dashboard (Weeks 13–20)

## Goal

Analytics API and dashboard with core views operational.

## Dependencies

- Phase 2 complete (messages flowing through pipeline, graph populated)

## Tasks

### 3.1 Implement Materialised View Aggregation
- Create materialised views for all derived metrics:
  - `attention_cost_index`
  - `communication_centrality` (PageRank variant)
  - `thread_entropy`
  - `automation_surface_score`
  - `response_latency_p50_p95`
- Implement 15-minute refresh scheduler
- Configurable aggregation windows

### 3.2 Build Intelligence Read API
- FastAPI application, JSON:API compliant
- Role-based access control (OVERMIND_admin, OVERMIND_viewer, OVERMIND_self)
- k-anonymity enforcement for viewer role
- Endpoints per [Intelligence Store spec](../components/intelligence-store.md)
- Authentication integration (token-based)

### 3.3 Build React Dashboard
- React 18.x SPA served by Caddy
- Dashboard views:
  - Org Communication Graph (force-directed, filterable)
  - Attention Cost Leaderboard (ranked, drilldown)
  - Automation Opportunity Queue (clustered by type)
- Role-aware: hide/show data based on user role

### 3.4 Self-Service Personal Metrics
- `/api/v1/graph/persons/{id}/self` endpoint
- Authenticated user sees only their own data
- Satisfies UK GDPR Article 15 right of access

### 3.5 DPIA Documentation
- Data Protection Impact Assessment template
- Privacy notice template for employees
- Legitimate Interest Assessment documentation

## Acceptance Criteria

- [ ] Materialised views refresh every 15 minutes
- [ ] API returns correct data for each role level
- [ ] k-anonymity enforced for viewer role (groups < 5 suppressed)
- [ ] Dashboard renders org graph, attention cost, automation queue
- [ ] Self-service endpoint returns authenticated user's own metrics
- [ ] DPIA template complete and ready for operator customisation
