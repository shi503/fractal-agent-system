# Fixtures and End-to-End

Every subsystem in this repo — the router, the plugin skills, the decision ledger, the wiki
substrate, the scheduled runner — is exercised against one synthetic corpus rather than each
test inventing its own throwaway input. This doc inventories that corpus and gives the exact
commands to run the full end-to-end.

## The corpus: `fixtures/taskflow/`

Everything under `fixtures/taskflow/` is fiction, written from scratch for this repo — the
initiative, the people, the decisions, the library names, the measurements. See
`fixtures/taskflow/README.md` for the full disclaimer. The fiction: TaskFlow (this repo's
demo product) is running an initiative called NOVA (Notifications + Offline Vault
Architecture) across three phases.

| Path | Count | What it exercises |
|---|---|---|
| `fixtures/taskflow/blueprints/` | 3 YAML | Router parsing in both blueprint shapes (flat and phased); dependency-edge resolution |
| `fixtures/taskflow/workstreams/*/prd-*.md` | 8 | PRD-template conformance; blueprint `prd:` path resolution |
| `fixtures/taskflow/workstreams/*/HANDOFF.md` | 3 | Eval-template inputs; handoff-schema validation |
| `fixtures/taskflow/wiki/` | 17 md | OKF v0.2 frontmatter lint; BM25 retrieval ranking |
| `fixtures/taskflow/decision-log/` | 4 md | Decision-ledger schema validation, including one non-terminal status |
| `fixtures/taskflow/v1-sample.md` | 1 | The v1 → v2 decision-ledger importer worked example |
| `fixtures/taskflow/people.yaml` | 1 | RACI-initials resolution across the corpus |

Two of the three blueprints use the flat shape (`workstreams:` at the top level with
`id:`/`depends_on:`); the third deliberately keeps the original phased shape (a top-level list
of phases with `feature_lead:`/`dependencies:`) as a backward-compatibility fixture — the
router's `_normalize_blueprint()` must keep accepting both. See
`fixtures/taskflow/README.md` for the per-file dependency-edge map and the three canned wiki
search queries the fixture's retrieval ranking is calibrated against.

## Running the full end-to-end

Each command below is independent and safe to run repeatedly — none of them mutate this
repo's own `.claude/fractal/.state.json` or committed files unless noted.

```bash
# 1. Plugin + marketplace layer
bash tools/validate-plugins.sh

# 2. Router — canonical/synced-copy identity, then a full init/next/update/status/pulse pass
#    against the fixture blueprints in a throwaway state directory
bash tools/check-router-identity.sh
bash tools/router-smoke.sh

# 3. Rules surface — frontmatter shape + every path each rule cites
bash tools/check-rules.sh

# 4. Standards — every guide path in the reference matrix resolves
bash tools/check-guide-matrix.sh

# 5. Decision ledger — schema, storage, safety, and import-pattern test suites
python3 -m pytest tools/decision-ledger -q

# 6. Wiki + BM25 index — three canned queries, each must rank a different document first
bash tools/wiki-index/query-smoke.sh

# 7. Scheduled runner — static allowlist safety guard, then a read-only dry-run scoring pass
cd tools/scheduled-fractal-runner
bash tests/test-allowlist-safety.sh
bash tests/eval-dryrun.sh
cd ../..

# 8. Top-level onboarding docs — every repo path cited in README/SETUP-CLAUDE-CODE/CLAUDE.md resolves
bash tools/check-doc-paths.sh
```

Run them in this order the first time — later steps assume the plugin and router layers are
already sound — but each is independently re-runnable once the repo is in a known-good state.

## Refreshing the fixture-derived index

`tools/wiki-index/taskflow.sqlite` is a committed artifact derived from
`fixtures/taskflow/wiki/`. If you edit that corpus, rebuild it before re-running step 6:

```bash
tools/wiki-index/refresh-bm25-index.sh
```

Review the resulting diff before committing — the script does not commit on your behalf.

## What this doc does not cover

It does not document TaskFlow's own application code (`app/`, `components/`, `lib/`,
`prisma/`) — that is a separate, partially-scaffolded Next.js demo the sample `.claude/CLAUDE.md`
describes, not part of the FRACTAL harness's own test surface.
