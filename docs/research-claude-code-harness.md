# Research: Claude Code Harness — Patterns & Takeaways from the Public Source Analysis

**Status:** Reference
**Created:** 2026-04-14
**Audience:** FRACTAL Architect, Feature Leads, anyone touching `.claude/agents/*` or `.claude/skills/*`
**Source strategy:** Secondary sources only (high-signal community analyses + Anthropic official docs). No direct ingestion of the disclosed source.

---

## TL;DR

The Claude Code source disclosure of March 2026 did **not** reveal model secrets — it revealed *harness* secrets: the permission pipeline, prompt-assembly logic, subagent forking model, memory consolidation, and the 20-odd conventions that make the agent feel reliable. The recurring meta-insight across every serious analysis is the same: **the harness, not the model, is where most of the quality lives.** Swap in a different frontier model behind the same harness and you keep most of the uplift.

This document is FRACTAL's canonical reference for what the public source analysis taught us, organized so downstream artifacts (`docs/harness-gap-analysis.md`, `docs/claude-md-rubric.md`, `docs/harness-upgrade-roadmap.md`) can link by section.

---

## 1. How the source became public

In late March 2026, Anthropic published `@anthropic-ai/claude-code@2.1.88` to npm with a 59.8 MB JavaScript source-map (`.map`) file that was intended for internal debugging. The source map let the community reverse-engineer ~500K lines of TypeScript within hours. The discovery was broadcast on X by Chaofan Shou ([@Fried_rice](https://x.com/), intern at Solayer Labs). Anthropic confirmed the packaging mistake, stated no customer data was involved, and began issuing DMCA takedowns against the most visible mirrors. ([VentureBeat](https://venturebeat.com/technology/claude-codes-source-code-appears-to-have-leaked-heres-what-we-know), [EngineersCodex](https://read.engineerscodex.com/p/diving-into-claude-codes-source-code))

Because the structural findings — not model weights — are what matter, this is effectively a zero-cost audit of a production agent harness. The community has converged on a consistent picture, and that picture is what this document captures.

---

## 2. System-prompt architecture

The stock Claude Code system prompt is **not one prompt**. It is assembled every turn from ~22–30 modular sections, some always included, others conditional on user type, tool availability, or config flags ([dbreunig](https://www.dbreunig.com/2026/04/04/how-claude-code-builds-a-system-prompt.html)).

Sections, in assembly order:

1. Intro (varies with output style)
2. System Rules (always)
3. Doing Tasks (conditional on user type / output style)
4. Executing Actions with Care (always)
5. Using Your Tools (conditional on REPL, Search, Task tools)
6. Tone and Style (varies by user type)
7. Output Efficiency (varies heavily between internal vs. external users)
8. Cache Boundary Marker (conditional)
9. Multiple Session Guidance sections (Ask User, Shell Shortcut, Agent Tool, Skills, Memory, etc.)
10. Environment Info (always; suppressed details in "undercover" mode)
11. Language (conditional)
12. Output Style (if custom)
13. MCP Server Instructions (conditional)
14. Scratchpad Instructions (conditional)
15. Git Status Snapshot (conditional on repo presence)
16. Append System Prompt (conditional on flag)

### Cache boundary

A sentinel marker — `__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__` — separates globally-cacheable content from session-specific content ([Sabrina.dev](https://www.sabrina.dev/p/claude-code-source-leak-analysis), [dbreunig](https://www.dbreunig.com/2026/04/04/how-claude-code-builds-a-system-prompt.html)). Sections above the boundary cache across organizations; sections below (CLAUDE.md, git status, dates, user-specific vars) are session-specific. A parallel convention tags cache-breaking content explicitly as `DANGEROUS_uncachedSystemPromptSection` so engineers modifying the prompt see the token-cost implication ([EngineersCodex](https://read.engineerscodex.com/p/diving-into-claude-codes-source-code)).

**Why it matters for FRACTAL:** Our agent prompts (`.claude/agents/*.md`) have no such discipline — every edit invalidates the whole cache. Opportunity to adopt.

---

## 3. CLAUDE.md conventions

Claude Code auto-loads `CLAUDE.md` from the project root at every session start and reloads it every turn along with git status ([MindStudio](https://www.mindstudio.ai/blog/claude-code-source-code-leak-8-hidden-features)). It attaches as **user content**, not as part of the system-prompt assembly proper — meaning CLAUDE.md instructions are treated structurally the same as user messages, which has two consequences:

- **Positive:** it survives context compression without special handling.
- **Negative:** the compaction summarizer does *not* distinguish instruction origins — file-injected instructions blend with legitimate user commands, a documented attack surface ([Sabrina.dev](https://www.sabrina.dev/p/claude-code-source-leak-analysis)).

Community best-practice — distilled from the public source and from the stock prompt's expectations — is that a high-quality CLAUDE.md contains: project-specific conventions, versioned tech stack, essential commands with a CI gate, project structure, forbidden patterns with reasons, and preferred libraries. The agent is specifically tuned to look for these signals. ([MindStudio](https://www.mindstudio.ai/blog/claude-code-source-code-leak-8-hidden-features), [StemSearch](https://stemsearchgroup.com/the-claude-code-leak-what-it-actually-means-for-you-no-matter-your-level/))

Crucial side effect documented in the source: AI tools default to the "fastest acceptable answer" rather than the "best possible one," so teams explicitly add instructions to CLAUDE.md forbidding the agent from reporting completion until it has successfully run a linter or type-checker ([MindStudio](https://www.mindstudio.ai/blog/claude-code-source-code-leak-8-hidden-features)). This is a harness-level behavior that CLAUDE.md can counteract but must do so *explicitly*.

---

## 4. Tool design

The public tool surface is roughly **19 permission-gated tools** in the core harness ([WaveSpeedAI](https://wavespeed.ai/blog/posts/claude-code-agent-harness-architecture/)), but community counts reach ~40–50 when LSP integration, subagent spawning, and MCP tools are included.

Design principles visible across every analysis:

- **Dedicated structured tools over raw shell:** `Grep`/`Glob`/`Read`/`Edit` instead of `bash grep/find/cat/sed`. Structured results are easier for the model to consume and easier for the harness to sandbox. ([EngineersCodex](https://read.engineerscodex.com/p/diving-into-claude-codes-source-code))
- **LSP integration** for symbol definitions, call hierarchies, and reference lookups — higher-level abstractions than file reads.
- **Uniform tool contract:** identity, execution, validation, permissions, and presentation — with behavioral properties like `isConcurrencySafe` and `isReadOnly` declared on every tool ([Ken Huang](https://kenhuangus.substack.com/p/the-claude-code-leak-10-agentic-ai)).
- **Tool output caps:** default MCP tool output = 25,000 tokens; warning at 10,000; servers may annotate for up to 500,000 characters which get persisted to disk rather than held in context ([WaveSpeedAI](https://wavespeed.ai/blog/posts/claude-code-agent-harness-architecture/)).

### Bash security layer

A **9,707-line bash security system** uses tree-sitter WASM parsing and 22 security validators. A documented vulnerability: two parsers disagree on carriage-return tokenization, and the deprecated `splitCommand_DEPRECATED` still flows through parts of `bashPermissions.ts` and `pathValidation.ts` ([Sabrina.dev](https://www.sabrina.dev/p/claude-code-source-leak-analysis)). This is useful context not because we'd replicate the bug but because it shows how much investment went into Bash guardrails — well beyond "blocklist of dangerous commands."

---

## 5. Permission model

Permissions run as a **separate code path** from the model — jailbreaks can't bypass them because the check isn't a prompt, it's a pipeline ([WaveSpeedAI](https://wavespeed.ai/blog/posts/claude-code-agent-harness-architecture/)).

Three tiers (simplified from six internal modes — `default`, `auto`, `plan`, `acceptEdits`, `bubble`, etc.):

- **Tier 1 — Auto-approved:** read-only or inherently safe (file reads, text search, code navigation).
- **Tier 2 — Prompt-for-confirmation:** state-modifying. In **auto mode, a background classifier running on Sonnet 4.6 evaluates whether these can proceed without asking the user** — the "critic" / side-query pattern ([EngineersCodex](https://read.engineerscodex.com/p/diving-into-claude-codes-source-code)).
- **Tier 3 — Block/explicit approval:** high-risk ops outside working directories, suspected exfiltration.

**"Deny always wins"** is the evaluation rule: allow/deny/ask lists + tool-specific checks + automated classifiers + user approval fallback, all gated by a central `canUseTool` function ([Ken Huang](https://kenhuangus.substack.com/p/the-claude-code-leak-10-agentic-ai)).

---

## 6. Subagent models

Claude Code supports three subagent patterns ([EngineersCodex](https://read.engineerscodex.com/p/diving-into-claude-codes-source-code)):

- **Fork** — byte-identical inheritance of parent context. Because prompt caching is content-addressed, **forking N subagents costs almost the same as forking one** for the shared prefix. This is the economic reason parallel exploration is cheap.
- **Teammate** — a fresh subagent with its own tool permissions and system prompt (analogous to FRACTAL's Feature Lead invocation).
- **Worktree** — subagent operating on an isolated git worktree, letting it write without stepping on the parent.

Two unreleased/internal daemon modes are visible in the source and worth flagging even though they're not in the public build:

- **KAIROS** — 190 references across 61 files; 5-minute cron cycles, GitHub webhook triggers, exclusive tool access. A "heartbeat" asking *"anything worth doing right now?"* Append-only logs prevent history erasure; sessions persist across restarts ([Sabrina.dev](https://www.sabrina.dev/p/claude-code-source-leak-analysis), [EngineersCodex](https://read.engineerscodex.com/p/diving-into-claude-codes-source-code)).
- **ULTRAPLAN** — offloads planning to remote Opus sessions for up to 30 minutes, polling every 3 seconds via "teleport sentinels" ([Sabrina.dev](https://www.sabrina.dev/p/claude-code-source-leak-analysis)).

**⚠️ Unverified:** the triple-gating numbers for memory consolidation (24h elapsed / 5+ sessions / lock acquired) come from a single source and should be treated as indicative, not authoritative.

---

## 7. Memory & context management

Claude Code treats the context window as a scarce, engineered resource with at least five compaction strategies and an `autoDream` idle-consolidation process. Documented patterns:

- **Three-layer memory index** ([EngineersCodex](https://read.engineerscodex.com/p/diving-into-claude-codes-source-code)):
  1. **Pointers always loaded** (cheap — file names + one-line descriptions).
  2. **Topic files fetched on demand** when relevant.
  3. **Transcripts greppable but never loaded wholesale.**
- **Write discipline:** write to topic files first, update indexes second, never dump content into indexes. Skip facts that can be re-derived from the codebase.
- **Memory-as-hint:** the agent is explicitly told to **verify** historical facts before acting on them — a recalled memory is context, not truth.
- **autoDream:** idle-time consolidation runs in a forked subagent with limited tool access, preventing corruption of main context ([EngineersCodex](https://read.engineerscodex.com/p/diving-into-claude-codes-source-code)).
- **Compaction circuit-breaker:** `MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES = 3`. A March 10 internal BigQuery note revealed 1,279 sessions had experienced 50+ consecutive compaction failures — wasting ~250K API calls/day globally — before this constant was added ([Sabrina.dev](https://www.sabrina.dev/p/claude-code-source-leak-analysis)). A cautionary tale about silent retry loops.

Context compaction **does not tag instruction origin** — so CLAUDE.md-level rules and user instructions collapse into the same blob after summarization ([Sabrina.dev](https://www.sabrina.dev/p/claude-code-source-leak-analysis)).

---

## 8. Hooks & extensibility

The harness exposes **25 event hooks** that intercept every execution stage — tool call pre/post, context changes, subagent spawn, compaction, etc. This is how the community builds harness extensions (Superpowers, gstack) without patching Claude Code itself. ([EngineersCodex](https://read.engineerscodex.com/p/diving-into-claude-codes-source-code))

For MCP specifically: three transport modes (HTTP, stdio, SSE), lazy-loaded tool schemas (only names at session start), and a practical cap of **5–6 active MCP servers** before subprocess overhead degrades startup. ([WaveSpeedAI](https://wavespeed.ai/blog/posts/claude-code-agent-harness-architecture/))

---

## 9. Plan mode / read-only exploration

Plan mode is a first-class harness state, not just a convention. When active, write tools are disabled at the permission layer, and the agent is instructed to conduct structured exploration (with the `Explore` subagent) before emitting a plan file. Execution only resumes after an explicit `ExitPlanMode` call. ([WaveSpeedAI](https://wavespeed.ai/blog/posts/claude-code-agent-harness-architecture/), [Ken Huang](https://kenhuangus.substack.com/p/the-claude-code-leak-10-agentic-ai))

Key design choice: plan mode is enforced by permission pipeline, **not** by asking the model nicely. This is the right layer for reversibility guarantees.

---

## 10. Output discipline

Internal A/B testing inside Anthropic showed a **~1.2% output-token reduction** by replacing generic "be concise" directives with explicit word-count caps:

> keep text between tool calls to ≤25 words. Keep final responses to ≤100 words.

This was significant enough at scale to be shipped and surfaced in the source analysis ([EngineersCodex](https://read.engineerscodex.com/p/diving-into-claude-codes-source-code)). The lesson: **numeric caps beat adjectives** when telling an LLM how to write.

The stock prompt also explicitly forbids: opening affirmations ("Great question!"), trailing summaries of what the agent just did, and apologies unless the user requests a retry ([EngineersCodex](https://read.engineerscodex.com/p/diving-into-claude-codes-source-code)).

---

## 11. "Magic Docs" — agent-maintained documentation

Files with a `MAGIC DOC` header are treated as self-updating — idle subagents run against them, scoped to a single file, updating contents so they don't drift. Scoping to one file is the trick that prevents "auto-maintain my docs" from silently rewriting unrelated code. ([EngineersCodex](https://read.engineerscodex.com/p/diving-into-claude-codes-source-code))

**Why it matters for FRACTAL:** PRDs and HANDOFF.mds drift the moment the underlying code changes. A FRACTAL `MAGIC DOC` convention could be valuable for living artifacts.

---

## 12. Security & integrity patterns

Worth noting even though they're outside most project scopes:

- **Anti-distillation poisoning:** fake tool definitions injected into prompts at data-collection time (not inference time). Models trained on poisoned prompts become less reliable — a deterrent against dataset scraping.
- **Zig-level DRM:** cryptographic request attestation lives in compiled Zig code (Bun's HTTP stack), not JavaScript. Resists runtime patching better than application-layer checks.
- **Undercover mode:** strips internal codenames from external builds. No force-OFF. Automatic, irrevocable suppression as a disclosure-prevention pattern. ([EngineersCodex](https://read.engineerscodex.com/p/diving-into-claude-codes-source-code), [Sabrina.dev](https://www.sabrina.dev/p/claude-code-source-leak-analysis))
- **Verification Agent hard rules:** embedded rationalizations explicitly to resist — *"reading is not verification. Run it."*, *"the implementer is an LLM. Verify independently."*, *"probably is not verified. Run it."* ([Sabrina.dev](https://www.sabrina.dev/p/claude-code-source-leak-analysis))

The Verification Agent lines are directly adoptable as CLAUDE.md clauses in any project that has agents self-reporting completion.

---

## 13. Meta-insight: the harness is the product

Every serious analysis converges on the same conclusion ([EngineersCodex](https://read.engineerscodex.com/p/diving-into-claude-codes-source-code), [WaveSpeedAI](https://wavespeed.ai/blog/posts/claude-code-agent-harness-architecture/), [Ken Huang](https://kenhuangus.substack.com/p/the-claude-code-leak-10-agentic-ai), [Matthew Berman](https://www.youtube.com/watch?v=dYG8JxtSgmM)):

> The model generates text. The harness decides what that text can touch. Most of the quality signal developers associate with "Claude Code" is actually the harness.

Concrete implication: a well-designed harness can take a second-tier model and extract first-tier productivity. Conversely, a great model behind a weak harness performs badly. For FRACTAL — which *is* a harness — this is the most important finding from the public source analysis.

---

## 14. Top 20 actionable takeaways (for gap analysis)

1. Split agent prompts at a stable/dynamic cache boundary; mark cache-breaking sections explicitly.
2. Auto-load an always-on context anchor (CLAUDE.md pattern) into every agent invocation.
3. Prefer structured tools (Grep/Glob/Read/Edit) over raw shell for both the main agent and subagents.
4. Declare `isReadOnly` / `isConcurrencySafe` behavioral properties on every tool.
5. Permission check is a separate code path, not a prompt — "deny always wins."
6. Use a side-query classifier ("is this safe?") for borderline tool calls.
7. Ship plan mode as a permission state, not a behavioral suggestion.
8. Provide three subagent flavors: fork (shared context), teammate (fresh), worktree (isolated).
9. Lean on prompt-caching economics: forking 5 subagents ~= forking 1.
10. Three-layer memory index: pointers always, topics on demand, transcripts greppable.
11. Memory-as-hint — verify recalled facts before acting on them.
12. Add circuit-breakers to any retry loop (`MAX_CONSECUTIVE_*`).
13. Idle-time consolidation runs in a forked subagent with limited tools (`autoDream` pattern).
14. Expose event hooks at every execution stage; don't require forking the harness to extend.
15. Use explicit numeric output caps (≤25 / ≤100 words), not adjectives.
16. Forbid opening affirmations and trailing summaries in agent prompts.
17. `MAGIC DOC` convention for auto-maintained, single-file-scoped documentation.
18. Verification Agent hard rules: *"reading is not verification. Run it."*
19. Cap tool output (25K tokens default); overflow to disk, not context.
20. Track MCP server count (practical cap ~5–6); lazy-load schemas.

---

## Sources

- [EngineersCodex — "Diving into Claude Code's Source Code Leak"](https://read.engineerscodex.com/p/diving-into-claude-codes-source-code) — primary anchor, 20 concrete technical takeaways
- [Matthew Berman — YouTube breakdown (`dYG8JxtSgmM`)](https://www.youtube.com/watch?v=dYG8JxtSgmM) — user-highlighted video analysis
- [Ken Huang — "The Claude Code Leak: 10 Agentic AI Harness Patterns"](https://kenhuangus.substack.com/p/the-claude-code-leak-10-agentic-ai) — harness paradigm, tool contract, permission pipeline
- [WaveSpeedAI — "Claude Code Agent Harness: Architecture Breakdown"](https://wavespeed.ai/blog/posts/claude-code-agent-harness-architecture/) — permission tiers, MCP limits, tool counts
- [Sabrina.dev — "Comprehensive Analysis of Claude Code Source Leak"](https://www.sabrina.dev/p/claude-code-source-leak-analysis) — KAIROS, ULTRAPLAN, autoDream, compaction circuit-breaker
- [Drew Breunig — "How Claude Code Builds a System Prompt"](https://www.dbreunig.com/2026/04/04/how-claude-code-builds-a-system-prompt.html) — prompt section inventory, cache-boundary sentinel
- [VentureBeat — "Claude Code's source code appears to have leaked"](https://venturebeat.com/technology/claude-codes-source-code-appears-to-have-leaked-heres-what-we-know) — incident timeline
- [MindStudio — "8 Hidden Features You Can Use Right Now"](https://www.mindstudio.ai/blog/claude-code-source-code-leak-8-hidden-features) — CLAUDE.md behavior, loop-escape patterns
- [Blake Crosley — "What the Claude Code Source Leak Reveals"](https://blakecrosley.com/blog/claude-code-source-leak) — corroborating analysis
- [StemSearch — "The Claude Code Leak: What It Actually Means for You"](https://stemsearchgroup.com/the-claude-code-leak-what-it-actually-means-for-you-no-matter-your-level/) — end-user implications
- [Piebald-AI — claude-code-system-prompts (reference index only)](https://github.com/Piebald-AI/claude-code-system-prompts)
- [asgeirtj — system_prompts_leaks (reference index only)](https://github.com/asgeirtj/system_prompts_leaks)
