# PRD — VaultStorageLayer

**Blueprint:** `blueprints/BLUEPRINT-NOVA-P2-OfflineVault.yaml`
**Workstream ID:** `WS-4`
**Model tier:** `opus`
**Owner:** Feature Lead (RV)
**Depends on:** `[]`
**Status:** `COMPLETE`

> **FIXTURE.** Synthetic PRD for the TaskFlow NOVA fixture corpus. Nothing here describes real work.

---

## 1. Feature Overview

The browser-side vault that lets a board keep accepting edits with no network: an IndexedDB write-ahead log with a bounded quota, a monotonic replay cursor, and an eviction policy that is deterministic enough to test. The self-host memory envelope is the hard constraint the eviction policy is tuned against.

**Source documents:**
- `wiki/sources/selfhost-resource-envelope.md`
- `wiki/sources/offline-sync-approaches.md`

**Locked decisions:**
- `D-0003`: mergeloom is the CRDT library — the vault stores mergeloom ops, not raw diffs.

## 2. Acceptance Criteria

- [ ] Hard reload replays every pending write with zero loss.
- [ ] Quota eviction is deterministic and asserted by a unit test with a fixed seed.
- [ ] Peak heap during the replay test stays inside the documented self-host envelope.

## 3. Read / Write File Manifest

**Read only:** `wiki/sources/selfhost-resource-envelope.md`, `decision-log/D-0003.md`
**Write / modify:** `lib/vault/index.ts`
**Create:** `lib/vault/wal.ts`, `lib/vault/eviction.ts`, `lib/vault/wal.test.ts`

## 4. CI Gate

```bash
npm run build && npx tsc --noEmit && npm run lint && npm run test:run
```

## 5. Session Protocol

Heartbeat to `PULSE.md` every ~30 min or at task boundaries. On completion generate `HANDOFF.md`. On block set `escalation_needed: true` and stop.

## 6. Out of Scope

- The wire protocol (WS-5).
- Any user-facing merge surface (WS-6).

## 7. Blockers

**Blockers:** None
