# FRACTAL Harness Upgrade Roadmap

**Status:** Advisory (not yet encoded as a BLUEPRINT)
**Date:** 2026-04-14 — see [Status as of 2026-08-28](#status-as-of-2026-08-28) for what has since shipped
**Source inputs:**
- [`research-claude-code-harness.md`](./research-claude-code-harness.md) — what "best practice" looks like
- [`harness-gap-analysis.md`](./harness-gap-analysis.md) — where FRACTAL stands (15 / 24)
- [`claude-md-audits/2026-04-14-taskflow.md`](./claude-md-audits/2026-04-14-taskflow.md) — first CLAUDE.md audit (22 / 24)

---

## Status as of 2026-08-28

**Shipped:**
- **#1 — Output-discipline section, every agent prompt.** All four `.claude/plugins/fractal-core/agents/*.md` carry a `§0. Reading rules` table with word caps, an affirmation ban, and a no-trailing-summary rule — the exact shape WS-1 specified. See the [2026-08-28 re-score](./harness-gap-analysis.md#2026-08-28-re-score-fractal-only) for the resulting D10 move (0 → 2).
- **#12 — Memory-as-hint verification rule**, as a side effect of #1: the same §0 block adds "verify recalled facts before acting — read the live state pointer first."
- Beyond the ranked backlog below: the plugin/marketplace port itself (not originally a roadmap line item) — six plugins, 37 skills, the decision ledger, the committed BM25 wiki index, the scheduled runner, and the `.claude/rules/` layer. See `README.md`'s capability tour.

**Not shipped — still open exactly as scoped below:** #2 (CLAUDE.md audit top-3), #3 (hooks MVP), #4 (cache-boundary convention), #5/#6/#7 (TDD-loop / systematic-debug / Socratic-brainstorm methodology skills), #8 (plan-mode enforcement), #9 (subagent-flavor classification), #10 (permission classifier). None of these should be assumed done because adjacent 2.0 work landed — verify against the tree before citing any of them as shipped.

**Next landing — typed work contracts.** An early, exploratory foundation doc and a set of JSON Schemas (capability, handoff, evidence, event, context-artifact, work-contract) live under `docs/fractal-harness-fork/` — not wired into the router, not validated by any deterministic gate, not a roadmap backlog item as of this writing. Treat it as direction, not a shipped capability: the next roadmap revision should decide whether to formalize it into a numbered backlog item (schema validation in `router.py update`, a `check-contracts.sh` gate) or fold specific pieces into the existing HANDOFF/PULSE templates instead of introducing a parallel contract format.

---

## Executive summary

1. **FRACTAL is 3rd of 9 harnesses measured**, leading on orchestration, evaluation, and observability but trailing on hooks, output discipline, and skills ecosystem depth.
2. **Two zero-scoring dimensions — D4 (hooks) and D10 (output discipline) — are the highest-leverage wins.** Closing both would raise the gap-analysis total from 15 → 19, tying Claude Code at 83%.
3. **The 4-tier orchestration (Strategist → Architect → Feature Lead → Sub-Agent) is a genuine moat.** Nothing in the field — not even Superpowers or gstack — matches it. Protect and extend it, don't redesign it.
4. **Output discipline is free money.** Adding numeric word caps to every `.claude/agents/*.md` is a single workstream worth an immediate A/B.
5. **A "methodology skills" workstream** — porting Superpowers' TDD / systematic-debug / Socratic-brainstorm patterns into FRACTAL's skill layout — is the single largest jump in perceived quality per unit effort.

---

## Prioritization framework

Every candidate is scored on four axes:

- **Impact (L / M / H):** expected lift in agent quality, developer UX, or token efficiency.
- **Effort (XS / S / M / L / XL):** XS = minutes; S = hours; M = half-day; L = 1–2 days; XL = multi-day.
- **Risk (L / M / H):** chance of destabilizing existing workflows.
- **Dependency:** does this unblock other items?

Priority is a function of `Impact / Effort` with Risk as a tiebreaker (lower risk wins ties).

---

## Ranked upgrade backlog

| # | Upgrade | Impact | Effort | Risk | Deps | Source gap |
|---:|---|:-:|:-:|:-:|---|---|
| **1** | ✅ **SHIPPED** (2026-08-28) — **Add output-discipline section to every agent prompt** (word caps, no affirmations, no trailing summaries) | H | XS | L | — | [Gap D10](./harness-gap-analysis.md#d10--output-discipline--token-hygiene) · [Research §10](./research-claude-code-harness.md) |
| **2** | **Apply CLAUDE.md audit top-3 recommendations** (canonical queries/forms/tests, link-out Design Tokens + Server Action, add output-discipline section) | H | S | L | — | [Audit](./claude-md-audits/2026-04-14-taskflow.md) |
| **3** | **Hooks inventory + minimum-viable settings-based hook set** (PostToolUse for Bash, PreCompact logging, SessionStart loader) | H | M | M | — | [Gap D4](./harness-gap-analysis.md#d4--hooks--extensibility) |
| **4** | **Cache-boundary convention in agent prompts** (static preamble / dynamic suffix split; `DANGEROUS_uncachedSystemPromptSection` tag convention) | H | S | L | #1 | [Research §2](./research-claude-code-harness.md) |
| **5** | **Methodology skill: TDD loop** (red-green-refactor; mandatory tests-before-code for Feature Lead) | H | M | M | — | [Gap D3](./harness-gap-analysis.md#d3--skills-ecosystem) |
| **6** | **Methodology skill: systematic-debug** (4-phase root cause — reproduce, isolate, diagnose, fix+test) | H | M | L | — | [Gap D3](./harness-gap-analysis.md#d3--skills-ecosystem) |
| **7** | **Methodology skill: Socratic brainstorm** (called by Architect before decomposition) | M | S | L | — | [Gap D3](./harness-gap-analysis.md#d3--skills-ecosystem) |
| **8** | **Feature Lead plan-mode enforcement** (read-only exploration phase required before first Write/Edit) | H | M | M | #3 | [Gap D6](./harness-gap-analysis.md#d6--plan-first-discipline) |
| **9** | **Sub-Agent fork / teammate / worktree classification** (encode which flavor in workstream PRD) | M | S | L | — | [Gap D11](./harness-gap-analysis.md#d11--subagent-forking-model) |
| **10** | **Side-query permission classifier for Sub-Agent Bash calls** (instead of flat allowlist) | M | M | M | #3 | [Gap D5](./harness-gap-analysis.md#d5--permission-model) |
| **11** | **Three-layer memory convention in CLAUDE.md** (pointers always loaded; topic files on demand; transcripts greppable) | M | S | L | #2 | [Gap D2](./harness-gap-analysis.md#d2--context--memory-management) |
| **12** | ✅ **SHIPPED** (2026-08-28, as a side effect of #1) — **Memory-as-hint verification rule** (Architect must verify recalled facts before acting on them) | M | XS | L | #11 | [Research §7](./research-claude-code-harness.md) |
| **13** | **Compaction / retry circuit breakers** (`MAX_CONSECUTIVE_*` constants anywhere Feature Lead retries) | M | S | L | — | [Research §7](./research-claude-code-harness.md) |
| **14** | **Layer 2 eval template Q6/Q7** (already queued in `BEST-PRACTICES.md` §3) | M | XS | L | — | `BEST-PRACTICES.md` §3 |
| **15** | **False-positive registry for LLM judge** (so Layer 2 evals can learn from prior misfires) | M | M | L | #14 | `BEST-PRACTICES.md` §3 |
| **16** | **"MAGIC DOC" convention for PRDs and HANDOFFs** (idle consolidator updates drifted sections, scoped to one file) | M | L | M | #3 | [Research §11](./research-claude-code-harness.md) |
| **17** | **gstack-style role-specialized skills** (`/cso` security audit, `/canary` post-deploy, `/retro` retrospective) | L | L | L | #5–7 | [Gap D3](./harness-gap-analysis.md#d3--skills-ecosystem) |
| **18** | **Tool output cap convention** (25K token default; disk overflow) in Sub-Agent tier | L | M | M | #3 | [Research §4](./research-claude-code-harness.md) |
| **19** | **`isReadOnly` / `isConcurrencySafe` annotation on agent tools and skills** | L | S | L | — | [Research §4](./research-claude-code-harness.md) |
| **20** | **Verification Agent hard rules in CLAUDE.md** ("reading is not verification. Run it.") | L | XS | L | #2 | [Research §12](./research-claude-code-harness.md) |
| **21** | **BLUEPRINT YAML schema extension** to record subagent flavor + expected model tier per workstream | L | M | M | #9 | [Gap D11](./harness-gap-analysis.md#d11--subagent-forking-model) |
| **22** | **Skill performance telemetry** (which skills get invoked, success rate, average tool-call count) | L | L | M | #3 | [Gap D3](./harness-gap-analysis.md#d3--skills-ecosystem) |
| **23** | **Re-run `claude-md-audit` quarterly** as a cadence item | M | XS | L | — | [Rubric v1.0](./claude-md-rubric.md) |
| **24** | **Agent-overlay (`.local.md`) pattern** for per-project Architect/Feature Lead customization without forking | L | M | L | — | inferred from public source; not cited |

---

## Top 5 recommended next workstreams

These are the five roadmap items that should be candidates for the next BLUEPRINT. Each is scoped small enough to execute as one Feature Lead invocation.

### WS-1 — Output Discipline Rollout — ✅ SHIPPED (2026-08-28)

**Problem:** FRACTAL scores 0 / 2 on output discipline. Claude Code's internal A/B showed ~1.2% token reduction from replacing generic "be concise" with explicit numeric caps. Across 4 agent tiers and every skill, that compounds.

**Approach:** Add a stock "## Output Discipline" section to each of `.claude/agents/{strategist,architect,feature-lead,sub-agent}.md` and every `.claude/skills/*/SKILL.md`. Section contains: ≤25 words intermediate / ≤100 words final / no opening affirmations / no trailing summaries / "reading is not verification — run it." Same section, same wording, copy-paste.

**Acceptance criteria:**
- Every agent file contains the section verbatim.
- Every skill file contains the section verbatim.
- CLAUDE.md adds a pointer to the convention.
- No existing instructions are silently overridden.

**Effort:** S (1–2 hours).

### WS-2 — Apply CLAUDE.md Audit Top 3

**Problem:** `.claude/CLAUDE.md` scores 22 / 24 (Band A). The first audit identifies three concrete edits to reach 24 / 24 + D13 advisory. Shipping these turns the reference CLAUDE.md into a true exemplar for downstream projects copying the template.

**Approach:** Apply each of the three before/after diffs in [`2026-04-14-taskflow.md`](./claude-md-audits/2026-04-14-taskflow.md):
1. Add canonical RSC query, form, and test templates.
2. Move Design Token System + full Server Action template into new `.SPECS/guides/design-tokens.md` and `.SPECS/guides/server-actions.md`; replace with 2-line pointers.
3. Add Output Discipline section (WS-1 convention).

**Acceptance criteria:**
- Re-running `claude-md-audit` scores 24 / 24.
- Line count of `.claude/CLAUDE.md` drops below 300.
- Linked-out guide files exist and contain the moved content.

**Effort:** S (1–2 hours).

### WS-3 — Hook Infrastructure (MVP)

**Problem:** FRACTAL has zero hooks. Every competitor scores ≥1. Hooks are how Claude Code extends behavior without forking, and how gstack / Superpowers layer opinionated workflow on top of the stock harness.

**Approach:** Ship three hooks via `.claude/settings.json` (not `.local.json` — this is project-level, not user-level):

1. **`PostToolUse` on Bash** — logs every Bash command to `.claude/fractal/.bash-log.jsonl` for later audit. Pure observability.
2. **`SessionStart`** — emits a one-line marker to `.claude/fractal/.session-log.jsonl` so we can correlate sessions with HANDOFFs.
3. **`PreCompact`** — writes the current context snapshot (sections only, not content) so we can debug compaction losses.

Document the hook inventory in `docs/fractal-hooks.md` so adding a 4th hook doesn't require rediscovering the pattern.

**Acceptance criteria:**
- `settings.json` contains the three hook definitions.
- All three hooks fire in a sanity-check session; logs appear.
- `docs/fractal-hooks.md` explains each hook's contract.
- No hook writes to the live workstream directory — hooks are observability only in v1.

**Effort:** M (half-day, mostly reading the Claude Code hooks documentation and picking the right event names).

### WS-4 — TDD-Loop Methodology Skill

**Problem:** Superpowers' enforcement of RED-GREEN-REFACTOR is widely credited as the single most impactful methodology skill. FRACTAL has no equivalent. For a test-heavy stack (TaskFlow uses Vitest + Playwright), this is a direct quality lift.

**Approach:** Create `.claude/skills/tdd-loop/SKILL.md`. When invoked (or when a Feature Lead begins a workstream that touches code with existing tests), the skill enforces: write the failing test first → commit the red state → write minimal implementation → commit green → refactor → commit. Each phase requires evidence (test output, commit SHA) before the next.

**Acceptance criteria:**
- `SKILL.md` exists with the RED-GREEN-REFACTOR phases enumerated.
- Feature Lead PRD template updated so workstreams can declare `tdd-loop: required`.
- First dogfooded workstream uses the skill end-to-end; HANDOFF records the three commits.

**Effort:** M (half-day).

### WS-5 — Feature Lead Plan-Mode Enforcement

**Problem:** Feature Leads today can write files on their first tool call. Claude Code enforces a read-only plan phase via the permission pipeline; Cline does it via UX mode. FRACTAL does neither.

**Approach:** Extend the Feature Lead agent definition with an explicit two-phase contract: **Phase 1 (read-only)** — must complete exploration and emit a brief plan artifact to `.claude/fractal/workstreams/{workstream}/PLAN.md` before any Write/Edit tool call. **Phase 2 (write)** — allowed only after PLAN.md exists and is non-empty. Enforcement is prompt-level in v1; hook-level enforcement becomes a follow-up once WS-3 lands.

**Acceptance criteria:**
- `feature-lead.md` prompt updated with the two-phase contract.
- Workstream directory structure updated to include `PLAN.md`.
- At least one workstream executed under the new contract; its PLAN.md and HANDOFF.md both exist.

**Effort:** M (half-day).

---

## Dependency graph (top 5)

```
WS-1 (Output discipline)  ──┐
                            ├──► WS-2 (CLAUDE.md polish)
WS-3 (Hooks MVP) ───────────┼──► WS-5 (Plan mode; hook enforcement in v2)
                            │
WS-4 (TDD-loop skill) ──────┘    (independent; can run in parallel)
```

WS-1 unblocks WS-2's output-discipline section. WS-3 unblocks the hook-based enforcement variant of WS-5 but isn't required for WS-5 v1.

---

## Out of scope / deferred

- **KAIROS-style autonomous daemon mode** (research §6). Significant architecture commitment; defer until the core roadmap ships.
- **ULTRAPLAN remote-planning model** (research §6). Requires remote-execution infra not currently in FRACTAL's surface.
- **Zig-level DRM / anti-distillation** (research §12). Out of scope for an open harness.
- **Undercover mode** (research §12). Only relevant for closed deployments.
- **Auto-maintained MAGIC DOCs for every PRD.** Listed in backlog (#16) but deferred out of top 5 because idle-consolidation requires hook infra (WS-3) to be battle-tested first.
- **Agent-overlay `.local.md` pattern** (#24). Speculative — no direct source evidence, and current single-project FRACTAL usage doesn't need it yet.
- **Cross-harness portability** (running FRACTAL atop Codex / OpenCode). Interesting but off-mission; FRACTAL's value is the 4-tier orchestration, which is Claude Code's agent-subagent model.

---

## Measurement

Before executing the top 5, snapshot:

- Current gap-analysis score: **15 / 24 (63%)**
- Current CLAUDE.md audit: **22 / 24 (92%, Band A)**
- Count of skills: **7**
- Count of hooks: **0**
- Count of agent tiers: **4**

Target after top 5 execution (estimated):

- Gap-analysis: **19 / 24 (79%)** — closes D4 (hooks) from 0 → 1 and D10 (output discipline) from 0 → 2; nudges D3 (skills) from 1 → 2 via TDD-loop; nudges D6 (plan-first) from 1 → 2 via WS-5.
- CLAUDE.md audit: **24 / 24 (100%) + D13 advisory satisfied** after WS-2.
- Skills: **8** (add `tdd-loop`).
- Hooks: **3** (WS-3 MVP).
- Agent tiers: **4** (unchanged).

Re-run both `claude-md-audit` and a fresh pass of the gap analysis after the top-5 ships; commit the delta.

**2026-08-28 actual (1 of 5 shipped, #4 skills nudge unplanned):** Gap-analysis: **18 / 24 (75%)** — see the [2026-08-28 re-score](./harness-gap-analysis.md#2026-08-28-re-score-fractal-only) for the full breakdown; D10 closed as predicted, D3 moved as a byproduct of the plugin port rather than the TDD-loop skill, D4 did not move. CLAUDE.md audit: not re-run (still citing 22/24 from 2026-04-14; do not treat as current — the file changed since). Skills: **37** across 6 plugins (roadmap predicted 8; actual growth came from the plugin port, not the single `tdd-loop` skill this section anticipated). Hooks: **0** (unchanged). Agent tiers: **4** (unchanged).
