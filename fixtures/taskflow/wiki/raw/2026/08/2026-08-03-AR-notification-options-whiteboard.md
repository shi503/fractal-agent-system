---
okf_version: "0.2"
type: note
title: "Whiteboard — three candidate notification architectures"
tier: raw
initiative: NOVA
created: "2026-08-03"
updated: "2026-08-03"
created_by: AR
updated_by: AR
status: ACTIVE
tags: [nova, notifications, architecture, whiteboard]
---

# Whiteboard — three candidate notification architectures

Raw capture from the 2026-08-03 whiteboard session. Not a decision. Three candidates were drawn on the board and argued for about ninety minutes. Numbers here are guesses from the room, not measurements — the spike (RV, this week) is what settles them.

## Candidate A — poll the inbox

The client asks the server every N seconds whether anything changed. Dead simple, survives every proxy a self-hoster is likely to put in front of TaskFlow, and needs no new infrastructure at all.

The cost is felt on the server, not the client. At a five-second poll interval a fifty-person instance generates about six hundred requests a minute that almost always return nothing. AR's objection: it scales in the wrong direction — the quieter the workspace, the more waste. TN's objection is different and more interesting: a poll interval is a floor on how stale the board can be, and "the board is stale" is exactly the complaint that started NOVA.

## Candidate B — server-sent events

One long-lived HTTP stream per client, server pushes down it. Cheaper than polling, works through most reverse proxies, and the browser reconnects on its own. The reason the room cooled on it: the stream is one-directional, so every client action still needs a separate request, and the connection cap per origin bites when a user has four boards open in four tabs.

## Candidate C — WebSocket fanout

A single bidirectional socket per client. The server keeps a subscriber table per board and fans out one message per interested subscriber when something changes. This is the option the room kept returning to, mostly because it is the only one that also gives us a channel the offline vault work can reuse in Phase 2 rather than building a second transport.

The open worries about WebSocket fanout are honest ones: a self-hoster behind a naive proxy may see the socket dropped at sixty seconds; the subscriber table is per-process, so a second app process needs a shared bus; and nobody in the room could say what the fanout cost looks like at five hundred subscribers on one board.

## What happens next

RV runs a spike against candidate C and reports back with actual measurements. CL to write down the self-host memory and CPU envelope so the spike has a ceiling to test against. TN continues the user interviews.

Whiteboard photo is in the shared drive; this file is the transcription.
