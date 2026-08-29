# FRACTAL Setup Guide — Claude Code

This guide walks through integrating FRACTAL into a Claude Code project from scratch. It documents the concrete setup steps, gotchas encountered, and conventions established from production use.

**Time to set up:** ~10 minutes with the marketplace path, ~30 minutes manual
**Prerequisites:** Claude Code CLI, Python 3, `pyyaml`

---

## Option A: Install via the plugin marketplace (fastest, recommended)

The four tier agents and every operational skill ship as Claude Code plugins — you no longer copy files into your project to get them.

```bash
# From a checkout of this repo (or point at wherever you cloned it):
```
```
/plugin marketplace add .
/plugin install fractal-core@fractal-marketplace
```

Add the others as your role needs them: `fractal-tools` (general dev helpers, every repo),
`fractal-planning` (Architect/Strategist work), `fractal-wiki` (repos with a markdown wiki
substrate), `fractal-runner` (the scheduled runner), `fractal-pr-review` (active PR flow).

Plugin install gives you the agents and skills. It does **not** give your project a router or
a state directory — those are project-side artifacts, not plugin content, because
`router.py` is the deterministic piece FRACTAL's design deliberately keeps out of the LLM's
hands. Wire those up:

1. **Copy the router into your project:**
   ```bash
   mkdir -p .claude/fractal/workstreams
   cp path/to/fractal-agent-system/ROUTING_LOGIC/router.py .claude/fractal/router.py
   ```
2. **Add `.gitignore` entries** — see §4 below.
3. **Write your first BLUEPRINT and workstream PRDs** — see §7–8 below; both sections apply
   identically whether you installed via the marketplace or built everything by hand.

Then skip to §9 (Initialize and Run). The rest of this guide (§1–§11) is the manual path —
useful if your Claude Code host doesn't support plugins, or you want to vendor the agent and
skill content directly instead of installing it.

---

## Option B: Manual setup (no plugin support)

---

## 1. Verify Prerequisites

```bash
# Python and PyYAML (router.py dependency)
python3 --version        # 3.8+
python3 -c "import yaml; print('pyyaml ok')"

# If pyyaml is missing:
pip install pyyaml
```

---

## 2. Create the Directory Structure

```bash
mkdir -p .claude/fractal/workstreams
mkdir -p .claude/agents
mkdir -p .claude/skills/fractal-init
mkdir -p .claude/skills/pulse
mkdir -p .claude/skills/handoff
```

---

## 3. Copy and Configure router.py

```bash
cp fractal-agent-system/ROUTING_LOGIC/router.py .claude/fractal/router.py
```

Open `.claude/fractal/router.py` and update the two path constants at the top:

```python
# Update these for each epic:
BLUEPRINT_PATH = os.path.join(os.path.dirname(__file__), "BLUEPRINT-MyEpic.yaml")
STATE_PATH     = os.path.join(os.path.dirname(__file__), ".state.json")
```

The router handles two BLUEPRINT formats:
- **Pure `.yaml`/`.yml` files** — read directly (recommended)
- **`.md` files** — extracts the fenced ` ```yaml ` block
- Both a top-level **phased** list and a flat single-mapping shape are accepted — `_normalize_blueprint()` coerces either into one canonical form before `init`/`next`/`update` run. See `fixtures/taskflow/blueprints/` for one worked example of each shape.

---

## 4. Add .gitignore Entries

Add to your project's `.gitignore`:

```gitignore
# FRACTAL runtime artifacts
.claude/fractal/.state.json
.claude/fractal/workstreams/*/PULSE.md
.claude/fractal/workstreams/*/HANDOFF.md
```

The `router.py`, `BLUEPRINT-*.yaml`, and workstream PRD `.md` files **are** committed. The state, pulse logs, and handoff reports are runtime artifacts that should not be committed.

---

## 5. Create Agent Definitions

Copy the three agent files directly from this repo's `fractal-core` plugin source rather than authoring them from scratch — they carry the reading-discipline contract (word caps, verification-before-acting, tier discipline) already dialed in:

```bash
cp fractal-agent-system/.claude/plugins/fractal-core/agents/architect.md    .claude/agents/architect.md
cp fractal-agent-system/.claude/plugins/fractal-core/agents/feature-lead.md .claude/agents/feature-lead.md
cp fractal-agent-system/.claude/plugins/fractal-core/agents/sub-agent.md    .claude/agents/sub-agent.md
cp fractal-agent-system/.claude/plugins/fractal-core/agents/strategist.md  .claude/agents/strategist.md
```

Then customize each for your project:

| File | What to Change |
|------|-----------------|
| `architect.md` | Project name, tech stack, design principles, technical standards |
| `feature-lead.md` | Project-specific code standards (the base standards work for most projects) |
| `sub-agent.md` | Usually no changes needed |
| `strategist.md` | Usually no changes needed — it interviews you |

These integrate with Claude Code's native agent system (invocable via the `Agent` tool with
`subagent_type`, or by name in natural language — "Use the architect agent to…").

---

## 6. Create Skills

Copy the operational skills the same way, from `fractal-core`'s `skills/` directory:

```bash
for s in fractal-init pulse handoff gap-analysis quality-pass commit-summarize claude-md-audit fractal-maintenance; do
  mkdir -p ".claude/skills/${s}"
  cp "fractal-agent-system/.claude/plugins/fractal-core/skills/${s}/SKILL.md" ".claude/skills/${s}/SKILL.md"
done
```

Each `SKILL.md` carries `disable-model-invocation: true` — its instructions inject into the
*current* session for the active model to execute; it is invoked explicitly (`/fractal-init`,
`/pulse`, `/handoff`, …), never self-fired on a passing mention. Leave that frontmatter key
alone — see `.claude/plugins/fractal-core/skills/fractal-init/SKILL.md` for the worked
reference.

---

## 7. Write Your First BLUEPRINT

Create `.claude/fractal/BLUEPRINT-{EpicName}.yaml`.

**Critical format rule:** The file must be a **top-level YAML list** (the phased shape) or a single flat mapping with a `workstreams:` list (the flat shape) — see `fixtures/taskflow/blueprints/` for one worked example of each. Do NOT wrap a phased list in an extra key; `router.py` iterates it directly and will throw `TypeError: string indices must be integers` if you use an unexpected dict wrapper.

```yaml
# BLUEPRINT-MyEpic.yaml
# Run: python3 .claude/fractal/router.py init

- name: "Phase 1 — Core (parallel)"
  workstreams:
    - feature_lead: FeatureLead-Database
      model: haiku
      prd: .claude/fractal/workstreams/database.md
      dependencies: []

    - feature_lead: FeatureLead-API
      model: sonnet
      prd: .claude/fractal/workstreams/api.md
      dependencies: []

- name: "Phase 2 — UI (depends on Phase 1)"
  workstreams:
    - feature_lead: FeatureLead-UI
      model: sonnet
      prd: .claude/fractal/workstreams/ui.md
      dependencies:
        - FeatureLead-Database
        - FeatureLead-API
```

### Blueprint authoring rules

- `feature_lead` names must be unique across the entire blueprint (used as state keys)
- `dependencies` is a list of `feature_lead` names that must be `COMPLETE` before this workstream starts
- `model` is a hint to the Architect — valid values: `haiku`, `sonnet`, `opus`
- All workstreams with `dependencies: []` will be returned by `router.py next` immediately after init

### Model tier guide (as of 2026-03-04)

> **Note:** Search "Claude Code agent model field" for the latest valid values and any new flags. The table below reflects what is confirmed working as of the date above.

| Value | Maps to | Best for |
|-------|---------|----------|
| `haiku` | Claude Haiku | Pure text transforms, simple SQL, tasks with no framework code |
| `sonnet` | Claude Sonnet | All Feature Lead workstreams, typed frontend frameworks, multi-file reasoning |
| `opus` | Claude Opus | Architect-level orchestration, BLUEPRINT authoring, HANDOFF eval |
| `inherit` | Parent session model | Sub-sessions that should match the caller's tier |

**Context window (200K vs 1M):** This is controlled by your Claude Code plan, **not** by the `model` field in agent frontmatter. If your plan includes 1M context, all `sonnet` and `opus` agents automatically benefit. Check your plan at https://claude.ai/settings or search "Claude Code 1M context plan".

**FRACTAL recommended tiers:**
- `sub-agent` → `sonnet` — upgraded from `haiku`; sonnet handles typed component-framework state primitives correctly
- `feature-lead` → `sonnet` — reads full multi-file manifests, needs reliable framework knowledge
- `architect` → `opus` — strategic decisions, dependency graph reasoning, HANDOFF evaluation

---

## 8. Write Workstream PRDs

Each workstream needs a PRD at `.claude/fractal/workstreams/{kebab-name}.md`. The PRD is the **complete context** a Feature Lead gets — it must be self-contained.

**Required sections:**

```markdown
# Workstream PRD: {FeatureLead-Name}

## Goal
One-sentence description of what this workstream produces.

## Context
What the Feature Lead needs to know about the surrounding system.
Reference existing files, APIs, interfaces — don't assume knowledge.

**Guides:** (reference by path only — do NOT paste content inline)
- `{project-guides}/frontend-dev-guide.md` — Frontend patterns (include for any FE work)
- `{project-guides}/testing-patterns.md` — if this workstream adds spec files
- `{project-guides}/api-status.md` — if this workstream touches backend routes
- Omit any guide not relevant to this workstream — unnecessary references create token bloat

## Acceptance Criteria
- [ ] Specific, verifiable outcome 1
- [ ] Specific, verifiable outcome 2
- [ ] Build/typecheck passes

## File Manifest

**Read:** (files to understand before writing)
- path/to/file.ts

**Write:** (files that may be modified or created)
- path/to/new-file.ts

## Session Protocol
1. Read all files in read manifest before writing
2. Implement following project conventions (link to CLAUDE.md / AGENTS.md)
3. Run build gate
4. Use /pulse if session > 30 min or blocked
5. Use /handoff on completion
```

**What makes a good workstream PRD:**
- File manifest is exhaustive — if a file isn't listed, the Feature Lead won't read it
- Acceptance criteria are binary (pass/fail), not subjective
- Context section explains WHY the change is needed, not just WHAT
- The PRD reads like a spec for a developer who has never seen the codebase

If your project keeps guides worth cross-referencing across many PRDs, consider a committed
guide-reference matrix like `standards/guide-reference-matrix.md` in this repo — a single
table mapping guide path → which write-manifest patterns pull it in, gated by
`tools/check-guide-matrix.sh` so a moved or renamed guide fails the build instead of drifting
silently out of every PRD that cited it.

---

## 9. Initialize and Run

```bash
# Initialize state
python3 .claude/fractal/router.py init

# See what's ready
python3 .claude/fractal/router.py next

# Claim a workstream
python3 .claude/fractal/router.py update FeatureLead-MyWorkstream IN_PROGRESS

# Start a Feature Lead session in Claude Code:
# - Open a new session
# - Reference the workstream PRD: .claude/fractal/workstreams/my-workstream.md
# - Invoke the feature-lead agent

# After HANDOFF accepted:
python3 .claude/fractal/router.py update FeatureLead-MyWorkstream COMPLETE
python3 .claude/fractal/router.py next
```

---

## 10. How to Use FRACTAL Day-to-Day

> **Audience:** You know Claude Code — agents, skills, the Agent tool. This section explains the FRACTAL-specific workflow you follow after setup.

### The Three Interaction Modes

| Mode | When | How |
|------|------|-----|
| **A — Strategist Interview** | New project, or when priorities shift significantly | In main session: use the strategist agent to interview you and update STRATEGIST.md |
| **B — Architect (main session)** | Planning or managing a FRACTAL epic | Main Claude Code window is the Architect. Use `/fractal-init`, `/gap-analysis`, and `/commit-summarize` here. |
| **C — Feature Lead Execution** | Running a workstream | Spawn Feature Lead via Agent tool (background, default) or open a new Claude Code window (interactive, skills available). |

### Mode A — Strategist Interview

Only needed once per project (or when priorities shift significantly). After completing this step, all subsequent sessions operate in **Architect mode (Mode B)**.

#### CRITICAL: The Strategist requires your presence

The Strategist is an intent engineering interview — it cannot run autonomously. You must be in the conversation to answer its questions.

**Correct invocation (you are present):**
```
Use the strategist agent to interview me and generate STRATEGIST.md
```

**Wrong invocation (autonomous — will be blocked):**
```
Use the strategist agent to analyze the codebase and generate STRATEGIST.md
```
A Strategist run without user input produces a document reflecting current code state, not intended direction. This defeats the purpose of intent engineering.

#### Pre-flight: Drop reference files first (optional)

Before invoking the Strategist, you can drop reference material into the intake folder:

```bash
mkdir -p .claude/fractal/intake
# Drop reference docs, notes, or links (see your FRACTAL docs for format).
# The Strategist reads everything in this folder at session start.
```

The Strategist produces output such as `STRATEGIST-{project}.md` and optionally a benchmarks file. The Architect reads these before decomposing any epic.

---

### Mode B — Architect (your main session)

Your main Claude Code session plays the Architect role. This is where you:

1. **Plan an epic** — ask Claude to decompose a feature into a BLUEPRINT and workstream PRDs
2. **Bootstrap the epic** — `/fractal-init BLUEPRINT-MyEpic.yaml`
3. **Monitor progress** — `python3 .claude/fractal/router.py status`
4. **Review HANDOFFs** — read `.claude/fractal/workstreams/{name}/HANDOFF.md` after each workstream
5. **Commit phase work** — `/commit-summarize` after all workstreams in a phase complete
6. **Milestone gates** — `/gap-analysis` at milestone boundaries

Skills available in the main session: `/fractal-init`, `/gap-analysis`, `/commit-summarize`

---

### Mode C — Feature Lead Execution

Feature Leads run as **background agents** by default (Agent tool). This is the recommended mode — it enables parallel workstream execution without manual window management.

**Spawn a Feature Lead:**
```
Use the feature-lead agent to execute workstream: .claude/fractal/workstreams/my-workstream.md
```

The Feature Lead agent will:
1. Read the workstream PRD fully
2. Read all files in the read manifest
3. Implement the changes within the write manifest
4. Run the build gate (your project's build/typecheck commands)
5. Write HANDOFF.md to disk (via bash when in background)
6. Update router state to COMPLETE
7. Report next ready workstreams

**After the agent completes**, review its HANDOFF.md and verify the build gate evidence before accepting.

**Alternative: dedicated session per workstream.** Open a new Claude Code window, reference the workstream PRD, and invoke the feature-lead agent. In this mode, `/pulse` and `/handoff` skills work as slash commands.

---

### Understanding Skills vs Bash

FRACTAL skills fall into two categories based on who uses them and where:

| Skill | Used by | Works in background agent? | How |
|-------|---------|---------------------------|-----|
| `/fractal-init` | Architect (main session) | Yes — always interactive | Type it in your main Claude Code window |
| `/gap-analysis` | Architect (main session) | Yes | Type it in your main Claude Code window |
| `/commit-summarize` | Architect (main session) | Yes | Type it in your main Claude Code window |
| `/pulse` | Feature Lead | No — background agents cannot invoke skills | Feature Lead writes PULSE.md + runs router.py directly via bash (see feature-lead.md) |
| `/handoff` | Feature Lead | No | Feature Lead writes HANDOFF.md + runs router.py directly via bash (see feature-lead.md) |

**Why `disable-model-invocation: true` is correct and should NOT be changed:** Operational FRACTAL skills use `disable-model-invocation: true` — the skill's instructions are injected into the *current* session for the active model to execute. This is required because `/pulse` and `/handoff` need to introspect current session state (tasks completed, blockers). Setting this to `false` would spawn a fresh context with no session state — the skill would have nothing to fill in and would break.

---

### Typical Weekly Workflow

```
Starting a new epic:
  1. In main session: plan the epic and generate BLUEPRINT + workstream PRDs
  2. /fractal-init BLUEPRINT-MyEpic.yaml
  3. python3 .claude/fractal/router.py next → spawn Feature Lead agents

Ongoing:
  1. Check router status: python3 .claude/fractal/router.py status
  2. Spawn Feature Lead agents for ready workstreams
  3. Review HANDOFF.md files as they complete

Phase complete:
  1. Review all HANDOFF.md files in the phase
  2. /commit-summarize
  3. python3 .claude/fractal/router.py next → begin next phase

Milestone boundary:
  1. /gap-analysis
  2. Review gap document and adjust priorities
```

---

## 11. Switching Epics

When starting a new epic:
1. Create `BLUEPRINT-{NewEpic}.yaml` in `.claude/fractal/`
2. Update `BLUEPRINT_PATH` in `router.py` to point to the new file (or pass `--blueprint` per-invocation instead — see the router README)
3. Run `python3 .claude/fractal/router.py init` — this overwrites `.state.json`
4. Old workstream PRDs remain as historical reference

To run two epics concurrently, use separate state files:
```python
# In router.py — use a different STATE_PATH per concurrent epic
STATE_PATH = os.path.join(os.path.dirname(__file__), ".state-epic2.json")
```

---

## Lessons from Production Use

These are concrete issues encountered during Claude Code integration:

| Issue | What happened | Fix |
|-------|---------------|-----|
| YAML TypeError | Blueprint wrapped in an unexpected dict; router expects a top-level list or a single flat mapping | Use one of the two accepted shapes — see `fixtures/taskflow/blueprints/` |
| router.py only handled `.md` files | Original source extracted YAML from fenced blocks; pure `.yaml` files caused parse errors | Added `.yaml`/`.yml` detection branch in `load_blueprint()` |
| No model shown in `next` output | Original `router.py next` didn't display the `model` field | Added model display to `cmd_next()` output |
| `.state.json` not gitignored | State file would conflict across branches | Add to `.gitignore` before first commit |
| PULSE file path convention | `/pulse` skill needs to know the kebab-name → file path mapping | Standardize: `FeatureLead-MyWorkstream` → `workstreams/my-workstream/PULSE.md` |
| Two blueprint shapes in the wild | Some authors wrote a flat single-mapping shape instead of the original phased list | `_normalize_blueprint()` (router `2.0.0`) coerces either shape before `init`/`next`/`update` run; `tools/check-router-identity.sh` keeps the two `router.py` copies in this repo byte-identical |

---

## Full Directory Reference

After setup, your project should look like:

```
.claude/
├── agents/                     # Only if you took the manual path (Option B) — otherwise
│   │                            # the four tier agents come from the fractal-core plugin
│   ├── architect.md
│   ├── feature-lead.md         # Sonnet
│   ├── sub-agent.md            # Sonnet (use Haiku only for pure text/SQL)
│   └── strategist.md
├── skills/                     # Manual path only — plugin install covers this otherwise
│   ├── fractal-init/SKILL.md
│   ├── pulse/SKILL.md
│   └── handoff/SKILL.md
└── fractal/
    ├── router.py               # Deterministic state machine
    ├── BLUEPRINT-{Epic}.yaml   # One per epic (committed)
    ├── .state.json             # Runtime state (gitignored)
    ├── intake/
    │   └── README.md           # Strategist intake folder guide (contents gitignored)
    ├── ISSUES.md               # Framework-issue log template (committed)
    ├── EVAL_TEMPLATES/         # Layer 1–4 eval templates (committed)
    │   ├── deterministic-eval.md
    │   ├── llm-judgment-eval.md
    │   ├── qualitative-persona-eval.md
    │   └── strategic-benchmark-eval.md
    └── workstreams/
        ├── {workstream-1}.md   # Workstream PRDs (committed)
        ├── {workstream-2}.md
        └── {workstream-1}/     # Created at runtime (gitignored)
            ├── PULSE.md
            └── HANDOFF.md
```
