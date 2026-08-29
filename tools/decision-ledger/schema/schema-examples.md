# Decision Ledger v2 — Schema Examples

One fully-populated example per entry type. These are canonical round-trip examples:
the validate CLI must pass every block below without errors (importer regression test).

Each example is a synthetic entry for the TaskFlow project, distinct from the
`fixtures/taskflow/decision-log/D-0001..D-0004.md` fixture corpus, so the two sets
never collide on ID.

---

## Example 1 — `discovery` (D-NNNN)

**v2 file:** `decision-log/D-9001.md`

```yaml
---
id: D-9001
type: discovery
layer: L4
title: "Rate limit shape for the public webhook API"
owner: RV
status: open
raci:
  responsible: [RV]
  accountable: [AR]
  consulted: [CL]
  informed: [TN]
created: 2026-08-18T14:31:00Z
updated: 2026-08-20T09:15:00Z
created_by: RV
updated_by: RV
cross_refs:
  - D-9002
---

## Context

The public webhook API has no documented rate limit. As self-hosters start
wiring TaskFlow into their own automation, unbounded retry storms are starting
to show up in the access logs.

## Answer

_Not yet answered. Candidate shapes: fixed-window per API key, or a token
bucket keyed on the workspace. See D-9002 for the related quota-display work._
```

---

## Example 2 — `critical_decision` (CD-N)

**v2 file:** `decision-log/CD-1.md`

```yaml
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
evaluation (see the NOVA discovery log for the related architecture thread).

**Rationale:** de-risking the vault's library choice before committing a
sprint to it avoids a rewrite mid-quarter.

## Addenda

- 2026-07-08: [AR-A] Initial framing — three workstreams considered in scope.
- 2026-07-15: [AR-A] Amended — vault deferred to Q4 after CL flagged the
  library-evaluation dependency.
```

---

## Example 3 — `big_idea` (BI-NN)

**v2 file:** `decision-log/BI-1.md`

```yaml
---
id: BI-1
type: big_idea
title: "Workspace-level automation rules"
owner: TN
status: in_discovery
raci:
  responsible: [TN]
  accountable: [AR]
  consulted: [RV, SP]
  informed: [CL]
created: 2026-08-01T00:00:00Z
updated: 2026-08-10T09:00:00Z
created_by: TN
updated_by: TN
unlocks:
  - D-9001
cross_refs:
  - D-9001
tags:
  - automation
  - workspace
---

## Context

A rules engine ("when a card enters column X, do Y") sits upstream of several
open questions — the webhook rate-limit shape (D-9001), the notification
fanout's event schema, and the preference center's default cadence.

Key capabilities unlocked:
- Self-serve automation without a support ticket
- A natural home for the webhook-delivery rate-limit work
- A reusable trigger surface for future integrations

## Answer

_In discovery. Scoping a minimal rules engine (trigger + one action) as the
Q4 wedge; the full condition/action matrix is a later phase._
```

---

## Example 4 — `layer_item` (L#-NN)

**v2 file:** `decision-log/L2-01a.md`

```yaml
---
id: L2-01a
type: layer_item
layer: L2
title: "Preference center default-view contract (v2 revision)"
owner: SP
status: pending_signoff
raci:
  responsible: [SP]
  accountable: [AR]
  consulted: [TN, RV]
  informed: [CL]
created: 2026-08-05T00:00:00Z
updated: 2026-08-19T00:00:00Z
created_by: SP
updated_by: SP
cross_refs:
  - D-9001
  - CD-1
superseded_by: null
tags:
  - preference-center
  - l2
---

## Context

L2-01a is the contract governing the preference center's default rendering
when a user has no stored preference row. v0.2 tightened the shape after the
digest-cadence research landed.

## Answer

**[SP-R 2026-08-19]:** Design review complete. Contract is v0.2-stable and
matches the notification-defaults decision.

**[AR-A]:** Sign-off pending — waiting on the accessibility pass on the
digest surface before ratifying.

## Addenda

- 2026-08-19: Flagged as needing a re-check once the accessibility audit
  lands; kept `pending_signoff` until then.
```

---

## Round-trip notes for the importer

The four examples above represent the full shape space of v1 entries:

| Dimension | Covered by |
|-----------|-----------|
| All four entry types | Examples 1–4 |
| All six status values | open (Ex1), answered (Ex2), in_discovery (Ex3), pending_signoff (Ex4); conflicted + deferred have same shape as open/answered |
| Multi-item RACI | Example 2 (3 roles populated) |
| Optional fields absent | Example 1 (no `options`, no `unlocks`) |
| Optional fields present | Examples 2–4 |
| `superseded_by` field | Example 4 (explicit null) |
| Free-text addenda | Examples 2 and 4 |
| Embedded lists in body | Example 3 (`unlocks` list) |
| Multi-line answer with sub-bullets | Example 2 |
| Layer-scoped ID with suffix | Example 4 (`L2-01a`) |

Edge cases the importer must handle:
- `id` suffix letters (e.g., `L2-01a`, `D-9001a`) — covered by `id_pattern` in schema.yaml
- `superseded_by: null` explicit null vs. field absent — both valid; normalize to absent on export
- Free-text addenda with embedded markdown tables — stored in body, not frontmatter; no schema constraint
- Activity Log rows — not a per-entry type; generated view only (not imported as typed entries)
