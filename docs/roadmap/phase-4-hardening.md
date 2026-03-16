# Phase 4: Hardening & Extended Analytics (Weeks 21–28)

## Goal

Production-ready deployment with advanced analytics and integration hooks.

## Dependencies

- Phase 3 complete (dashboard and API operational)

## Tasks

### 4.1 k-Anonymity Enforcement (Hardening)
- Review and harden k-anonymity in all viewer role API responses
- Edge cases: small departments, new employees, time-windowed queries that reduce group size
- Automated tests for k-anonymity violation

### 4.2 Deletion API & Audit Log
- DELETE endpoint: accepts person identifier, removes all graph nodes, edges, materialised metrics
- Article 17 (right to erasure) compliance
- Audit log: append-only Postgres table with row-level security
- Log all intelligence layer access (12-month retention)

### 4.3 Webhook Notification System
- Configurable threshold alerts for:
  - `attention_cost_index` exceeds threshold
  - `automation_surface_score` exceeds threshold
  - Custom metric thresholds
- Webhook delivery with retry logic

### 4.4 BI Tool Integration
- Metabase/Superset integration guide
- Pre-built dashboard templates
- CSV export for all materialised metrics

### 4.5 Mobile Client
- React Native application
- JMAP client (jmap-client-ts)
- Standard mail operations: compose, read, search, folders
- Intelligence annotation sidebar (condensed for mobile)
- Web push notifications

### 4.6 Load Testing & Scaling Documentation
- Load test at 500-user scale
- GPU inference scaling benchmarks
- Document scaling thresholds and recommendations

### 4.7 Operator Deployment Artefacts
- Kubernetes manifests
- Helm chart
- Deployment guide
- Configuration reference

## Acceptance Criteria

- [ ] Deletion API removes all traces of a person from intelligence layer
- [ ] Audit log captures all intelligence layer access
- [ ] Webhook notifications fire when thresholds crossed
- [ ] Mobile client sends/receives mail with intelligence annotations
- [ ] System tested at 500-user sustained load
- [ ] Helm chart deploys full stack to Kubernetes
