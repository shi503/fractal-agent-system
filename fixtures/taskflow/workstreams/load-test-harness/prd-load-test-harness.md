# PRD — LoadTestHarness

**Blueprint:** `blueprints/BLUEPRINT-NOVA-P3-Hardening.yaml`
**Workstream ID:** `WS-7`
**Model tier:** `opus`
**Owner:** Feature Lead (CL)
**Depends on:** `[]`
**Status:** `NOT_STARTED`

> **FIXTURE.** Synthetic PRD for the TaskFlow NOVA fixture corpus. Nothing here describes real work.

---

## 1. Feature Overview

NOVA's GA gate is a number, and nobody can produce the number twice the same way. This workstream builds the harness: one command that drives both the notification channel and the vault sync channel at the self-host ceiling, records the distribution, and fails the run when a threshold in the gate table is breached.

**Source documents:**
- `wiki/sources/selfhost-resource-envelope.md`
- `wiki/raw/2026/08/2026-08-10-CL-selfhost-constraints.md`

**Locked decisions:**
- `D-0004`: proposed — a load-test gate must pass before GA. This workstream builds the instrument that decision will be measured with.

## 2. Acceptance Criteria

- [ ] A 500-subscriber board run reproduces from a single command with no manual setup.
- [ ] The run report records p50/p95/p99 per channel plus peak resident memory.
- [ ] The harness exits non-zero when any gate-table threshold is breached.

## 3. Read / Write File Manifest

**Read only:** `lib/notifications/fanout.ts`, `lib/sync/protocol.ts`, `decision-log/D-0004.md`
**Write / modify:** `package.json`
**Create:** `scripts/loadtest/run.ts`, `scripts/loadtest/gates.json`, `scripts/loadtest/README.md`

## 4. CI Gate

```bash
npm run build && npx tsc --noEmit && npm run lint && npm run test:run
```

## 5. Session Protocol

Heartbeat to `PULSE.md` every ~30 min or at task boundaries. On completion generate `HANDOFF.md`. On block set `escalation_needed: true` and stop.

## 6. Out of Scope

- Ratifying D-0004 itself — that is an owner decision, not a workstream deliverable.
- Continuous scheduled runs in CI — follow-up.

## 7. Blockers

**Blockers:** D-0004 is still `in_discovery`. The harness ships regardless; only the pass/fail thresholds in `gates.json` are provisional until the decision is answered.
