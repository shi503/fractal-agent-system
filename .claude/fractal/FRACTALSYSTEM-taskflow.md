# The FRACTAL Multi-Agent System — TaskFlow

> **Localized for TaskFlow.** Project-specific paths and commands below. Core system descriptions (tiers, evaluation layers, retry policy) are unchanged from the upstream reference: `The FRACTAL Multi-Agent System.md`.

---

## Core Philosophy

The FRACTAL system is built on four core principles:

1. **Hierarchy and Specialization:** The system is organized as a fractal hierarchy of agents, where each level has a specific role and a specialized set of skills. This mirrors the structure of a human software development team.
2. **Deterministic Orchestration:** The flow of work is controlled by a deterministic state machine (`router.py`), not by an LLM. This ensures that the system is predictable and that agents remain focused on assigned tasks.
3. **Hard Context Resets:** Agents do not maintain long-running conversational history. Each agent starts with a clean, well-defined context (the workstream PRD). This prevents context drift.
4. **Tool Trace as Truth:** The evaluation framework is based on actual build/test output and state changes, not on the agent's self-reported narrative.

---

## The Four Tiers

The system operates top-down, starting with the **Strategist** and moving to **Sub-Agents**.

1. **The Strategist (Tier 0):** Captures project-level intent in `STRATEGIST-taskflow.md` — WHY the project exists and WHAT good looks like. Re-engage at major priority shifts and milestone boundaries (M1→M2→M3→M4 transitions).
2. **The Architect (Tier 1):** The central orchestrator. Creates the BLUEPRINT, authors workstream PRDs, evaluates HANDOFFs (Layers 1–2), and manages escalations. Never writes implementation code.
3. **The Feature Leads (Tier 2):** Each Feature Lead owns one workstream. It reads the PRD, implements all changes in the file manifest, runs the build gate, and generates a `HANDOFF.md` on completion.
4. **The Sub-Agents (Tier 3):** Execute single atomic tasks delegated by Feature Leads. One task, one file manifest, terminates on completion.

---

## 4-Layer Evaluation Pipeline

Every workstream goes through up to 4 evaluation layers:

| Layer | Owner | Blocks HANDOFF? | What It Checks |
|-------|-------|-----------------|----------------|
| Layer 1 — Deterministic | Architect | Yes | Build, lint, typecheck, security audit, diff scope |
| Layer 2 — LLM Judgment | Architect | Yes | Intent alignment, architecture idioms, security/compliance, pattern consistency |
| Layer 3 — Qualitative Persona | Strategist/User | No (informs backlog) | Would real users trust this? Workflow fit, UX, domain accuracy |
| Layer 4 — Strategic Benchmark | Strategist/User | No (informs roadmap) | Are we building the right thing? Competitive positioning vs. Section 0 benchmarks |

**2-Attempt Retry Policy:** If a layer fails twice, escalate to the next tier up — do not loop indefinitely.

---

## Getting Started — TaskFlow

```bash
# Router location
python3 .claude/fractal/router.py --help

# Initialize a new epic (after Architect generates BLUEPRINT)
python3 .claude/fractal/router.py --blueprint .claude/fractal/BLUEPRINT-{EpicName}.yaml init

# Check what's ready to execute next
python3 .claude/fractal/router.py next

# Check overall epic status
python3 .claude/fractal/router.py status

# Mark a workstream complete (Feature Lead runs this after HANDOFF)
python3 .claude/fractal/router.py update {WorkstreamName} COMPLETE

# Check a PULSE heartbeat for escalation
python3 .claude/fractal/router.py pulse .claude/fractal/workstreams/{workstream}/PULSE.md
```

**CI gate (must pass before any HANDOFF):**
```bash
npm run build && npx tsc --noEmit && npm run lint && npm run format:check && npm run test:run
```

**Typical session flow:**
1. **Strategist interview** (once per project, or at major pivots): `you are @.claude/agents/strategist.md let's run the interview`
2. **Plan an epic**: `Use the architect to plan [epic]. Read STRATEGIST-taskflow.md first.`
3. **Bootstrap**: `/fractal-init BLUEPRINT-{EpicName}.yaml`
4. **Execute workstreams**: `Use the feature-lead agent to execute workstream: .claude/fractal/workstreams/{name}.md`
5. **Check progress**: `python3 .claude/fractal/router.py status`

---

## Directory Structure — TaskFlow

```
.claude/
├── CLAUDE.md                        # Always-on context: TaskFlow stack, conventions, forbidden patterns
├── agents/
│   ├── architect.md                 # Architect — Opus; reads STRATEGIST-taskflow.md before every epic
│   ├── feature-lead.md              # Feature Lead — Sonnet; owns one workstream end-to-end
│   ├── sub-agent.md                 # Sub-Agent — Sonnet; single atomic task, terminates on completion
│   └── strategist.md                # Strategist — Opus; interview-only, no code generation
├── skills/
│   ├── fractal-init/SKILL.md        # Bootstrap FRACTAL epic session
│   ├── pulse/SKILL.md               # Feature Lead heartbeat + escalation check
│   ├── handoff/SKILL.md             # Build gate + HANDOFF.md + router COMPLETE
│   ├── gap-analysis/SKILL.md        # Milestone boundary gap analysis
│   ├── commit-summarize/SKILL.md    # Phase/epic commit + optional PR creation
│   └── quality-pass/SKILL.md        # AI slop cleanup before handoff
└── fractal/
    ├── router.py                    # Deterministic state machine
    ├── STRATEGIST-taskflow.md       # ← Seed of Intent — READ BEFORE EVERY EPIC
    ├── FRACTALSYSTEM-taskflow.md    # This file — localized FRACTAL system reference
    ├── BLUEPRINT-{Epic}.yaml        # One per epic (committed to git)
    ├── .state.json                  # Runtime state — GITIGNORE this
    ├── ISSUES.md                    # Framework-level issue log; triage before each BLUEPRINT phase
    ├── EVAL_TEMPLATES/
    │   ├── deterministic-eval.md    # Layer 1 (required) — build/lint/tsc/security
    │   ├── llm-judgment-eval.md     # Layer 2 (required) — intent alignment, architecture
    │   ├── qualitative-persona-eval.md  # Layer 3 (optional) — Strategist-owned
    │   └── strategic-benchmark-eval.md  # Layer 4 (optional) — vs. Section 0 benchmarks
    ├── intake/                      # Strategist reference material (gitignored)
    │   ├── platform-strategy.md
    │   ├── frontend-dev-guide.md
    │   ├── soc2-compliance.md
    │   └── testing-patterns.md
    └── workstreams/                 # One PRD per workstream, authored by the Architect
```

---

## A Note on Determinism

While orchestration is deterministic, the work performed by agents is not. The FRACTAL system manages non-determinism — not eliminates it. The deterministic routing layer ensures agents work on the right tasks at the right time, and their work is evaluated against consistent criteria. The 2-attempt retry policy caps runaway loops.

---

## Key Project References

| Document | Purpose |
|----------|---------|
| `.claude/fractal/STRATEGIST-taskflow.md` | Project mandate, principles, failure modes, milestone roadmap, autonomy level |
| `.claude/CLAUDE.md` | Tech stack, coding conventions, forbidden patterns, component decision trees |
| `.claude/fractal/intake/platform-strategy.md` | Phase roadmap, competitive context, architecture patterns |
| `.claude/fractal/intake/soc2-compliance.md` | Healthcare/SOC2 guardrails — apply to all workstreams touching data or auth |
| `.claude/fractal/intake/frontend-dev-guide.md` | RSC patterns, Server Actions, shadcn/ui, component anatomy |
| `.claude/fractal/intake/testing-patterns.md` | Vitest, RTL, Playwright patterns |
