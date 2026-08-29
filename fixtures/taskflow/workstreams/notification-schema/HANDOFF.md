# HANDOFF — NotificationSchema

**Completed:** `2026-08-11`
**Blueprint:** `blueprints/BLUEPRINT-NOVA-P1-NotificationCore.yaml`
**Workstream PRD:** `workstreams/notification-schema/prd-notification-schema.md`

> **Synthetic fixture.** Fictional HANDOFF in the TaskFlow NOVA corpus, authored as an eval-template input and a handoff-schema validation target. No real work is described. See `fixtures/taskflow/README.md`.

---

## 1. Summary of Work Completed

- `prisma/schema.prisma` — added `Notification`, `NotificationDelivery`, and the `NotificationCategory` enum. `NotificationDelivery` carries `cursor BigInt` (monotonic, board-scoped) so the fanout service can range-scan a reconnecting client's backlog without a join.
- `lib/notifications/types.ts` — exported `NotificationCategory`, `NotificationPayload`, and `DeliveryCursor`. Every downstream workstream imports from here rather than from the generated Prisma client, so a schema rename does not ripple into UI code.
- `lib/notifications/idempotency.ts` — `buildIdempotencyKey({resource, id, event})` returning `{resource}-{id}-{event}`. Producers must call it; the raw string form is not exported.
- `lib/notifications/idempotency.test.ts` — 11 cases covering the format contract, collision behaviour on a retried producer, and rejection of empty segments.
- `prisma/migrations/20260810_nova_notification_core/migration.sql` — generated, applied clean on a fresh database and on a seeded one.

## 2. Summary of Work Not Completed

None. All four acceptance criteria shipped.

## 3. Technical Debt Register

- **What:** `NotificationDelivery.cursor` is board-scoped rather than globally monotonic.
  **Why:** A global sequence needs a shared counter, which conflicts with the single-process assumption in `D-0001`'s impact section. Board-scoped is correct for Phase 1 and is a schema change, not a rewrite, if that assumption ever falls.
  **Remediation:** Revisit when multi-process deployment is scoped. Owner: RV.

- **What:** The category enum is stored as a Postgres enum, not a lookup table.
  **Why:** Six categories, all known, and enum comparison is cheaper on the small reference box.
  **Remediation:** Convert only if user-defined categories are ever scoped. No owner; not currently planned.

## 4. Key Decisions Made

- **Decision:** Export domain types from `lib/notifications/types.ts` instead of re-exporting Prisma's generated types.
  **Reasoning:** The PRD did not specify. Re-exporting generated types couples every UI import to the ORM.
  **Impact:** WS-2 and WS-3 import from one module; a column rename stays inside the data layer.

- **Decision:** Suppression of self-caused events is enforced in the schema layer as a non-nullable `actorId` on `Notification`, not left to the fanout query.
  **Reasoning:** `D-0002` makes suppression non-overridable; making the actor structurally present means WS-2 cannot forget to filter.
  **Impact:** Producers must supply an actor. One seed script was updated.

## 5. Deterministic Eval Results (Layer 1)

| Command | Result | Notes |
|---|---|---|
| `npx prisma generate` | **PASS** | client regenerated, no drift |
| `npx prisma migrate dev` | **PASS** | applies clean on fresh and seeded databases |
| `npm run build` | **PASS** | — |
| `npx tsc --noEmit` | **PASS** | strict mode, 0 errors |
| `npm run lint` | **PASS** | 0 errors, 0 warnings |
| `npm run test:run` | **PASS** | 11/11 new, 214/214 total |
| `npm run test:e2e` | **N/A** | no UI surface in this workstream |

## 6. Verification for Reviewer

1. `git diff main..HEAD -- prisma/ lib/notifications/` — the whole change surface.
2. `npx prisma migrate reset && npx prisma migrate dev` — confirms the migration applies from empty.
3. `npm run test:run -- idempotency` — confirms the key contract is enforced, not merely documented.

## 7. Next Steps / Handoff Notes

- WS-2 (`FeatureLead-EventFanout`) and WS-3 (`FeatureLead-PreferenceCenter`) are both unblocked; their `depends_on` is satisfied.
- WS-2 should range-scan on `(boardId, cursor)`; the composite index exists.
- Open question surfaced: nothing in the schema prevents a producer from emitting two logically distinct events with the same idempotency key. The test documents the behaviour (second write is ignored) but the product answer is unconfirmed.
