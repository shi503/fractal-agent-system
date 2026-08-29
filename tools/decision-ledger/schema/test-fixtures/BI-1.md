---
id: BI-1
type: big_idea
title: "Workspace-level automation rules"
owner: TN
status: in_discovery
raci:
  responsible: [TN]
  accountable: [AR]
  consulted: [RV, SP]
  informed: [CL]
created: 2026-08-01T00:00:00Z
updated: 2026-08-10T09:00:00Z
created_by: TN
updated_by: TN
unlocks:
  - D-9001
cross_refs:
  - D-9001
tags:
  - automation
  - workspace
---

## Context

A rules engine ("when a card enters column X, do Y") sits upstream of several
open questions — the webhook rate-limit shape (D-9001), the notification
fanout's event schema, and the preference center's default cadence.

Key capabilities unlocked:
- Self-serve automation without a support ticket
- A natural home for the webhook-delivery rate-limit work
- A reusable trigger surface for future integrations

## Answer

_In discovery. Scoping a minimal rules engine (trigger + one action) as the
Q4 wedge; the full condition/action matrix is a later phase._
