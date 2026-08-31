# Harness Gap Analysis — FRACTAL vs. The Field

**Status:** Observation only (recommendations go in [`harness-upgrade-roadmap.md`](./harness-upgrade-roadmap.md))
**Date:** 2026-04-14 (original score below) — see [2026-08-28 re-score](#2026-08-28-re-score-fractal-only) for the current FRACTAL row, and the [2026-08-30 D13 addendum](#2026-08-30-addendum--d13-comprehensibility) for the new comprehensibility dimension and the HumanLayer comparator
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
| 9 | **HumanLayer** | [humanlayer.dev](https://humanlayer.dev) | Six-phase QRSPI workflow (Questions → Research → Design → Structure → Plan → Implement) under the banner "Do not outsource the thinking"; added 2026-08-30 as the D13 comparator only — chosen for onboarding clarity, not re-benchmarked on D1–D12 (see the [D13 addendum](#2026-08-30-addendum--d13-comprehensibility)) |
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
| D13 | Comprehensibility | Can a stranger state what the project is for, **and** complete a first run, from the README alone? 0 = neither, 1 = one, 2 = both. Added 2026-08-30 — every prior dimension above measures an internal capability axis; none asks whether an outsider can understand or use the project at all. See the [2026-08-30 addendum](#2026-08-30-addendum--d13-comprehensibility) for scope and scoring. |

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

**D13 note:** this table is the frozen 2026-04-14 snapshot, scored on 12 dimensions (max 24) — D13 (Comprehensibility) did not exist yet and is not applied retroactively to it. Totals above are re-verified as internally consistent (12 rows × 12 cells, summed and cross-checked against the printed `Total`/`%` columns) and unchanged. D13 first applies in the [2026-08-30 addendum](#2026-08-30-addendum--d13-comprehensibility).

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

## 2026-08-28 Re-score — FRACTAL only

**What changed since 2026-04-14:** the plugin/marketplace port (six plugins, 37 skills + 4 tier agents across `fractal-core`/`fractal-planning`/`fractal-tools`/`fractal-wiki`/`fractal-runner`/`fractal-pr-review`), the decision ledger (`tools/decision-ledger/`), the committed BM25 wiki index (`tools/wiki-index/`), the scheduled runner (`tools/scheduled-fractal-runner/`), the `.claude/rules/` path-scoped layer, and — the item that actually moved a score — an "Output Discipline"-equivalent §0 reading-rules block (word caps, no affirmations, no trailing summaries, verify-recalled-facts-before-acting) landed in all four tier agent files. This section re-scores FRACTAL only; the eight competitor rows above are frozen at their 2026-04-14 values (not re-benchmarked this pass) — do not read this as claiming they stood still, only that FRACTAL is the row this repo can attest to firsthand.

| Harness | D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | D9 | D10 | D11 | D12 | **Total** | % | Δ vs 04-14 |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| **FRACTAL** | 2 | 1 | **2** | 0 | 1 | 1 | 2 | 2 | 2 | **2** | 1 | 2 | **18** | **75%** | **+3** |

FRACTAL now ties Superpowers (18/24, 75%) for second place and closes one point of the four-point gap to Claude Code stock (20/24, 83%).

### What moved, dimension by dimension

- **D10 (output discipline: 0 → 2).** The exact upgrade the roadmap's #1 item called for. `.claude/plugins/fractal-core/agents/{architect,strategist,feature-lead,sub-agent}.md` each carry a `§0. Reading rules` table: ≤25-word intermediate / ≤100-word final caps, a ban on opening affirmations, no unsolicited trailing summaries, and "verify [recalled facts] before acting — read the live state pointer first." That last clause is also roadmap item #12 (memory-as-hint verification) — closed as a side effect, not a separate workstream.
- **D3 (skills ecosystem: 1 → 2).** 37 skills across 6 plugins (was 7 flat skills) — breadth now rivals or exceeds Superpowers' 20+ and gstack's 23. Caveat, so this isn't read as full parity: Superpowers' D3=2 rests on *mandatory, enforced* workflow skills (the agent is required to check for a relevant skill before any task); FRACTAL's skills remain slash-invoked or description-triggered, not enforced. The three methodology skills the roadmap named specifically — TDD-loop, systematic-debug, Socratic-brainstorm (roadmap items #4, #5, #6 as WS-4 and neighbors) — did **not** land; there is no `tdd-loop`, `systematic-debug`, or `brainstorm` skill anywhere in the tree. The 2 reflects breadth and organization, not enforcement parity.
- **D4 (hooks: unchanged at 0).** No `settings.json` hook definitions exist anywhere in the repo — only `.claude/settings.local.json`'s Bash permission allowlist, exactly as in April. The `.claude/rules/` path-scoped layer that landed this cycle is a *context-loading* mechanism (auto-injected instructions keyed on file path), not a programmatic event hook (`PreToolUse`/`PostToolUse`/`SessionStart`/etc.) — it does not close this gap and is not counted toward it. Still FRACTAL's single largest deficit versus the field.
- **D2 (context/memory: unchanged at 1).** The verify-before-acting clause (see D10 above) is a real, narrow win for this dimension's "memory-as-hint verification" gap, but the three-layer pointer/topic/transcript index and idle-consolidation pattern the 2026-04-14 analysis called out are still absent, so the dimension stays at partial credit rather than moving to strong.
- **D5, D6, D9, D11 — unchanged.** No side-query Sub-Agent permission classifier (D5), no Feature Lead plan-mode read-only phase or `PLAN.md` gate (D6), no fork/teammate/worktree Sub-Agent flavor classification (D11). D9 (orchestration) stays at its existing max of 2 — router `2.0.0`'s dual blueprint-shape normalization and `tools/router-smoke.sh` reinforce the lead without raising a ceiling that was already full.
- **D7, D8, D12 — unchanged at their existing max of 2.** Reinforced by new evidence (the decision-ledger and repo-hygiene test suites for D7; the scheduled runner's evidence artifacts for D12) but the rubric's 2 was already the ceiling.
- **D8 caveat:** the `2026-04-14-taskflow.md` CLAUDE.md audit (22/24) has not been re-run against the current `.claude/CLAUDE.md`, which grew from 357 to 386 lines this cycle (new plugin/rules/fixture sections) and never had the WS-2 top-3 fixes (canonical query/form/test templates, Design Tokens/Server Action link-out, sub-300-line target) applied. The 2/2 dimension score is a harness-capability judgment (a CLAUDE.md exists and is comprehensive), not a claim that the prior 22/24 audit score still holds unverified — re-run `claude-md-audit` before citing a number.

### Honest headline

FRACTAL closed exactly the two roadmap items with the lowest effort and least cross-dependency (WS-1's output-discipline rollout, and its side-effect on the D2/#12 verification gap) plus grew skills breadth as a byproduct of the plugin port. It did not touch hooks (D4), plan-mode enforcement (D6), the permission classifier (D5), or subagent-flavor classification (D11) — those remain exactly where the 2026-04-14 analysis left them. 18/24 is a real gain, not a swept board.

**Arithmetic recheck (12-dimension total, pre-D13):** 2+1+2+0+1+1+2+2+2+2+1+2 = 18. Matches the printed `Total` and `18/24 = 75%` above. This is the row the D13 addendum below extends.

---

## 2026-08-30 Addendum — D13 Comprehensibility

**What prompted this:** the 2026-04-14 → 2026-08-28 scoring passes measured twelve internal-capability axes and never asked whether an outsider could understand or use the project at all. D13 closes that blind spot. This score is deliberately not self-graded from familiarity with the repo — it is backed by an external test run by a fresh agent instance with no prior exposure to this project, given only the README and told to execute the literal steps.

**Rubric (restated):** can a stranger state what the project is for, **and** complete a first run, **from the README alone**? 0 = neither, 1 = one, 2 = both.

**Tree state scored:** commit `42fce73` ("feat(ws-21): disclose prereqs before the install steps they gate"), the current HEAD as of 2026-08-30. This is after the problem-statement rewrite (`5cbe4ae`), the prereq-disclosure fix (`42fce73`), and the docs triage (`6b9485f`) — all three are reflected in the score below, and it will need re-running if the tree moves again.

### FRACTAL — D13 = 1

**Half satisfied — "state what it's for": yes, externally verified.** A fresh agent given only the README's opening section, with no other file access, restated FRACTAL's purpose, the three failure modes it targets, and why someone would choose it over a single agent session — in its own words, without prompting or hints. Verbatim from that test: *"FRACTAL is a multi-agent orchestration system for Claude Code that breaks large, multi-day engineering epics into dependency-tracked workstreams, using a Python state machine (`router.py`) — not an LLM — to decide what work is unblocked... trading setup overhead for auditability and safer parallelism."* That is an accurate, unprompted restatement — this half is real.

**Half not established — "complete a first run": partial, not verified end-to-end.** The same fresh-agent test independently executed the README's shell-executable Install steps against a clean clone: `tools/check-prereqs.sh` (exit 0, `OK: python3 + PyYAML present.`) and `tools/router-smoke.sh` (exit 0, 7/7 checks, confirmed zero side effects via `git status --porcelain` before/after) both ran exactly as documented — this is the structural fix for the previously-reproducing ImportError-on-first-run failure, and it holds up under independent execution, not just source-reading. But the README's separate **"First Run"** section — the one that actually walks a stranger through using FRACTAL on a real epic (Strategist interview → Architect BLUEPRINT → `/fractal-init` → Feature Lead execution) — was not completable by the test: step 1 invokes "the strategist agent" and step 3 invokes `/fractal-init`, both used before the README defines either (their definitions appear later, in the Capability Tour and How It Works sections). The tester's own words: *"A reader following First Run top-to-bottom would be typing commands referencing agents/skills the doc hasn't yet named."* No independent test has ever run FRACTAL's actual first-run workflow (interview → plan → bootstrap → execute) end-to-end from the README — only the install/verify prerequisite subset, which is necessary but is not the same claim.

**Score:** 1. Comprehension is real and externally demonstrated; first-run completion is demonstrated only for the install/verify subset, and the section titled to carry the rest of that claim has a disclosed, unresolved forward-reference gap. That is one half satisfied, not two.

### HumanLayer — D13 = 2 (comparator only, sourced from published copy — see caveat)

Fetched from [humanlayer.dev](https://humanlayer.dev), 2026-08-30. Above-the-fold tagline: *"The multiplayer control plane for your software factory."* Names its workflow explicitly — QRSPI (Questions, Research, Design, Structure, Plan, Implement) — under a section banner reading *"Do not outsource the thinking,"* with supporting copy: "Ensure alignment at every step and put engineers in the driver's seat for code quality and architecture." Above-fold call to action is a single command: `brew install humanlayer/humanlayer/humanlayer` (plus a one-click download button) — no clone, no prerequisite check, no multi-step sequence. On the stated rubric this reads as both halves satisfied from marketing copy alone: the purpose statement is self-contained, and the first run is a single package-manager command.

**Caveat:** this D13=2 is sourced from the vendor's own landing-page copy, not an independent execution (`brew install` was not run — installing third-party software was out of scope for this workstream). It is directionally solid — a one-line install command is a much lower bar to clear than FRACTAL's multi-step, multi-tool sequence, regardless of who is asserting it — but it does not carry the same execution-verified weight as the FRACTAL score above, which was independently run. D1–D12 are not scored for HumanLayer; it enters this benchmark as the D13 comparator only, not a full re-benchmark.

### Recomputed total (FRACTAL, with D13)

18 (12-dimension total from the 2026-08-28 re-score, rechecked above) + 1 (D13) = **19 / 26 (73%)**. Max moves from 24 to 26 only for a row that carries a D13 score — the frozen 2026-04-14 table's rows (D13 unscored, marked N/A) stay at max 24, per the note under that table.

### Why this isn't a swept board either

D13 = 1 is the reason this column exists: the 15→18 capability gain across three landed workstreams did not, on its own, make the project legible to a stranger — the "First Run" section's forward-reference gap is a comprehensibility defect the prior two scoring passes had no dimension to catch, because no dimension was looking. Closing it is a small, scoped fix (define "the strategist agent" and `/fractal-init` inline, or reorder the sections) — smaller than most of what already shipped this cycle — and it is now a tracked, named gap rather than an invisible one.

---

## What this doc explicitly does NOT do

- Does not prescribe which gaps to close first → see [`harness-upgrade-roadmap.md`](./harness-upgrade-roadmap.md).
- Does not score dimensions the rubric doesn't cover (UX, model cost, IDE integration). Those are intentional omissions — scope is *harness quality*, not product comparison.
- Does not audit closed-source agents (Cursor, Zed's AI, GitHub Copilot Workspace). Those are outside the "harness we can study and adopt from" scope.
