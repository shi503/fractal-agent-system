---
okf_version: "0.2"
type: source
title: "Notification architecture options — one-page summary"
tier: sources
initiative: NOVA
created: "2026-08-05"
updated: "2026-08-06"
created_by: AR
updated_by: RV
status: ACTIVE
source:
  - wiki/raw/2026/08/2026-08-03-AR-notification-options-whiteboard.md
  - wiki/raw/2026/08/2026-08-04-RV-websocket-spike-notes.md
tags: [nova, notifications, architecture, transport]
---

# Notification architecture options — one-page summary

Distilled from the 2026-08-03 whiteboard and the 2026-08-04 spike. This page is the input to D-0001.

## The three options as they stood

| Option | Server cost | Freshness floor | Reuse in Phase 2 | Verdict |
|---|---|---|---|---|
| Poll the inbox | high and constant | the poll interval | none | rejected |
| Server-sent events | low | none | half — one direction only | rejected |
| WebSocket fanout | low, bounded by subscriber count | none | full — the vault reuses the channel | **recommended** |

## Why polling lost

Its cost is inverted: a quiet workspace generates the most waste. Worse, the poll interval is a hard floor on staleness, and staleness is the complaint that started NOVA.

## Why server-sent events lost

Cheap and proxy-friendly, but one-directional, so client actions still need separate requests. The per-origin connection cap also bites the multi-tab user, which is the keyboard-first power user we are optimising for.

## Why WebSocket fanout won

Two reasons, one measured and one structural.

Measured: the spike showed delivery is comfortably fast at the sizes a self-hoster actually runs, provided the implementation pre-encodes each frame once and bounds the per-socket queue. Without a bounded queue, one stalled reader degrades the whole board — the single most important finding in the spike.

Structural: it is a bidirectional channel, so the Phase 2 offline vault sync rides on the same connection instead of introducing a second transport.

## Conditions attached to the recommendation

1. Pre-encode the payload once per event, not once per subscriber.
2. Bound the per-socket queue; drop and record rather than block.
3. Ship a replay window keyed on the delivery cursor so a reconnect does not lose events.
4. Document the proxy timeout requirement for self-hosters.

## Numbers

Full measurement tables, including the p99 curve and the stalled-reader case, are in the spike note — see `wiki/raw/2026/08/2026-08-04-RV-websocket-spike-notes.md`. Summary: flat to about a hundred subscribers, tail grows past two hundred and fifty, fixable by pre-encoding.
