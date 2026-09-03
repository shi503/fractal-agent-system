# AGENTS.md — FRACTAL Multi-Agent System

> Platform-agnostic context for AI-assisted work (Cursor, Codex, Gemini, Copilot).
> Claude Code sessions read the root `CLAUDE.md`, which carries the same identity plus the Claude-Code-specific surfaces (rules auto-load, plugins, skills).

## Repo identity — two things at once

This repo is **FRACTAL**, a multi-tier agent orchestration framework distributed as Claude Code plugins, **and** it is **TaskFlow**, the Next.js demo application FRACTAL dogfoods itself against.

Both are live. They are not the same size, and knowing which one you are in is the first thing to establish in any session:

| Identity | Where it lives | Tracked files (approx.) |
|---|---|---|
| **FRACTAL — the framework** | `.claude/plugins/`, `.claude/fractal/`, `ROUTING_LOGIC/`, `tools/`, `standards/`, `docs/`, `fixtures/` | ~290 |
| **TaskFlow — the demo app** | `app/`, `components/`, `lib/`, `prisma/` | ~11 |

The demo app is small **today** and is intended to grow. It is a real target, not a throwaway — but the framework is what most sessions touch, and a request phrased in framework vocabulary ("add a skill", "fix the gate", "the router is wrong") never belongs in `app/`.

## Your role when working here

You are working on **agent infrastructure** far more often than on product code. That means:

- Authoring and revising `SKILL.md` files, agent definitions, and path-scoped rules
- Writing and hardening deterministic gates in `tools/` — bash and Python, not TypeScript
- Maintaining the router state machine and its blueprint/PRD/HANDOFF artifact contract
- Keeping `docs/` and `standards/` accurate against what the code actually does
- Building out the TaskFlow demo app when the task is explicitly a product task

The framework's own doctrine applies to work on the framework: a claim of completion needs pasted command output, not a summary.

## Canonical vs. generated — read before editing

Three paths in this repo are **generated mirrors**. Editing a mirror loses the work silently at the next sync, with no error and no conflict.

| You want to change | Edit this (canonical) | Then run | Drift gate |
|---|---|---|---|
| A tier agent definition | `.claude/plugins/fractal-core/agents/` | `tools/sync-agents.sh` | `tools/sync-agents.sh --check` |
| The router | `ROUTING_LOGIC/router.py` | (sync the copy) | `tools/check-router-identity.sh` |
| A skill | the owning plugin's skills directory | — | `tools/validate-plugins.sh` |

`.claude/agents/` and `.claude/fractal/router.py` are the mirrors. They exist because Claude Code loads agents from `.claude/agents/`; the plugin is the distributable unit and therefore the source of truth.

## Content surfaces

| Path | What it holds |
|---|---|
| `.claude/plugins/` | Six plugins — `fractal-core` plus tools, planning, wiki, runner, pr-review |
| `.claude-plugin/marketplace.json` | Marketplace manifest; every plugin registered here |
| `.claude/fractal/` | Router copy, blueprints, workstream PRDs, `.claude/fractal/templates/`, `.claude/fractal/EVAL_TEMPLATES/` |
| `ROUTING_LOGIC/router.py` | The canonical router — a Python state machine, no LLM in the decision loop |
| `.claude/rules/` | Seven path-scoped rule files that load only when a session touches a matching path |
| `tools/` | Deterministic gates plus four subsystems: `tools/decision-ledger/`, `tools/wiki-index/`, `tools/contracts/`, `tools/scheduled-fractal-runner/` |
| `standards/` | Framework-agnostic engineering standards every project guide inherits from |
| `docs/` | Deep-dive guides, harness research, evaluation framework, rubrics |
| `fixtures/taskflow/` | The synthetic NOVA corpus every subsystem is exercised against |
| `app/`, `components/`, `lib/`, `prisma/` | The TaskFlow demo application |

## Gates — you are the CI

`.github/` contains only `dependabot.yml`. **There is no CI pipeline running these checks.** If you do not run them, nothing does.

The full suite is fast — under five seconds end to end — so run all of it before any commit rather than picking a subset:

```bash
bash tools/check-prereqs.sh && bash tools/check-router-identity.sh && \
bash tools/sync-agents.sh --check && bash tools/check-rules.sh && \
bash tools/validate-plugins.sh && bash tools/check-doc-paths.sh && \
bash tools/check-guide-matrix.sh && bash tools/docs-freshness-check.sh && \
bash tools/router-smoke.sh && bash tools/release-gate.sh
```

Product-side changes additionally run the app's own gate: `npm run build && npx tsc --noEmit && npm run lint && npm run format:check && npm run test:run`.

## Fixtures are fictional

`fixtures/taskflow/` is a synthetic corpus — the NOVA initiative, its people, its decisions, its wiki. Every name and every fact in it is invented so the subsystems have something realistic to run against.

Never cite a fixture as evidence about a real project, a real person, or a real decision. Read `fixtures/taskflow/README.md` before treating anything in that tree as true.

## Release hygiene — this repo is a public port

`tools/release-gate.sh` enforces what a public repo must not contain: no tracked PDFs, no tracked file over 2 MB outside the allowlist, no `people.yaml` outside fixtures, no tracked `.env*` or `settings.local.json`, no absolute home-directory path in any tracked file, and a clean pass from `tools/repo-hygiene/contamination_scan.py`.

The last one bites most often. A machine-local path like `/Users/<name>/...` or `/home/<name>/...` pasted into a doc or a script fails the gate — cite repo-relative paths instead.

## Conventions

- **Markdown prose is never hard-wrapped.** One logical line per paragraph; let the editor soft-wrap. Tables, lists, code fences, and headings keep their normal line structure. A newline mid-sentence is a literal character — it survives the paste into any downstream surface and renders as a broken mid-sentence break.
- **Every repo-relative path you cite in a top-level doc must resolve.** `tools/check-doc-paths.sh` gates this — a dangling path fails the build.
- **Conventional Commits**, one logical change per commit. Never commit over a failing gate.
- **Branch, don't push to the default branch** for multi-file changes.
- **Never log credentials, tokens, or secrets.** Environment variables for every secret; `.env.example` carries placeholders only.

## Forbidden patterns

| Pattern | Why |
|---|---|
| Hand-editing `.claude/agents/` or `.claude/fractal/router.py` | Generated mirrors — the next sync silently overwrites you |
| `python3 ROUTING_LOGIC/router.py init` mid-epic | Resets every workstream state for the blueprint |
| Citing a fixture as a real fact | `fixtures/taskflow/` is fictional by construction |
| An absolute home-directory path in a tracked file | Fails `tools/release-gate.sh` |
| Adding a plugin without registering it | `tools/validate-plugins.sh` gates the marketplace manifest |
| Marking a workstream COMPLETE without pasted gate output | The framework's central claim is evidence over assertion |
| Hard-wrapping markdown prose | Breaks downstream paste; see Conventions |

## When uncertain

Surface the ambiguity rather than guessing. This repo's whole thesis is that unverifiable "done" is the expensive failure — a guessed convention propagates into every consuming project that installs the plugins.
