# Privacy Architecture & Legal Compliance

Designed for UK/EU jurisdictions. Must comply with UK GDPR and ICO Employment Practices Code.

## Data Minimisation (Non-Negotiable)

| Principle | Implementation |
|-----------|---------------|
| Message body NOT stored in intelligence layer | Only structured classification output is persisted |
| Full content retained ONLY in mail store | Stalwart/IMAP, subject to standard retention policies |
| BCC addresses NOT stored in graph | Only count is recorded |
| Attachment content NOT analysed or stored | Only MIME type metadata recorded |

## Transparency Requirements (UK GDPR Article 13/14)

Employees must be informed of processing activities at or before data collection.

### Operator Obligations

1. **Privacy notice update** — employee privacy notice must describe the communication analytics processing
2. **DPIA** — Data Protection Impact Assessment required prior to deployment. Profiling individuals via communication patterns = high-risk processing (Article 35)
3. **Legal basis** — Legitimate Interest Assessment (LIA) or explicit consent required
   - Legitimate interest is likely more defensible given organisational efficiency purpose
   - Three-part test must be documented

## Retention & Right to Erasure

| Item | Retention | Notes |
|------|-----------|-------|
| Graph nodes and edges | 24 months rolling (configurable) | Default |
| Audit log | 12 months | Immutable, append-only Postgres table with RLS |
| Mail content | Operator-defined | Managed by Stalwart retention policy |

### Article 17 — Right to Erasure

A deletion API endpoint accepts a person identifier and removes:
- All associated graph nodes
- All associated edges
- All materialised metrics referencing that person

## Outbound Monitoring (SENSITIVE — Open Question)

Inbound analysis is straightforward from consent perspective. Outbound analysis (monitoring what employees send externally) is more sensitive under the Employment Practices Code.

**Recommendation**: Legal advice required before activating outbound LLM processing. May require stronger legitimate interest justification or explicit consent.

See [Open Questions](../OPEN-QUESTIONS.md).
