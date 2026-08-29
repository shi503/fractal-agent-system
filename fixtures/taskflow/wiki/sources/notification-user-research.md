---
okf_version: "0.2"
type: source
title: "Notification user research — what six teams said"
tier: sources
initiative: NOVA
created: "2026-08-06"
updated: "2026-08-06"
created_by: TN
updated_by: TN
status: ACTIVE
source:
  - wiki/raw/2026/08/2026-08-05-TN-user-interview-notifications.md
tags: [nova, notifications, research, product]
---

# Notification user research — what six teams said

Summary of six interviews with self-hosting TaskFlow teams. Input to D-0002.

## Findings, ranked by strength of signal

1. **Self-caused events must never come back.** 6/6, volunteered unprompted. The strongest single signal in the study, and the cheapest to honour.
2. **Assignment and direct reply are the only universal interrupts.** 6/6 named both; nothing else was named by more than four.
3. **A roll-up is the preferred reading surface for everything else.** 4/6 described wanting one digest they read on their own schedule.
4. **Noise is why people churn.** 5/6 said they left a previous tool over volume, not over missing capability.
5. **Cadence is contested.** Four wanted daily; one wanted four-hourly for a two-timezone team; one wanted everything immediately.

## The trap the study identifies

The failure pattern participants described is bimodal, not gradual: users do not tune, they flip between everything-on and everything-off. P2 described the full cycle — turn it all off, miss something important, turn it all back on, turn it all off again. A product that ships loud and expects tuning is choosing the wrong half of that cycle.

## Product implication

Start quiet. Make the roll-up the primary reading surface, let direct mentions interrupt, and suppress self-caused events unconditionally. Teams that want more volume can raise it; a team shouted at on day one uninstalls before it ever finds the settings.

## Direct quotes worth keeping

> "The problem isn't that it tells me things. It's that it tells me things at the same volume whether it's a typo fix or someone reassigning my whole column."

> "Interrupt me for a reply. Roll everything else into one thing I read when I choose to read it."

Full interview notes: `wiki/raw/2026/08/2026-08-05-TN-user-interview-notifications.md`.
