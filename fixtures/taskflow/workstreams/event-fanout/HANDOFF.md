# HANDOFF — EventFanout

**Completed:** `2026-08-16`
**Blueprint:** `blueprints/BLUEPRINT-NOVA-P1-NotificationCore.yaml`
**Workstream PRD:** `workstreams/event-fanout/prd-event-fanout.md`

> **Synthetic fixture.** Fictional HANDOFF in the TaskFlow NOVA corpus, authored as an eval-template input and a handoff-schema validation target. No real work is described. See `fixtures/taskflow/README.md`.

---

## 1. Summary of Work Completed

- `lib/notifications/fanout.ts` — `fanout(event)` expands a domain event to eligible subscribers, filters by stored preferences and by the unconditional self-caused suppression, writes one `NotificationDelivery` row per subscriber, and enqueues one pre-encoded frame per socket.
- `lib/notifications/channel.ts` — socket registry plus the bounded outbound queue. Queue depth 64 per socket; on overflow the frame is dropped and a `fanout.drop` counter is incremented with the board id. Drops are never silent.
- `lib/notifications/replay.ts` — replay window. On reconnect the client sends its last cursor and receives up to 200 undelivered events in order.
- `lib/notifications/fanout.test.ts` — 23 cases: exactly-once delivery, self-caused suppression, preference filtering, the drop path, and cursor ordering under interleaved writes.
- `lib/notifications/index.ts` — re-exports the public surface.

Implementation follows all four conditions attached to `D-0001`: the frame is encoded once per event (condition 1), the per-socket queue is bounded with drop-and-record (condition 2), the replay window ships (condition 3), and the proxy idle-timeout requirement is documented in `docs/self-hosting/websockets.md` (condition 4).

## 2. Summary of Work Not Completed

- **Multi-process subscriber bus** — not built. Explicitly out of scope per `D-0001`'s impact section: the subscriber table is per-process, and a second app process would need a shared bus. Single-process deployments are the entire Phase 1 target.

## 3. Technical Debt Register

- **What:** Queue depth 64 is a constant, not configuration.
  **Why:** Nobody has a number yet — the load harness (WS-7) has not run. Making it configurable before there is a baseline invites self-hosters to tune it wrongly.
  **Remediation:** Promote to configuration once WS-7 produces a baseline. Owner: RV. Tracked on `D-0004`.

- **What:** Preference filtering re-reads the preference row per event rather than caching it per socket.
  **Why:** Correctness first; the read is indexed and the profile did not show it.
  **Remediation:** Cache per socket with invalidation on preference write if the harness shows it matters.

- **What:** `fanout.drop` increments a counter but does not sample the dropped payload.
  **Why:** Sampling payloads risks logging content; deferred pending a decision on what is safe to record.
  **Remediation:** Decide the sampling policy before GA.

## 4. Key Decisions Made

- **Decision:** Drop-and-record rather than disconnect-the-slow-client.
  **Reasoning:** `D-0001` condition 2 forbids blocking but does not say what to do with the client. Disconnecting turns one slow network into a reconnect storm; dropping degrades one client only, and the replay window recovers it.
  **Impact:** A slow client sees gaps until it reconnects. Documented in the self-hosting notes.

- **Decision:** Replay is capped at 200 events, then the client is told to do a full refetch.
  **Reasoning:** The PRD specified 200 as the window; it did not say what happens past it. An unbounded replay on a long absence would defeat the resource envelope.
  **Impact:** A client dark for a very long time takes one extra round trip.

## 5. Deterministic Eval Results (Layer 1)

| Command | Result | Notes |
|---|---|---|
| `npm run build` | **PASS** | — |
| `npx tsc --noEmit` | **PASS** | strict mode, 0 errors |
| `npm run lint` | **PASS** | 0 errors, 0 warnings |
| `npm run test:run` | **PASS** | 23/23 new, 237/237 total |
| `npm run test:e2e` | **PASS** | 18/18; includes the reconnect-replay flow |

## 6. Verification for Reviewer

1. `git diff main..HEAD -- lib/notifications/` — the change surface.
2. `npm run test:run -- fanout` — confirms exactly-once delivery and the drop path.
3. `npm run test:e2e -- reconnect` — kills the socket mid-run and asserts no duplicates after replay.
4. Read `docs/self-hosting/websockets.md` — confirms condition 4 shipped as documentation.

## 7. Next Steps / Handoff Notes

- Phase 1 is complete once WS-3 lands; WS-3 was never blocked on this workstream.
- WS-5 (`FeatureLead-SyncProtocol`) will ride this channel — `channel.ts` exposes a `registerProtocol(id, handler)` seam for that, currently with one registered protocol.
- WS-7 should drive `fanout()` directly rather than through HTTP so the harness measures fanout cost, not request overhead.
