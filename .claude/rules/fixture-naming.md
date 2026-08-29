paths: ["fixtures/taskflow/**"]
---

# Fixture Naming and Terminology

**Canonical reference:** `fixtures/taskflow/README.md`

## Canonical names

| Term | Use this | Not this |
|---|---|---|
| Demo product | **TaskFlow** — a keyboard-first, self-hosted kanban tracker | Any other product name |
| Initiative | **NOVA** (Notifications + Offline Vault Architecture) | An unexpanded acronym, or a different initiative name |
| Phase 1 | NotificationCore — WS-1, WS-2, WS-3 | — |
| Phase 2 | OfflineVault — WS-4, WS-5, WS-6 | — |
| Phase 3 | Hardening — WS-7, WS-8 (old phased blueprint shape, backward-compat fixture) | — |
| Email domain | `taskflow.example` (RFC 2606 reserved, not routable) | Any resolvable domain |
| Fictional libraries | `mergeloom`, `driftset`, `weaveline` | Any real library name |

## Fiction discipline

**Everything under `fixtures/taskflow/` is fictional.** The initiative, the people, the
decisions, the meeting transcripts, the measurements, and the library names were invented for
this fixture. Nothing here was derived from, sanitized from, or adapted out of any real
corpus. Do not cite anything in this directory as evidence about the real world, and never
introduce a real person, company, product, hostname, or repository name into it.

## Cast — `fixtures/taskflow/people.yaml`

| Initials | Name | Role | Default RACI |
|---|---|---|---|
| AR | Alex Rivera | Tech Lead / Architect | Accountable |
| RV | Rowan Vance | Backend Engineer | Responsible |
| SP | Sam Park | Frontend Engineer | Responsible |
| TN | Toni Nguyen | Product | Consulted |
| CL | Casey Lume | SRE / Infrastructure | Consulted |

Every RACI field and `created_by` / `updated_by` value in the corpus must resolve against
this file. Do not introduce a sixth person, and do not change an initial's name, role, or
default RACI without updating every entry that references it.

## Rules

1. **Stay inside the fiction.** No real name, company, product, hostname, or repository name
   may enter `fixtures/taskflow/`.
2. **Keep cross-references resolving.** Blueprint `prd:` paths, decision `cross_refs`, wiki
   `source:` lists, and HANDOFF citations must all point at files that exist. A dangling
   reference silently weakens multiple validators at once.
3. **Keep both blueprint shapes.** Two flat (`BLUEPRINT-NOVA-P1-*`, `BLUEPRINT-NOVA-P2-*`),
   one old-style phased (`BLUEPRINT-NOVA-P3-Hardening.yaml`, which indexes
   `phase["workstreams"][n]["feature_lead"]` directly). Do not modernize the phased file into
   the flat shape — it is the router's backward-compatibility fixture.
4. **Keep the three wiki smoke queries distinct.** `websocket fanout latency`, `offline
   conflict resolution`, and `notification preference defaults` must each rank a different
   document first (`tools/wiki-index/query-smoke.sh` enforces this). Rebalance vocabulary
   rather than accepting a tie if a corpus edit flattens the rankings.
5. **`D-0004` stays non-terminal** (`status: in_discovery`) — it is the fixture exercising
   validators and renderers on a status that is not the happy path.
6. **Paths are repo-relative.** No absolute paths anywhere in the corpus.

## Source-of-truth

On any disagreement between this rule and `fixtures/taskflow/README.md`, the README wins —
this rule is a summary auto-loaded when working in the directory, not a second canonical copy.

<!-- referenced-paths
fixtures/taskflow/README.md
fixtures/taskflow/people.yaml
fixtures/taskflow/blueprints
fixtures/taskflow/workstreams
fixtures/taskflow/decision-log
fixtures/taskflow/wiki
tools/wiki-index/query-smoke.sh
-->
