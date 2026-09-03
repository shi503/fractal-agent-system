# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working in this repository. It is the always-on anchor; `.claude/rules/` is the on-demand layer that loads per path, and nothing here should contradict it.

## What this repo is — establish the mode first

This repo is **two things at once**, and which one you are in changes almost everything about what good looks like.

1. **FRACTAL — the framework.** Multi-tier agent orchestration distributed as six Claude Code plugins. A Python state machine decides what runs next from a dependency graph; each unit of work starts in a fresh context and ends in a `HANDOFF.md` whose claims are pasted command output. Roughly 290 tracked files: `.claude/`, `ROUTING_LOGIC/`, `tools/`, `standards/`, `docs/`, `fixtures/`.
2. **TaskFlow — the demo app.** The Next.js 15 kanban tracker FRACTAL dogfoods against. Roughly 11 tracked files today across `app/`, `components/`, `lib/`, `prisma/`. Small, real, and **intended to grow** — not a throwaway.

**Framework mode** is the default; it is where most of the repo lives. **Product mode** is entered deliberately, when the task names a TaskFlow feature, a route, a component, or the schema. Read `.claude/CLAUDE.md` before writing any product code — it carries the full stack table, the RSC/client decision tree, the canonical Server Action shape, the design-token rules, and the database conventions. That file doubles as the sample a consuming project copies, which is exactly why it stays a real, working guide rather than a stub.

## FRACTAL tiers

| Tier | Agent | Model | Role |
|---|---|---|---|
| 0 | Strategist | opus | Project intent, constraints, failure modes |
| 1 | Architect | opus | BLUEPRINT authoring, workstream PRDs, HANDOFF evaluation |
| 2 | Feature Lead | sonnet | One workstream end-to-end |
| 3 | Sub-Agent | sonnet | Atomic single-file task |

Intent for this project lives in `.claude/fractal/STRATEGIST-taskflow.md`; the localized system description is `.claude/fractal/FRACTALSYSTEM-taskflow.md`. Blueprints, workstream PRDs, `.claude/fractal/templates/`, and `.claude/fractal/EVAL_TEMPLATES/` sit alongside them.

## Canonical vs. generated — the trap that costs the most

Three paths are **generated mirrors**. Editing a mirror loses the work at the next sync, silently — no error, no conflict, no diff to notice.

| To change | Edit (canonical) | Then | Drift gate |
|---|---|---|---|
| A tier agent | `.claude/plugins/fractal-core/agents/` | `tools/sync-agents.sh` | `tools/sync-agents.sh --check` |
| The router | `ROUTING_LOGIC/router.py` | sync the copy | `tools/check-router-identity.sh` |
| A skill | the owning plugin's skills directory | — | `tools/validate-plugins.sh` |

`.claude/agents/` and `.claude/fractal/router.py` are the mirrors. The plugin is the distributable unit and therefore the source of truth; Claude Code just needs the agents to also exist at `.claude/agents/`.

## Rules surface — what auto-loads where

`.claude/rules/` holds seven path-scoped rule files. Each declares a `paths:` frontmatter glob and loads only when a session touches a matching path.

| Rule file | Loads when working in |
|---|---|
| `markdown-authoring.md` | every `.md` file |
| `fractal-protocol.md` | `.claude/fractal/**`, `ROUTING_LOGIC/**` |
| `plugin-authoring.md` | `.claude/plugins/**`, `.claude-plugin/**` |
| `decision-ledger.md` | `tools/decision-ledger/**`, `fixtures/taskflow/decision-log/**` |
| `wiki-conventions.md` | the wiki substrate and `tools/wiki-index/**` |
| `memory-vs-wiki.md` | the wiki substrate, `tools/decision-ledger/**`, `standards/**` |
| `fixture-naming.md` | `fixtures/taskflow/**` |

`tools/check-rules.sh` gates their frontmatter shape and verifies every path they cite still exists.

## Plugins

Six plugins under `.claude/plugins/`, registered in `.claude-plugin/marketplace.json`:

`fractal-core` (the four tier agents plus `fractal-init`, `pulse`, `handoff`, `gap-analysis`, `quality-pass`, `commit-summarize`, `claude-md-audit`, `fractal-maintenance`) is the one every session needs. `fractal-tools`, `fractal-planning`, `fractal-wiki`, `fractal-runner`, and `fractal-pr-review` add role-specific skills.

```bash
/plugin marketplace add .
/plugin install fractal-core@fractal-marketplace
```

Read `.claude/rules/plugin-authoring.md` before adding or editing any skill — it auto-loads under `.claude/plugins/**`. `example-claude/DEPRECATED.md` records that the old copy-the-directory install is retired; the marketplace is the install path.

## Gates — you are the CI

`.github/` holds only `dependabot.yml`. **No pipeline runs these checks.** If you do not run them, nothing does — and every claim in a HANDOFF is unverified.

The full suite completes in under five seconds, so run all of it rather than picking a subset:

```bash
bash tools/check-prereqs.sh && bash tools/check-router-identity.sh && \
bash tools/sync-agents.sh --check && bash tools/check-rules.sh && \
bash tools/validate-plugins.sh && bash tools/check-doc-paths.sh && \
bash tools/check-guide-matrix.sh && bash tools/docs-freshness-check.sh && \
bash tools/router-smoke.sh && bash tools/release-gate.sh
```

Product-mode changes additionally run the app gate:

```bash
npm run build && npx tsc --noEmit && npm run lint && npm run format:check && npm run test:run
```

Paste the actual output into the HANDOFF or the PR. A summary of a gate is not a gate.

## Fixtures are fictional

`fixtures/taskflow/` is the synthetic NOVA corpus — blueprints, workstream PRDs, HANDOFFs, wiki docs, decision entries — that every subsystem is exercised against. Every name and fact in it is invented.

Never cite a fixture as evidence about a real project, person, or decision. `fixtures/taskflow/README.md` states the boundary; `docs/fixtures-and-e2e.md` has the inventory and the end-to-end run.

## Release hygiene — this is a public repo

`tools/release-gate.sh` enforces what must never be tracked here: PDFs, files over 2 MB outside the allowlist, `people.yaml` outside fixtures, any `.env*` or `settings.local.json`, and any absolute home-directory path in file content. It then runs `tools/repo-hygiene/contamination_scan.py`.

The home-path check is the one that fires most. Cite repo-relative paths in docs and scripts; a pasted `/Users/<name>/...` fails the gate.

## Output discipline

- Between tool calls: **40 words max** — no narration, no restating the plan.
- Final answer with no further tools: **150 words max** unless detail is requested.
- Never open with "Great", "Sure", "Certainly", "Of course", or "I'll".
- No trailing summary of what you just did unless asked.

## Forbidden patterns

| Pattern | Why |
|---|---|
| Hand-editing `.claude/agents/` or `.claude/fractal/router.py` | Generated mirrors — the next sync overwrites you silently |
| `python3 ROUTING_LOGIC/router.py init` mid-epic | Resets every workstream state for that blueprint |
| Marking a workstream COMPLETE without pasted gate output | Evidence over assertion is the framework's central claim |
| Citing `fixtures/taskflow/` as a real fact | Fictional by construction |
| An absolute home-directory path in a tracked file | Fails `tools/release-gate.sh` |
| A repo-relative path in a top-level doc that does not resolve | Fails `tools/check-doc-paths.sh` |
| Adding a plugin or skill without registering it | Fails `tools/validate-plugins.sh` |
| Hard-wrapped markdown prose | A mid-sentence newline survives the paste downstream |
| Writing product code in framework mode (or the reverse) | Establish the mode first — see the top of this file |

## Git conventions

Conventional Commits (`feat`, `fix`, `docs`, `chore`, `refactor`, `test`), one logical change per commit, descriptive kebab-case branches off the default branch. Never commit over a failing gate. `CHANGELOG.md` records router-behavior changes — a breaking router change re-baselines every downstream vendor pinning it.

## Key references

- `README.md` — install, the capability tour, and wiring FRACTAL into another project
- `.claude/CLAUDE.md` — the TaskFlow product-stack guide, and the sample a consuming project copies
- `standards/engineering-principles.md`, `standards/architecture-patterns.md` — the canonical tier every guide inherits from
- `standards/guide-reference-matrix.md` — which guide a workstream PRD should cite, gated by `tools/check-guide-matrix.sh`
- `docs/claude-md-rubric.md` — how a CLAUDE.md is scored; `claude-md-audit` runs it
- `docs/research-claude-code-harness.md` — how the harness loads and weighs this file
- `docs/permissions-guide.md` — permission tiers for dispatched agents
- `docs/frontend-dev-guide.md`, `docs/testing-patterns.md` — product-mode deep dives

## When uncertain

Surface the ambiguity instead of guessing. A guessed convention here does not stay here — it ships in a plugin and propagates into every project that installs it.
