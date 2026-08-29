# HANDOFF — VaultStorageLayer

**Completed:** `2026-08-24`
**Blueprint:** `blueprints/BLUEPRINT-NOVA-P2-OfflineVault.yaml`
**Workstream PRD:** `workstreams/vault-storage-layer/prd-vault-storage-layer.md`

> **Synthetic fixture.** Fictional HANDOFF in the TaskFlow NOVA corpus, authored as an eval-template input and a handoff-schema validation target. No real work is described. See `fixtures/taskflow/README.md`.

---

## 1. Summary of Work Completed

- `lib/vault/wal.ts` — the IndexedDB-backed write-ahead log. `append(op)`, `since(cursor)`, `truncate(upTo)`. Ops are mergeloom ops per `D-0003`, stored encoded, never as raw diffs.
- `lib/vault/eviction.ts` — bounded-store policy. Soft bound 12 MB, hard bound 20 MB. On crossing the soft bound the store compacts acknowledged ops oldest-first; on crossing the hard bound it refuses new appends and surfaces a typed `VaultFullError` rather than failing silently.
- `lib/vault/clock.ts` — thin wrapper over the mergeloom clock so WS-5 has one import site for the ordering primitive.
- `lib/vault/wal.test.ts` — 31 cases including the hard-reload replay, the seeded deterministic eviction run, and the `VaultFullError` path.
- `lib/vault/index.ts` — public surface: `openVault`, `VaultFullError`, and the cursor type.

## 2. Summary of Work Not Completed

- **Cross-tab coordination** — two tabs on the same origin each open their own vault handle. Out of scope in the PRD; the sync protocol (WS-5) currently makes this harmless because both drain to the same server state, but it is wasteful.

## 3. Technical Debt Register

- **What:** Eviction runs on the main thread.
  **Why:** A worker adds a message-passing boundary around the one structure that must not lose writes; the measured incremental compaction stayed under 8 ms per pass, which is inside a frame budget.
  **Remediation:** Move to a worker if WS-7's harness shows a stall on a large board. Owner: RV.

- **What:** The 12 MB / 20 MB bounds are constants derived from a survey of typical board sizes, not measured against real usage.
  **Why:** No production telemetry exists for a feature that has not shipped.
  **Remediation:** Revisit after the first harness run. Related to the provisional thresholds on `D-0004`.

- **What:** `VaultFullError` is surfaced but the UI treatment is a plain toast.
  **Why:** The vault-full case is a WS-6 surface and WS-6 has not started.
  **Remediation:** WS-6 owns the real treatment.

## 4. Key Decisions Made

- **Decision:** Two bounds (soft compaction, hard refusal) instead of one.
  **Reasoning:** The PRD asked for a deterministic eviction policy and a bounded store. A single bound forces a choice between evicting unacknowledged ops (data loss) and unbounded growth. Two bounds let compaction reclaim acknowledged ops while refusing to ever discard an unacknowledged one.
  **Impact:** A user who works offline past the hard bound is told, loudly, rather than quietly losing work. This is the vault's expression of the `D-0003` residue rule.

- **Decision:** Eviction is seeded and deterministic in test, wall-clock ordered in production.
  **Reasoning:** The acceptance criterion demanded a deterministic, testable policy; wall-clock ordering is not reproducible in CI.
  **Impact:** `eviction.ts` takes an injectable ordering source. One extra parameter; the test asserts an exact eviction sequence.

## 5. Deterministic Eval Results (Layer 1)

| Command | Result | Notes |
|---|---|---|
| `npm run build` | **PASS** | — |
| `npx tsc --noEmit` | **PASS** | strict mode, 0 errors |
| `npm run lint` | **PASS** | 0 errors, 0 warnings |
| `npm run test:run` | **PASS** | 31/31 new, 268/268 total |
| `npm run test:e2e` | **PASS** | 21/21; includes the hard-reload replay flow |

Peak heap during the replay test: **214 MB**, inside the ~320 MB app-process headroom published in `wiki/sources/selfhost-resource-envelope.md`. Recorded here because it is an acceptance criterion, not merely a nice number.

## 6. Verification for Reviewer

1. `git diff main..HEAD -- lib/vault/` — the change surface.
2. `npm run test:run -- eviction` — confirms the seeded run evicts in the asserted order.
3. `npm run test:e2e -- reload` — confirms zero lost writes across a hard reload.
4. `npm run test:run -- wal --heap` — prints the peak heap figure quoted above.

## 7. Next Steps / Handoff Notes

- WS-5 (`FeatureLead-SyncProtocol`) is unblocked. It should import the clock from `lib/vault/clock.ts`, not from mergeloom directly, so a library swap stays inside one module.
- WS-6 (`FeatureLead-ConflictResolutionUX`) remains blocked — it depends on both this workstream and WS-5, and WS-5 has not started.
- Open question surfaced: nothing decides what happens to the vault when a user is removed from a board while offline. The ops are retained and will be rejected on drain. Whether the user should be told, and how, is unowned.
