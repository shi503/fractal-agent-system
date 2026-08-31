# docs/ — Reading Order

Every tracked file under `docs/` is listed below, grouped by what a newcomer needs and in the order to read it. Nothing is silently unlisted. Files under `docs/_archive/` are superseded; skip them unless you're researching design history (see `docs/_archive/README.md`).

## 1. Start here

1. [`../README.md`](../README.md) — repo overview, quickstart, how the four artifact tiers chain together.
2. [`../The FRACTAL Multi-Agent System.md`](../The%20FRACTAL%20Multi-Agent%20System.md) — the live conceptual overview of the framework (root-level, actively maintained).

## 2. The artifact contracts (what each tier reads and writes)

Read these in tier order — each is the spec for one file a running system actually produces:

3. [`PRD.md`](./PRD.md) — the Architect→Feature Lead contract (a workstream's spec).
4. [`_PRD-template.md`](./_PRD-template.md) — copyable PRD skeleton.
5. [`FEATURELEAD.md`](./FEATURELEAD.md) — the Feature Lead's session-start context file.
6. [`ExampleSubAgent.md`](./ExampleSubAgent.md) — the Sub-Agent's scoped-task contract.
7. [`PULSE.md`](./PULSE.md) — the heartbeat log format Feature Leads append to.
8. [`HANDOFF.md`](./HANDOFF.md) — the workstream completion report format.
9. [`The FRACTAL Evaluation Framework.md`](./The%20FRACTAL%20Evaluation%20Framework.md) — how the Architect evaluates a HANDOFF (tool-trace-as-truth, deterministic-first). Still actively cited by `harness-gap-analysis.md`.
10. [`DETERMINISTIC_EVAL.md`](./DETERMINISTIC_EVAL.md) / [`DETERMINISTIC_EVAL_RESULT.md`](./DETERMINISTIC_EVAL_RESULT.md) — Layer 1 eval template + a worked example.
11. [`LLM_JUDGMENT_EVAL.md`](./LLM_JUDGMENT_EVAL.md) / [`LLM_JUDGMENT_EVAL_RESULT.md`](./LLM_JUDGMENT_EVAL_RESULT.md) — Layer 2 eval template + a worked example.

## 3. Engineering guides (canonical — enforced conventions)

12. [`frontend-dev-guide.md`](./frontend-dev-guide.md) — Next.js patterns for this codebase.
13. [`testing-patterns.md`](./testing-patterns.md) — test conventions.
14. [`fixtures-and-e2e.md`](./fixtures-and-e2e.md) — the shared synthetic corpus + how to run the full end-to-end.
15. [`wiki-conventions.md`](./wiki-conventions.md) — the `fractal-wiki` plugin's markdown substrate contract.
16. [`permissions-guide.md`](./permissions-guide.md) — graduated Claude Code permission tiers for onboarding (pairs with `permission-templates/*.json`).
17. [`soc2-compliance.md`](./soc2-compliance.md) — compliance guardrails for enterprise/healthcare deployments.
18. [`platform-strategy.md`](./platform-strategy.md) — architecture & evolution strategy reference (defers to `CLAUDE.md` and the frontend guide for implementation decisions).
19. [`claude-md-rubric.md`](./claude-md-rubric.md) — scoring rubric used by the `claude-md-audit` skill.
20. [`claude-md-audits/2026-04-14-taskflow.md`](./claude-md-audits/2026-04-14-taskflow.md) — a worked audit against that rubric.

## 4. Background research (context for why the harness looks the way it does)

21. [`research-claude-code-harness.md`](./research-claude-code-harness.md) — public source-analysis patterns behind `.claude/agents/*` and `.claude/skills/*`.
22. [`research_notes.md`](./research_notes.md) / [`research_notes_consolidated.md`](./research_notes_consolidated.md) — raw and consolidated notes on agentic design patterns (OpenClaw et al.) that informed FRACTAL.
23. [`harness-gap-analysis.md`](./harness-gap-analysis.md) — FRACTAL scored against comparable harnesses.
24. [`harness-upgrade-roadmap.md`](./harness-upgrade-roadmap.md) — advisory roadmap from that gap analysis (not yet a BLUEPRINT).

## 5. Miscellaneous reference

25. [`skill-disposition-2.0.md`](./skill-disposition-2.0.md) — disposition of source skills against the plugin split.
26. [`fractal_slide_content.md`](./fractal_slide_content.md) — slide content/copy for presenting FRACTAL.
27. [`permission-templates/`](./permission-templates/) — `tier-1.json` .. `tier-4-auto.json`, the copy-paste configs `permissions-guide.md` walks through.

## Archived / deprecated

Superseded content, kept for history only — **not** part of the reading order above:

- [`_archive/ARCHITECT.md - The Orchestrator.md`](./_archive/ARCHITECT.md%20-%20The%20Orchestrator.md)
- [`_archive/BLUEPRINT.md - The Deterministic Execution Plan.md`](./_archive/BLUEPRINT.md%20-%20The%20Deterministic%20Execution%20Plan.md)
- [`_archive/STRATEGIST.md - The Seed of Intent.md`](./_archive/STRATEGIST.md%20-%20The%20Seed%20of%20Intent.md)
- [`_archive/The Four Disciplines of Prompting: A New Framework for AI-Powered Work.md`](./_archive/The%20Four%20Disciplines%20of%20Prompting%3A%20A%20New%20Framework%20for%20AI-Powered%20Work.md)

See [`_archive/README.md`](./_archive/README.md) for why each was archived (evidence table: last-commit date, inbound link count, reason).

`docs/The FRACTAL Multi-Agent System.pptx` was deleted (not archived) — see `_archive/README.md` for why.
