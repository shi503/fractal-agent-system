---
okf_version: "0.2"
type: note
title: "WebSocket fanout spike — latency measurements"
tier: raw
initiative: NOVA
created: "2026-08-04"
updated: "2026-08-04"
created_by: RV
updated_by: RV
status: ACTIVE
tags: [nova, websocket, fanout, latency, spike]
---

# WebSocket fanout spike — latency measurements

Spike branch `spike/websocket-fanout`. Goal: measure fanout latency, not to build anything shippable. Everything below is WebSocket fanout latency measured end to end — server accepts the write, to client renders the change.

## Rig

One app process, one WebSocket per simulated client, a synthetic board, and a driver that writes one card update per second. Fanout is naive: iterate the subscriber table, write to each socket. Latency sampled per delivered message.

## WebSocket fanout latency table

| Subscribers on the board | p50 latency | p95 latency | p99 latency | Fanout CPU per event |
|---|---|---|---|---|
| 10 | 11 ms | 19 ms | 24 ms | negligible |
| 50 | 14 ms | 27 ms | 41 ms | 0.4 ms |
| 100 | 18 ms | 38 ms | 63 ms | 0.9 ms |
| 250 | 31 ms | 74 ms | 148 ms | 2.6 ms |
| 500 | 58 ms | 191 ms | 470 ms | 6.1 ms |

## Reading the latency numbers

Up to a hundred subscribers the WebSocket fanout latency is flat enough that a user cannot tell the difference. Past two hundred and fifty the tail latency starts to run away — the p99 latency at five hundred subscribers is nearly half a second, and the shape of the curve says the cost is the serial write loop, not the socket itself.

Fixing the tail latency looks cheap: serialize the payload once per event instead of once per subscriber, and the fanout loop stops re-encoding five hundred times. A rough retest with a pre-encoded frame put p99 latency at five hundred subscribers back down to 96 ms. Not committed to the spike branch; noting it so the WS-2 fanout implementation starts there.

## Latency under a slow consumer

Deliberately stalled one client's reader. With no backpressure policy the fanout loop blocks and every other subscriber inherits that client's latency — p95 latency for the whole board went from 27 ms to 2.3 s with one stalled reader out of fifty. This is the single most important finding in the spike: a WebSocket fanout implementation without a bounded per-socket queue turns one bad network into a board-wide latency incident. Drop-and-record beat block-and-wait in every run.

## Reconnect

Killed the socket mid-run. Browser reconnected in under a second. Whatever was fanned out during the gap is simply lost, so the fanout service needs a replay window keyed on the delivery cursor. Replaying the last two hundred events cost 40 ms of extra latency on reconnect, which is fine.

## Verdict

WebSocket fanout latency is acceptable for the self-host target if and only if the implementation pre-encodes the frame and bounds the per-socket queue. Recommending candidate C.
