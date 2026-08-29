---
okf_version: "0.2"
type: note
title: "Self-host resource envelope — memory and CPU ceiling"
tier: raw
initiative: NOVA
created: "2026-08-10"
updated: "2026-08-10"
created_by: CL
updated_by: CL
status: ACTIVE
tags: [nova, selfhost, infrastructure, resources]
---

# Self-host resource envelope — memory and CPU ceiling

Written down so NOVA has a ceiling to design against instead of an assumption. Numbers come from the deployment survey plus the two reference boxes CL keeps for reproduction.

## The modal self-host box

The typical TaskFlow self-hoster runs a single small VM or a home server: two vCPU, four gigabytes of RAM, one app process, one Postgres, both on the same host. A meaningful minority run on a one-vCPU / two-gigabyte instance because it is the free tier of their provider.

## Budget

| Component | Steady-state RAM | Ceiling |
|---|---|---|
| App process (Node) | 380 MB | 700 MB |
| Postgres | 512 MB | 900 MB |
| OS + reverse proxy | 250 MB | 400 MB |
| Headroom | — | ~1 GB on a 4 GB box |

The number that matters for NOVA: the app process gets about **320 MB of new headroom** before a 4 GB box starts swapping, and roughly zero on a 2 GB box. Any per-connection state must therefore be small and bounded. A subscriber table entry that costs a kilobyte is fine at a thousand connections; one that costs a hundred kilobytes is not.

## CPU

Two vCPU means a serial per-event loop competes directly with request handling. CL's rule of thumb: any per-event work that is O(subscribers) needs to stay under a millisecond per subscriber, or a busy board starves the request path on a small box.

## Browser side

Self-hosters are not the constraint here — their browsers are ordinary. But the offline store lives in the browser, and IndexedDB quota on a shared origin is not guaranteed. Design for a bounded store with an eviction policy rather than an unbounded log.

## Recommendation

Publish these numbers as the envelope in `wiki/sources/selfhost-resource-envelope.md` and gate the GA decision on a measured run against a 2 vCPU / 4 GB box, not a developer laptop.
