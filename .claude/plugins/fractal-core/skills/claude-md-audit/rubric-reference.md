# Rubric Reference (for the `claude-md-audit` skill)

This file is a stable pointer for the skill. The **authoritative rubric** lives at:

> [`docs/claude-md-rubric.md`](../../../docs/claude-md-rubric.md)

Read that file before running. It defines:

- 12 scored dimensions (0/1/2 each, 24-point total)
- 1 advisory dimension (D13 — Output Discipline)
- Letter-grade bands (A 22–24 / B 18–21 / C 12–17 / D 6–11 / F 0–5)

## Why a separate pointer file?

Skills live inside `.claude/skills/` and can be copied into other projects. The rubric lives in `docs/` so it can be cited by gap analyses, roadmaps, and the skill itself without duplication. This pointer file is here so a future maintainer reading the skill directory in isolation knows exactly where the rubric lives and doesn't inline a stale copy.

## If the rubric is missing

Halt the skill and report: `rubric not found at docs/claude-md-rubric.md — cannot score without it`. Do not improvise a rubric inline; that defeats the point of a durable, version-controlled standard.

## Updating the rubric

- The rubric is versioned (see its "Change log" section).
- When adding/removing dimensions, bump the version and update this skill's `SKILL.md` Step 2 wording if the dimension count changes.
- Every audit report records the rubric version in its header — that's how we track scoring methodology over time.
