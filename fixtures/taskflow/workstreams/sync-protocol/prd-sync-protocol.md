# PRD — SyncProtocol

**Blueprint:** `blueprints/BLUEPRINT-NOVA-P2-OfflineVault.yaml`
**Workstream ID:** `WS-5`
**Model tier:** `sonnet`
**Owner:** Feature Lead (RV)
**Depends on:** `[WS-4]`
**Status:** `NOT_STARTED`

> **FIXTURE.** Synthetic PRD for the TaskFlow NOVA fixture corpus. Nothing here describes real work.

---

## 1. Feature Overview

The wire protocol that drains the vault into the server and back. Three parts: op batching with a size ceiling, causal ordering carried by the mergeloom clock, and a resume handshake that lets a client that has been dark for half an hour catch up without a full resync.

**Source documents:**
- `wiki/sources/offline-sync-approaches.md`
- `wiki/raw/2026/08/2026-08-14-RV-crdt-library-eval.md`

**Locked decisions:**
- `D-0003`: mergeloom CRDT — the clock format is the library's, not ours.
- `D-0001`: the sync channel piggybacks on the existing socket rather than opening a second one.

## 2. Acceptance Criteria

- [ ] Two clients converge to an identical board state after an interleaved edit run.
- [ ] Resume handshake recovers from a 30-minute gap without a full resync.
- [ ] Version negotiation rejects an unknown major version with a typed error, not a crash.

## 3. Read / Write File Manifest

**Read only:** `lib/vault/wal.ts`, `decision-log/D-0003.md`
**Write / modify:** `lib/vault/index.ts`
**Create:** `lib/sync/protocol.ts`, `lib/sync/handshake.ts`, `lib/sync/protocol.test.ts`

## 4. CI Gate

```bash
npm run build && npx tsc --noEmit && npm run lint && npm run test:run
```

## 5. Session Protocol

Heartbeat to `PULSE.md` every ~30 min or at task boundaries. On completion generate `HANDOFF.md`. On block set `escalation_needed: true` and stop.

## 6. Out of Scope

- The user-facing merge queue (WS-6).
- Server-side storage of op history beyond the retention window.

## 7. Blockers

**Blockers:** None
