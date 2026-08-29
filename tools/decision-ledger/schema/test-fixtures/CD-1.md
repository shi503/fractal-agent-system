---
id: CD-1
type: critical_decision
title: "Q3 scope: what ships vs. what waits?"
owner: AR
status: answered
raci:
  responsible: [AR]
  accountable: [AR]
  consulted: [RV, SP, TN]
  informed: [CL]
created: 2026-07-01T00:00:00Z
updated: 2026-07-15T00:00:00Z
created_by: AR
updated_by: AR
options:
  - "Full scope: notification fanout + offline vault + preference center"
  - "Reduced scope: notification fanout + preference center; offline vault deferred"
cross_refs:
  - D-9001
---

## Context

All delivery planning and sprint allocation depend on this decision. The
offline vault carries meaningfully higher implementation risk than the other
two workstreams.

## Answer

**[AR-A 2026-07-15]:** Q3 ships the notification fanout service and the
preference center. The offline vault moves to Q4 pending the CRDT library
evaluation.

**Rationale:** de-risking the vault's library choice before committing a
sprint to it avoids a rewrite mid-quarter.

## Addenda

- 2026-07-08: [AR-A] Initial framing — three workstreams considered in scope.
- 2026-07-15: [AR-A] Amended — vault deferred to Q4 after CL flagged the
  library-evaluation dependency.
