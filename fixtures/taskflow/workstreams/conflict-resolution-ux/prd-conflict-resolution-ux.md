# PRD — ConflictResolutionUX

**Blueprint:** `blueprints/BLUEPRINT-NOVA-P2-OfflineVault.yaml`
**Workstream ID:** `WS-6`
**Model tier:** `sonnet`
**Owner:** Feature Lead (SP)
**Depends on:** `[WS-4, WS-5]`
**Status:** `NOT_STARTED`

> **FIXTURE.** Synthetic PRD for the TaskFlow NOVA fixture corpus. Nothing here describes real work.

---

## 1. Feature Overview

The small residue of merges the CRDT will not settle on its own — mostly a title rewritten on two devices — needs a human. This workstream builds the review queue that surfaces those cases, shows both candidate versions side by side, and writes the chosen winner back as a single op. It is the multi-edge workstream: it needs both the vault (WS-4) and the protocol (WS-5) in place.

**Source documents:**
- `wiki/raw/2026/08/2026-08-12-AR-offline-vault-design-session.md`
- `wiki/synthesis/nova-architecture-synthesis.md`

**Locked decisions:**
- `D-0003`: mergeloom settles ordering automatically; only same-field text rewrites reach the queue.

## 2. Acceptance Criteria

- [ ] Unsettled merges appear in the review queue with both candidate versions rendered.
- [ ] Choosing a winner writes exactly one op through the sync protocol.
- [ ] The queue is fully operable from the keyboard with no pointer-only affordance.

## 3. Read / Write File Manifest

**Read only:** `lib/sync/protocol.ts`, `lib/vault/wal.ts`
**Write / modify:** `app/(dashboard)/board/[boardId]/page.tsx`
**Create:** `components/vault/merge-queue.tsx`, `components/vault/candidate-diff.tsx`, `components/vault/merge-queue.test.tsx`

## 4. CI Gate

```bash
npm run build && npx tsc --noEmit && npm run lint && npm run test:run && npm run test:e2e
```

## 5. Session Protocol

Heartbeat to `PULSE.md` every ~30 min or at task boundaries. On completion generate `HANDOFF.md`. On block set `escalation_needed: true` and stop.

## 6. Out of Scope

- Changing what the CRDT considers settleable (that is a mergeloom-level decision).
- Bulk resolution across many cards — backlog.

## 7. Blockers

**Blockers:** None
