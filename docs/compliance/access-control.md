# Access Control Model

## Roles

| Role | Access Level | Intended Users |
|------|-------------|---------------|
| `OVERMIND_admin` | Full dashboard access including individual-level metrics | C-suite, designated HR/legal personnel |
| `OVERMIND_viewer` | Aggregate and department-level metrics only. Individual data suppressed below k-anonymity threshold (default k=5) | Department managers, ops leads |
| `OVERMIND_self` | Own metrics only via self-service endpoint. Reinforced by UK GDPR Article 15 (right of access) | All employees |
| `mail_user` | Standard mail access only. No visibility of intelligence layer | All employees |

## k-Anonymity Enforcement

For `OVERMIND_viewer` role:
- Individual-level data is suppressed when group size < k (default k=5)
- Only aggregate and department-level data returned
- Prevents identification of individuals from small groups

## API Access Control

All Intelligence API endpoints enforce role-based access:
- Role determined from authentication token
- `OVERMIND_self` endpoints filter to authenticated user's own data only
- `OVERMIND_admin` required for deletion and webhook configuration
- All access logged to immutable audit table

## Audit Log

- All intelligence layer access is logged
- Retention: 12 months
- Immutable: append-only Postgres table with row-level security
- Fields: timestamp, user_id, role, endpoint, query_parameters
