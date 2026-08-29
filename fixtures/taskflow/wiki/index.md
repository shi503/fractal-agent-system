---
okf_version: "0.2"
type: index
title: "TaskFlow Wiki Index — NOVA fixture corpus"
tier: librarian
vault-root: fixtures/taskflow/wiki/
initiative: NOVA
created: "2026-08-03"
updated: "2026-08-22"
created_by: AR
updated_by: AR
status: ACTIVE
tags: [index, nova, fixture]
---

# TaskFlow Wiki — Content Catalog

> **Synthetic fixture.** Every person, document, decision, and measurement in this corpus is fictional. See `fixtures/taskflow/README.md`.

Registry for the NOVA (Notifications + Offline Vault Architecture) corpus. Four tiers: `raw/` captures, `sources/` distillations, `synthesis/` cross-cutting reads, `entities/` stubs.

## 1. Raw tier — `raw/2026/08/`

Filename convention: `{YYYY-MM-DD}-{INITIALS}-{slug}.md`.

| File | Type | Author | Gist |
|---|---|---|---|
| `2026-08-03-AR-notification-options-whiteboard.md` | note | AR | Three candidate notification architectures argued on a whiteboard |
| `2026-08-04-RV-websocket-spike-notes.md` | note | RV | Spike measurements and the fanout latency table |
| `2026-08-05-TN-user-interview-notifications.md` | meeting | TN | Six interviews on notification fatigue |
| `2026-08-08-SP-preference-center-sketch.md` | note | SP | Preference surface sketch and the defaults table |
| `2026-08-10-CL-selfhost-constraints.md` | note | CL | Memory and CPU envelope for self-host deployments |
| `2026-08-12-AR-offline-vault-design-session.md` | meeting | AR | Design session: replicated types versus operational transform |
| `2026-08-14-RV-crdt-library-eval.md` | note | RV | Three candidate libraries against five criteria |

## 2. Sources tier — `sources/`

| File | Distilled from | Gist |
|---|---|---|
| `notification-architecture-options.md` | raws 1–2 | Transport comparison; input to D-0001 |
| `notification-user-research.md` | raw 3 | Study findings; input to D-0002 |
| `selfhost-resource-envelope.md` | raw 5 | The published resource ceiling |
| `offline-sync-approaches.md` | raws 6–7 | Merge strategies; input to D-0003 |

## 3. Synthesis tier — `synthesis/`

| File | Gist |
|---|---|
| `nova-architecture-synthesis.md` | Cross-cutting read across all four source pages |
| `notification-fatigue-principles.md` | Five product principles derived from the study |

## 4. Entities tier — `entities/`

| File | Kind | Gist |
|---|---|---|
| `websocket-fanout-service.md` | system | The push transport built in Phase 1 |
| `alex-rivera.md` | person | Fictional tech lead; accountable owner |

## 5. Adjacent artifacts (outside `wiki/`)

| Path | What it is |
|---|---|
| `blueprints/` | Three NOVA phase blueprints (two flat shape, one phased shape) |
| `decision-log/` | Four ledger-v2 entries, D-0001 through D-0004 |
| `workstreams/` | Eight PRD stubs and three completed HANDOFFs |
| `people.yaml` | Synthetic RACI registry |
| `v1-sample.md` | v1-format decision table, importer worked example |

## 6. Frontmatter contract

Every file in this corpus carries `okf_version: "0.2"` and a `type:`. Provenance keys (`created`, `updated`, `created_by`, `updated_by`) are required on all tiers; `source:` is required on `sources/` and `synthesis/` tiers and lists the wiki paths the page was distilled from.
