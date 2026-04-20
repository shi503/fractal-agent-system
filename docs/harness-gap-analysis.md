# Harness Gap Analysis — FRACTAL vs. The Field

**Status:** Observation only (recommendations go in [`harness-upgrade-roadmap.md`](./harness-upgrade-roadmap.md))
**Date:** 2026-04-14
**Scoring source:** `docs/research-claude-code-harness.md` (patterns from public source analysis) + primary README/docs fetches for each competitor
**Scoring scale:** 0 (absent) / 1 (partial) / 2 (strong). Max per harness = 24. Ties broken by leverage.

---

## Harnesses benchmarked

| # | Harness | Repo | Flavor |
|---:|---|---|---|
| 1 | **Claude Code (stock)** | Anthropic (public source) | Reference baseline — the harness everything else orbits |
| 2 | **Superpowers** | [`obra/superpowers`](https://github.com/obra/superpowers) | Skills framework enforcing TDD / debugging / brainstorm methodology (~152K★) |
| 3 | **gstack** | [`garrytan/gstack`](https://github.com/garrytan/gstack) | Role-based slash-commands (CEO / Designer / QA / Release) |
| 4 | **OpenCode** | `sst/opencode` (~95K★) | Go terminal agent, 75+ models |
| 5 | **OpenHands** | [`All-Hands-AI/OpenHands`](https://github.com/All-Hands-AI/OpenHands) (~68K★) | Autonomous single-agent SDK, SWE-Bench 77.6 |
| 6 | **Cline** | [`cline/cline`](https://github.com/cline/cline) (~59K★) | VS Code extension, Plan/Act modes, checkpoints |
| 7 | **everything-claude-code** | `affaan-m/everything-claude-code` | Performance optimization pack across Claude/Codex/Opencode/Cursor |
| 8 | **LangGraph / AutoGen** | Microsoft & LangChain | Framework-level multi-agent orchestration |
| ★ | **FRACTAL** | this repo | 4-tier orchestration (Strategist → Architect → Feature Lead → Sub-Agent) + BLUEPRINT router + 4-layer eval |

---

## Scoring dimensions

| # | Dimension | Why it matters |
|---|---|---|
| D1 | Role specialization | Keeps subagents scoped, reduces context pollution |
| D2 | Context / memory management | Prevents drift, bounds token cost across long sessions |
| D3 | Skills ecosystem | Mandatory workflows beat optional ones (Superpowers thesis) |
| D4 | Hooks / extensibility surface | Can the harness be extended without forking? |
| D5 | Permission model | Deny-first safety, separate-code-path enforcement |
| D6 | Plan-first discipline | Read-only exploration before writes |
| D7 | Evaluation / quality gates | "Done" has a measurable definition |
| D8 | CLAUDE.md-equivalent anchor | Reloaded-every-turn project context |
| D9 | Orchestration (BLUEPRINT / DAG) | Multi-workstream dependency tracking |
| D10 | Output discipline / token hygiene | Numeric caps beat adjectives |
| D11 | Subagent forking model | Fork / teammate / worktree modes |
| D12 | Observability (PULSE-equivalent) | Live execution trace, not just final logs |

---

## Score matrix

| Harness | D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | D9 | D10 | D11 | D12 | **Total** | % |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| Claude Code (stock) | 2 | 2 | 2 | 2 | 2 | 2 | 1 | 2 | 0 | 2 | 2 | 1 | **20** | 83% |
| Superpowers | 2 | 1 | 2 | 2 | 1 | 2 | 2 | 2 | 0 | 1 | 2 | 1 | **18** | 75% |
| gstack | 2 | 1 | 2 | 1 | 0 | 1 | 2 | 2 | 1 | 0 | 1 | 1 | **14** | 58% |
| OpenCode | 1 | 1 | 1 | 2 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | **12** | 50% |
| OpenHands | 1 | 1 | 1 | 2 | 2 | 0 | 2 | 0 | 0 | 0 | 1 | 1 | **11** | 46% |
| Cline | 1 | 1 | 1 | 1 | 2 | 2 | 0 | 1 | 0 | 0 | 1 | 2 | **12** | 50% |
| everything-claude-code | 1 | 2 | 1 | 2 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | **13** | 54% |
| LangGraph / AutoGen | 2 | 1 | 0 | 2 | 1 | 1 | 1 | 0 | 2 | 0 | 2 | 1 | **13** | 54% |
| **FRACTAL** | **2** | **1** | **1** | **0** | **1** | **1** | **2** | **2** | **2** | **0** | **1** | **2** | **15** | **63%** |

**Headline:** FRACTAL ranks 3rd overall behind Claude Code and Superpowers, leads on orchestration (D9) and observability (D12), ties best-in-class on CLAUDE.md (D8) and evaluation (D7), but sits at **zero** on hooks (D4) and output discipline (D10) — two dimensions where the public source analysis showed Anthropic extracted real uplift.

---

## Dimension-by-dimension narrative

### D1 — Role specialization

- **Claude Code (2):** 3 built-in subagent types (Plan, Explore, general-purpose) + unlimited custom subagents via agent definitions.
- **Superpowers (2):** Fresh subagent per task with two-stage review (spec compliance → code quality) — the `subagent-driven-development` skill.
- **gstack (2):** Distinct role personas (CEO, Designer, Engineer Manager, QA Lead, Security Officer, Release Engineer) as slash commands.
- **FRACTAL (2):** 4-tier explicit separation (Strategist / Architect / Feature Lead / Sub-Agent) documented in `.claude/agents/*.md`.
- **OpenCode / OpenHands / Cline (1):** Single-agent default; subagents exist but aren't the organizing principle.
- **LangGraph / AutoGen (2):** Multi-agent is the *product*; roles defined as graph nodes.

FRACTAL is **at parity with the best**; its 4 tiers are arguably more opinionated than Claude Code's 3.

### D2 — Context / memory management

- **Claude Code (2):** Three-layer memory index (pointers / topic files / transcripts), `autoDream` idle consolidation, memory-as-hint verification, `MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES = 3` circuit breaker ([harness research §7](./research-claude-code-harness.md)).
- **everything-claude-code (2):** Explicitly markets "memory and research-first development" as its core value-add.
- **FRACTAL (1):** Strategist doc + BLUEPRINT + PULSE + HANDOFF provide *persistent* context, but no three-layer pointer index, no verification-on-recall, no compaction circuit-breaker. Memory is structured but not disciplined.
- **Others (1):** Informal; no layered pattern.

**Gap for FRACTAL:** formal verification-on-recall, idle-time consolidation pattern, circuit-breakers on any retry loop.

### D3 — Skills ecosystem

- **Superpowers (2):** Composable mandatory skills ("the agent checks for relevant skills before any task"). Covers TDD, debugging (4-phase), brainstorming, code review, git worktrees, writing-skills meta-skill.
- **gstack (2):** 23 opinionated slash commands spanning plan / build / review / ship / retro.
- **Claude Code (2):** Skills are a first-class harness primitive with lazy-loaded schemas.
- **FRACTAL (1):** 7 skills (`fractal-init`, `pulse`, `handoff`, `gap-analysis`, `quality-pass`, `commit-summarize`, `claude-md-audit`). Functional but light compared to 20+ in Superpowers/gstack. No TDD / debugging / brainstorm methodology skills.
- **LangGraph / AutoGen (0):** Skills aren't a framework concept.

**Gap:** Methodology skills (TDD-loop, systematic-debug, Socratic-brainstorm) are missing. Each of those is a direct Superpowers clone target.

### D4 — Hooks / extensibility

- **Claude Code (2):** **25 event hooks** at every execution stage — tool call pre/post, context changes, subagent spawn, compaction ([harness research §8](./research-claude-code-harness.md)).
- **OpenHands (2):** Feature flags + plugin infra + multi-integration surface.
- **Superpowers (2):** `.claude-plugin`, `.cursor-plugin`, `.codex`, `.opencode` directories — platform-specific hooks.
- **everything-claude-code (2):** Markets multi-host support (Claude/Codex/Opencode/Cursor) as a core feature.
- **LangGraph / AutoGen (2):** Extension via graph node types.
- **FRACTAL (0):** No hooks. `.claude/settings.local.json` contains only a Bash permission allowlist. No event hooks, no pre/post-tool interceptors, no pluggable extension points.

**This is FRACTAL's biggest single gap.** Every competitor scores ≥1 here; FRACTAL scores 0.

### D5 — Permission model

- **Claude Code (2):** Three-tier (auto / prompt / block), deny-first, `canUseTool` central gate, background Sonnet 4.6 side-query classifier for borderline cases ([harness research §5](./research-claude-code-harness.md)).
- **Cline (2):** Human-in-the-loop approval for every file/terminal change — explicit review gate.
- **OpenHands (2):** RBAC + Docker container sandboxing.
- **FRACTAL (1):** Uses Claude Code's native permission model via settings, with a Bash allowlist. No FRACTAL-specific permission layering, no tier-aware Sub-Agent gating.
- **gstack (0):** Runs unconstrained on top of Claude Code; no additional permission policy.

**Gap:** Sub-Agent tier should have its own permission classifier (side-query pattern from the public source analysis) for Bash calls rather than inheriting the parent's allowlist wholesale.

### D6 — Plan-first discipline

- **Cline (2):** Plan vs Act modes are the core UX distinction.
- **Claude Code (2):** Plan mode is a permission state (write tools disabled), not a behavioral suggestion.
- **Superpowers (2):** Plans require human sign-off before execution proceeds.
- **FRACTAL (1):** Architect does blueprinting, Feature Lead receives a PRD — planning is **implicit** in the tiering. But there's no enforced read-only state for the Feature Lead during its first exploration phase.
- **OpenHands (0):** Interactive/conversational by default.

**Gap:** Make the Feature Lead explicitly enter a plan-mode-equivalent exploration phase before first write, mirroring Claude Code's permission-pipeline enforcement.

### D7 — Evaluation / quality gates

- **FRACTAL (2):** **4-layer evaluation pipeline** (deterministic / LLM-judgment / persona / strategic) documented in `.claude/fractal/EVAL_TEMPLATES/`. This is best-in-class.
- **Superpowers (2):** TDD red-green-refactor enforces tests-before-code; subagent review as a second quality gate.
- **gstack (2):** `/review`, `/qa`, `/cso` (security), `/canary` post-deploy — shipping has quality gates.
- **OpenHands (2):** Benchmarks repo + SWE-Bench 77.6 — institutionalized measurement.
- **Cline (0):** No explicit eval framework.

**FRACTAL leads here.** No competitor has a 4-layer pipeline equivalent. The one queued improvement is Q6/Q7 in the Layer 2 template (already flagged in `BEST-PRACTICES.md`).

### D8 — CLAUDE.md-equivalent anchor

- **Claude Code (2):** CLAUDE.md is the canonical pattern.
- **Superpowers (2):** Platform-specific files (CLAUDE.md, GEMINI.md).
- **gstack (2):** Injects its own section into CLAUDE.md naming its slash commands.
- **FRACTAL (2):** `.claude/CLAUDE.md` audited at 22/24 (Band A) in [`2026-04-14-taskflow.md`](./claude-md-audits/2026-04-14-taskflow.md).
- **OpenHands / LangGraph (0):** No equivalent.
- **OpenCode / Cline / everything-claude-code (1):** Supported but not central.

**FRACTAL is at parity.** Room for 23/24 or 24/24 per the audit's top improvement targets (templates expansion + token hygiene).

### D9 — Orchestration (BLUEPRINT / DAG)

- **FRACTAL (2):** BLUEPRINT YAML + `router.py` state machine. Explicit DAG with parallel workstreams and dependencies. Best-in-class of this set.
- **LangGraph / AutoGen (2):** Graphs are the organizing primitive.
- **gstack (1):** `/autoplan` pipelines CEO → design → eng review, but no persisted DAG.
- **Claude Code (0):** No cross-session orchestration primitive — each session is standalone.
- **All others (0):** N/A.

**FRACTAL leads.** This is the system's most differentiated asset; no single-session harness ships anything equivalent.

### D10 — Output discipline / token hygiene

- **Claude Code (2):** Explicit word caps (≤25 between tool calls, ≤100 final) from A/B-tested ~1.2% token reduction ([harness research §10](./research-claude-code-harness.md)). Explicit ban on opening affirmations / trailing summaries. Prompt cache boundary with `DANGEROUS_uncachedSystemPromptSection` tagging.
- **Superpowers (1):** Mentions complexity reduction but no numeric output caps.
- **everything-claude-code (1):** "Performance optimization" is the marketing angle but the README doesn't show concrete numeric discipline.
- **FRACTAL (0):** **No output discipline anywhere.** No word caps in any agent definition. No cache boundary convention in agent prompts. Agent definitions edit freely, invalidating cache on every change.
- **gstack / Cline / OpenHands / LangGraph (0):** Not addressed.

**Tied-zero with most of the field, but Claude Code showed concrete uplift here.** Adopting the word caps is a near-free win. The cache boundary is a medium-effort win with compounding payoff.

### D11 — Subagent forking model

- **Claude Code (2):** Three explicit modes — fork (byte-identical context, near-free via prompt cache) / teammate (fresh context) / worktree (isolated) ([harness research §6](./research-claude-code-harness.md)).
- **LangGraph / AutoGen (2):** Agent spawning is a first-class framework operation.
- **Superpowers (2):** Fresh subagent per task + git-worktrees skill for isolation.
- **FRACTAL (1):** Sub-Agent tier exists as a concept but doesn't formalize fork vs teammate vs worktree. All sub-agent invocations look like "teammate" mode.
- **Others (1):** Implicit.

**Gap:** Explicit classification of Sub-Agent flavors. A "fork" flavor (inheriting Feature Lead context) would be much cheaper for parallel exploration tasks than today's stateless teammate-default.

### D12 — Observability (PULSE-equivalent)

- **FRACTAL (2):** **PULSE heartbeats + HANDOFF artifacts** are a first-class pattern. Each workstream emits a live execution trace and a final artifact.
- **Cline (2):** Checkpoint system with workspace snapshots — "Compare" and "Restore."
- **Claude Code (1):** Session-local logs; no pulse equivalent across runs.
- **Superpowers (1):** Writes plans and reviews to markdown as execution artifacts.
- **Others (1):** Generic logging.

**FRACTAL leads or ties.** PULSE is a genuine differentiator; no other open-source harness ships a structured live-execution heartbeat pattern.

---

## Where FRACTAL leads

1. **Orchestration (D9 = 2):** BLUEPRINT + router state machine is unmatched in this set.
2. **Evaluation (D7 = 2):** 4-layer eval pipeline has no single-session equivalent.
3. **Observability (D12 = 2):** PULSE heartbeats are a genuine novelty.
4. **Role specialization (D1 = 2):** 4 tiers are more opinionated than Claude Code's 3.
5. **CLAUDE.md (D8 = 2):** Audit confirms Band A; only polish items remain.

## Where FRACTAL is at parity

- **Role specialization (D1):** Matches Superpowers and gstack.
- **CLAUDE.md (D8):** Matches Claude Code / Superpowers / gstack.
- **Permission model (D5) and subagent forking (D11):** Inherits Claude Code's baseline without adding or subtracting.

## Where FRACTAL is behind (and by how much)

| Dimension | Gap | Leader | FRACTAL | Behind by |
|---|---|---|---:|---:|
| **D4 — Hooks / extensibility** | Zero hooks defined; settings has only a Bash allowlist. Source analysis showed 25 hook points in Claude Code. | Claude Code (2) | 0 | **–2** |
| **D10 — Output discipline** | No numeric caps, no affirmation ban, no cache boundary pattern in agent prompts. Source analysis showed ~1.2% token savings from this alone. | Claude Code (2) | 0 | **–2** |
| **D3 — Skills ecosystem** | 7 skills vs Superpowers' 20+ methodology skills. Missing TDD, systematic-debug, Socratic-brainstorm. | Superpowers (2) | 1 | **–1** |
| **D2 — Context / memory** | No three-layer index, no compaction circuit-breaker, no memory-as-hint verification. | Claude Code (2) | 1 | **–1** |
| **D6 — Plan-first discipline** | Tiering implies planning but doesn't enforce read-only exploration before first write. | Claude Code / Cline (2) | 1 | **–1** |
| **D5 — Permissions** | No side-query classifier for Sub-Agent Bash. Allowlist only. | Claude Code (2) | 1 | **–1** |
| **D11 — Subagent flavors** | No fork / teammate / worktree classification. | Claude Code / LangGraph (2) | 1 | **–1** |

**Net negative gaps:** 9 points across 7 dimensions. If FRACTAL closed D4 and D10 alone, it would tie Claude Code at 19 total.

---

## Citation notes

Each competitor's scoring was grounded in:

- **Claude Code:** `docs/research-claude-code-harness.md` (secondary-source synthesis).
- **Superpowers:** [github.com/obra/superpowers README](https://github.com/obra/superpowers) fetched for skill list and methodology.
- **gstack:** [github.com/garrytan/gstack README](https://github.com/garrytan/gstack) — 23 slash-command inventory.
- **OpenHands:** [github.com/All-Hands-AI/OpenHands README](https://github.com/All-Hands-AI/OpenHands) — feature flags + enterprise RBAC.
- **Cline:** [github.com/cline/cline README](https://github.com/cline/cline) — Plan/Act modes, checkpoints, `copilot_swe_agent_use_subagents` flag.
- **OpenCode / everything-claude-code / LangGraph:** web searches (Stoneforge, Fungies, NocoBase roundups) + own READMEs.
- **FRACTAL:** this repo — `.claude/agents/*.md`, `.claude/skills/*`, `.claude/fractal/router.py`, `BEST-PRACTICES.md`, `docs/The FRACTAL Evaluation Framework.md`, `docs/PULSE.md`, `docs/HANDOFF.md`, and the just-written `docs/claude-md-audits/2026-04-14-taskflow.md`.

---

## What this doc explicitly does NOT do

- Does not prescribe which gaps to close first → see [`harness-upgrade-roadmap.md`](./harness-upgrade-roadmap.md).
- Does not score dimensions the rubric doesn't cover (UX, model cost, IDE integration). Those are intentional omissions — scope is *harness quality*, not product comparison.
- Does not audit closed-source agents (Cursor, Zed's AI, GitHub Copilot Workspace). Those are outside the "harness we can study and adopt from" scope.
