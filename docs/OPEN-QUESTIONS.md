# Open Questions & Deferred Design Decisions

These require resolution before or during Phase 2/3.

## 1. Thread Context Injection

**Status**: Unresolved — impacts Phase 2 (classification prompt)

**Problem**: The LLM prompt currently receives a single message. Injecting prior thread context would improve classification quality (especially `thread_role` and `automation_candidate`) but increases token consumption and latency.

**Options**:
- A) Fixed window — inject last N messages from thread
- B) Summarisation-based context compression — summarise thread before injecting

**Trade-offs**: Option A is simpler but token cost scales linearly. Option B adds an extra LLM call but caps token usage.

**Decision needed by**: Phase 2, Task 2.5 (classification worker implementation)

---

## 2. Identity Resolution

**Status**: Unresolved — impacts Phase 2 (graph model)

**Problem**: Multiple email addresses may represent the same person. The graph is not meaningful without canonical identity resolution.

**Approaches**:
- Display name + domain heuristics
- Reply-chain analysis (who replies to whom consistently)
- HR feed integration (authoritative mapping)

**Scope and accuracy threshold**: TBD

**Decision needed by**: Phase 2, Task 2.7 (graph write worker)

---

## 3. Roundcube Next Maturity

**Status**: Decision checkpoint at Week 3

**Problem**: Roundcube Next is under active development and may not be production-stable within Phase 1.

**Fallback**: Snappymail (mature, PHP, less modern UX)

**Decision needed by**: Week 3 of Phase 1

---

## 4. LLM Model Fine-Tuning

**Status**: Deferred to Phase 4+

**Problem**: Base instruction tuning is sufficient for MVP, but domain-specific fine-tuning on operator's email corpus could substantially improve classification accuracy.

**Requires**: Labelling pipeline, data governance framework (who labels, what supervision)

**Decision needed by**: Phase 4 planning

---

## 5. Outbound Monitoring Consent

**Status**: Unresolved — legal review required

**Problem**: Inbound analysis is straightforward from consent perspective. Outbound analysis (monitoring what employees send externally) is more sensitive under the Employment Practices Code.

**Options**:
- A) Stronger legitimate interest justification
- B) Explicit consent from employees

**Recommendation**: Legal advice required before activating outbound LLM processing.

**Decision needed by**: Phase 2 activation of outbound stream

---

## 6. Real-Time vs. Batch Processing

**Status**: Deferred pending use case validation

**Problem**: Current design processes messages asynchronously (near-real-time, typically <30 seconds). Some use cases (automated triage, intelligent auto-reply routing) would benefit from synchronous in-line processing before delivery.

**Impact**: Changes Stalwart integration significantly — milter-style blocking call vs. fire-and-forget.

**Decision needed by**: Phase 4+ (if use cases validated)
