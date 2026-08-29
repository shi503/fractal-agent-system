---
okf_version: "0.2"
type: source
title: "Self-host resource envelope — the published ceiling"
tier: sources
initiative: NOVA
created: "2026-08-11"
updated: "2026-08-11"
created_by: CL
updated_by: CL
status: ACTIVE
source:
  - wiki/raw/2026/08/2026-08-10-CL-selfhost-constraints.md
tags: [nova, selfhost, infrastructure, budget]
---

# Self-host resource envelope — the published ceiling

This page is the number NOVA designs against. Cite it rather than re-deriving a budget.

## Reference box

Two vCPU, four gigabytes of RAM, single app process plus Postgres on the same host. A meaningful minority of deployments run half that.

## Memory budget

| Component | Steady state | Ceiling |
|---|---|---|
| App process | 380 MB | 700 MB |
| Postgres | 512 MB | 900 MB |
| OS and reverse proxy | 250 MB | 400 MB |

**Available headroom for NOVA on the app process: ~320 MB.** On a two-gigabyte deployment: effectively none.

## Derived design rules

1. **Per-connection state must be small and bounded.** A kilobyte per subscriber is fine at a thousand connections; a hundred kilobytes is not.
2. **Per-event work that is O(subscribers) must stay under a millisecond per subscriber.** Two vCPU means that loop competes with the request path directly.
3. **The browser store must be bounded with a deterministic eviction policy.** Origin storage quota is not guaranteed, and an unbounded local log becomes a support ticket.
4. **Gate on a measured run against the reference box**, never a developer laptop.

## What this rules out

Anything that materialises a full board document per connection on the server. Anything that holds an unbounded history in process. Anything whose steady-state cost grows with total workspace size rather than with active connections.

Raw derivation and the survey it came from: `wiki/raw/2026/08/2026-08-10-CL-selfhost-constraints.md`.
