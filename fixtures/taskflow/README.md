# TaskFlow Fixture Corpus — initiative NOVA

## Fiction disclaimer

**Everything in this directory is fictional.** The initiative, the people, the decisions, the meeting transcripts, the measurements, the library names (`mergeloom`, `driftset`, `weaveline`), and the products described here were invented for this fixture. Any resemblance to real persons, companies, products, or events is coincidental. All email addresses use `taskflow.example`, a reserved domain under RFC 2606, and are not routable. Nothing here was derived from, sanitized from, or adapted out of any real corpus — it was written from scratch for this purpose.

Do not cite anything in this directory as evidence about the real world. It exists to be parsed, indexed, validated, and ranked — not to be believed.

## What this is

The synthetic corpus every ported subsystem is exercised against. Instead of each test inventing its own throwaway input, they all read this one internally-consistent body of documents: wiki docs argue the options, decision entries lock them, blueprints execute them, HANDOFFs record the outcomes, and the cross-references between all four actually resolve.

The fiction: **TaskFlow** — the repo's demo product, a keyboard-first self-hosted kanban tracker — is running initiative **NOVA (Notifications + Offline Vault Architecture)** across three phases. Phase 1 builds a notification channel, Phase 2 adds an offline vault that rides it, Phase 3 hardens both.

## Layout

| Path | Count | What it exercises |
|---|---|---|
| `blueprints/` | 3 YAML | Router parsing in both blueprint shapes; dependency-edge resolution |
| `workstreams/*/prd-*.md` | 8 | PRD-template conformance; blueprint `prd:` path resolution |
| `workstreams/*/HANDOFF.md` | 3 | Eval-template inputs; handoff-schema validation |
| `wiki/` | 17 md | OKF v0.2 frontmatter lint; BM25 retrieval ranking |
| `decision-log/` | 4 md | Ledger schema validation, including one non-terminal status |
| `v1-sample.md` | 1 | v1 → v2 importer worked example (renders `D-0003` in the v1 table format) |
| `people.yaml` | 1 | RACI initials resolution |

### Blueprints

| File | Shape | Workstreams | Edges |
|---|---|---|---|
| `BLUEPRINT-NOVA-P1-NotificationCore.yaml` | flat (`workstreams:` at top level) | WS-1, WS-2, WS-3 | WS-2 → WS-1, WS-3 → WS-1 |
| `BLUEPRINT-NOVA-P2-OfflineVault.yaml` | flat | WS-4, WS-5, WS-6 | WS-5 → WS-4, **WS-6 → WS-4 + WS-5** (multi-edge) |
| `BLUEPRINT-NOVA-P3-Hardening.yaml` | **old phased shape** (top-level list of phases, `feature_lead:` / `dependencies:` keys) | WS-7, WS-8 | WS-8 → WS-7, across a phase boundary |

The P3 file is the backward-compatibility fixture. It must keep loading under the original router, which indexes `phase["workstreams"][n]["feature_lead"]` directly. Do not modernize it into the flat shape.

### Wiki

Four tiers under `wiki/`: `raw/2026/08/` (7 captures, `{YYYY-MM-DD}-{INITIALS}-{slug}.md`), `sources/` (4 distillations), `synthesis/` (2 cross-cutting reads), `entities/` (2 stubs), plus lowercase `index.md` and `log.md`. Every file carries `okf_version: "0.2"` and a `type:`, with provenance keys on all tiers and `source:` on the sources and synthesis tiers.

The corpus vocabulary is deliberately overlapping but differentiated so that retrieval ranking is a real test rather than a formality. Three canned smoke queries must each rank a **different** document first:

| Query | Expected top hit |
|---|---|
| `websocket fanout latency` | `wiki/raw/2026/08/2026-08-04-RV-websocket-spike-notes.md` |
| `offline conflict resolution` | `wiki/sources/offline-sync-approaches.md` |
| `notification preference defaults` | `wiki/raw/2026/08/2026-08-08-SP-preference-center-sketch.md` |

If a corpus edit flattens those rankings, the edit has weakened the fixture — rebalance the vocabulary rather than accepting the tie.

### Decisions

| ID | Title | Status |
|---|---|---|
| `D-0001` | WebSocket fanout over server-sent events and polling | `answered` |
| `D-0002` | Notification preference defaults are opt-in digests | `answered` |
| `D-0003` | Adopt the mergeloom CRDT library for offline vault sync | `answered` |
| `D-0004` | Load-test gate before general availability | `in_discovery` |

`D-0004` is deliberately non-terminal so validators and renderers are exercised on a status that is not the happy path.

## People

Five fictional people, registered in `people.yaml`: AR (Alex Rivera, tech lead, accountable), RV (Rowan Vance, backend), SP (Sam Park, frontend), TN (Toni Nguyen, product), CL (Casey Lume, SRE). Every RACI field and every `created_by` / `updated_by` in the corpus resolves against that file.

## Editing rules

1. **Stay inside the fiction.** No real name, company, product, hostname, or repository name may enter this directory.
2. **Keep the cross-references resolving.** Blueprint `prd:` paths, decision `cross_refs`, wiki `source:` lists, and the HANDOFF citations all point at files that exist. Adding a dangling reference silently weakens several tests at once.
3. **Keep the two blueprint shapes.** Two flat, one phased. That contrast is the point.
4. **Keep the three smoke queries distinct.** See the table above.
5. **Paths are repo-relative.** No absolute paths anywhere in the corpus.
