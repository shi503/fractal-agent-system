# FRACTAL Setup Guide — Claude Code

This guide walks through integrating FRACTAL into a Claude Code project from scratch. It documents the concrete setup steps, gotchas encountered, and conventions established from production use.

**Time to set up:** ~30 minutes
**Prerequisites:** Claude Code CLI, Python 3, `pyyaml`

---

## 1. Verify Prerequisites

```bash
# Python and PyYAML (router.py dependency)
python3 --version        # 3.8+
python3 -c "import yaml; print('pyyaml ok')"

# If pyyaml is missing:
pip install pyyaml
# or: pip3 install pyyaml
```

---

## 2. Create the Directory Structure

```bash
mkdir -p .claude/FRACTAL/workstreams
mkdir -p .claude/agents
mkdir -p .claude/skills/fractal-init
mkdir -p .claude/skills/pulse
mkdir -p .claude/skills/handoff
```

---

## 3. Copy and Configure router.py

```bash
cp .FRACTAL_AGENTS_SYSTEM/ROUTING_LOGIC/router.py .claude/FRACTAL/router.py
```

Open `.claude/FRACTAL/router.py` and update the two path constants at the top:

```python
# Update these for each epic:
BLUEPRINT_PATH = os.path.join(os.path.dirname(__file__), "BLUEPRINT-MyEpic.yaml")
STATE_PATH     = os.path.join(os.path.dirname(__file__), ".state.json")
```

The router handles two BLUEPRINT formats:
- **Pure `.yaml`/`.yml` files** — read directly (recommended)
- **`.md` files** — extracts the fenced ` ```yaml ` block

---

## 4. Add .gitignore Entries

Add to your project's `.gitignore`:

```gitignore
# FRACTAL runtime artifacts
.claude/FRACTAL/.state.json
.claude/FRACTAL/workstreams/*/PULSE.md
.claude/FRACTAL/workstreams/*/HANDOFF.md
```

The `router.py`, `BLUEPRINT-*.yaml`, and workstream PRD `.md` files **are** committed. The state, pulse logs, and handoff reports are runtime artifacts that should not be committed.

---

## 5. Create Agent Definitions

Create three agent files in `.claude/agents/`. These integrate with Claude Code's native agent system (invocable via the `Agent` tool with `subagent_type`).

### Architect Agent

Your primary Claude Code session or existing CTO/planner agent. Add an **Architect Mode** section to it:

```markdown
## Architect Mode (FRACTAL Epics)

When working on a large epic, shift into Architect mode. Rules:
- Never write code — only generate BLUEPRINTs, write workstream PRDs, evaluate HANDOFFs
- BLUEPRINT workstreams must have explicit file manifests — ambiguous PRDs produce ambiguous work
- Dependency edges are the core value — be precise about what can run in parallel
- HANDOFF evaluation is an approval gate — verify build passes and acceptance criteria are met

### Generating a BLUEPRINT

1. Decompose the epic into workstreams (3–8 is typical)
2. Assign model tier: `sonnet` for multi-file/complex, `haiku` for single-file/mechanical
3. Map dependency edges — most workstreams should have `dependencies: []`
4. Write BLUEPRINT to `.claude/FRACTAL/BLUEPRINT-{EpicName}.yaml`
5. Write one workstream PRD per workstream to `.claude/FRACTAL/workstreams/`
6. Tell user to run: `python3 .claude/FRACTAL/router.py init`
```

### Feature Lead Agent

`.claude/agents/feature-lead.md`:

```markdown
---
name: feature-lead
description: "Execute a single FRACTAL workstream end-to-end. Read the workstream PRD, implement all required changes, emit PULSE heartbeats, generate HANDOFF.md on completion."
# Valid model values: haiku | sonnet | opus | inherit  (as of 2026-03-04)
# Search "Claude Code agent model field" for the latest valid values.
# Context window size (200K vs 1M) is set by your plan, not this field.
model: sonnet
color: green
---

You are a Feature Lead. You own one workstream. You do not make architectural decisions.

## Session Protocol
1. Read the workstream PRD fully before writing anything
2. Read all files in the read manifest before modifying any write-manifest file
3. Stay within the file manifest — do not touch files not listed
4. Run the build gate before HANDOFF:
   [your project's build/typecheck commands]
5. Use /pulse [name] if session runs > 30 minutes or you hit a blocker
6. Use /handoff [name] on completion

## Delegation to Sub-Agents
Spawn up to 2 Sub-Agents for tasks that are:
- Single file, mechanical (no reasoning required)
- Fully specified (you know exactly what to write)
Provide: single-sentence task, explicit file manifest, 1–3 acceptance criteria.
```

### Sub-Agent

`.claude/agents/sub-agent.md`:

```markdown
---
name: sub-agent
description: "Execute a single atomic task. One task, explicit file manifest, terminates on completion. Use for mechanical single-file changes delegated from a Feature Lead."
# Valid model values: haiku | sonnet | opus | inherit  (as of 2026-03-04)
# sonnet: recommended for typed Angular/TypeScript tasks; reduces hallucination
# haiku:  use only for pure text transforms or simple SQL with no framework code
model: sonnet
color: yellow
---

You are a Sub-Agent executing a single atomic task.

## Rules
- One task only — if you discover additional scope, stop and report it
- Read only your assigned files, write only your assigned files
- Follow exactly what exists in the surrounding code — no new patterns
- Report: what you changed, file:line references, whether acceptance criteria passed
```

---

## 6. Create Skills

Three skills that inject structured instructions into active Claude Code sessions.

### `/fractal-init`

`.claude/skills/fractal-init/SKILL.md`:

```markdown
---
name: fractal-init
description: "Bootstrap a FRACTAL epic session — verify router.py, initialize state, display ready workstreams"
argument-hint: "[blueprint filename]"
disable-model-invocation: true
---

Bootstrapping FRACTAL for the epic in $ARGUMENTS.

Steps:
1. Verify: ls .claude/FRACTAL/router.py && ls .claude/FRACTAL/$ARGUMENTS
2. Run: python3 .claude/FRACTAL/router.py init
3. Run: python3 .claude/FRACTAL/router.py next
4. Print session brief: epic name, workstream count, which are parallel, recommended first step
5. Remind: run `router.py update <name> IN_PROGRESS` before starting each workstream
```

### `/pulse`

`.claude/skills/pulse/SKILL.md`:

```markdown
---
name: pulse
description: "Emit a structured heartbeat and check for escalation"
argument-hint: "[FeatureLead name]"
disable-model-invocation: true
---

Emitting heartbeat for $ARGUMENTS.

Steps:
1. Collect: tasks_completed (N/total), blockers, escalation_needed (bool)
2. Determine pulse path: .claude/FRACTAL/workstreams/{kebab-name}/PULSE.md
3. Append JSON block:
   { "timestamp": "ISO-8601", "status": "IN_PROGRESS",
     "tasks_completed": "N/total", "blockers": "...", "escalation_needed": false }
4. Run: python3 .claude/FRACTAL/router.py pulse <path>
5. If HEARTBEAT_ALERT: surface to user, stop work
6. If HEARTBEAT_OK: one-line summary, continue
```

### `/handoff`

`.claude/skills/handoff/SKILL.md`:

```markdown
---
name: handoff
description: "Build gate + generate HANDOFF.md + mark workstream COMPLETE"
argument-hint: "[FeatureLead name]"
disable-model-invocation: true
---

Completing workstream $ARGUMENTS.

CRITICAL: Do not proceed if the build gate fails.

Steps:
1. Run build gate: [your project's build/typecheck commands]
   Stop and fix if it fails — do not proceed to Step 2.
2. Write .claude/FRACTAL/workstreams/{kebab-name}/HANDOFF.md:
   - Summary of work completed (specific: file paths, function names)
   - Summary of work NOT completed (honest)
   - Technical debt registered
   - Key decisions and deviations from PRD
   - Deterministic eval results (build: PASS/FAIL)
3. Run: python3 .claude/FRACTAL/router.py update <name> COMPLETE
4. Run: python3 .claude/FRACTAL/router.py next
5. Tell user: "Review HANDOFF.md before accepting."
```

---

## 7. Write Your First BLUEPRINT

Create `.claude/FRACTAL/BLUEPRINT-{EpicName}.yaml`.

**Critical format rule:** The file must be a **top-level YAML list**. Do NOT wrap it in a `phases:` key — `router.py` iterates the list directly and will throw `TypeError: string indices must be integers` if you use a dict wrapper.

```yaml
# BLUEPRINT-MyEpic.yaml
# Run: python3 .claude/FRACTAL/router.py init

- name: "Phase 1 — Core (parallel)"
  workstreams:
    - feature_lead: FeatureLead-Database
      model: haiku
      prd: .claude/FRACTAL/workstreams/database.md
      dependencies: []

    - feature_lead: FeatureLead-API
      model: sonnet
      prd: .claude/FRACTAL/workstreams/api.md
      dependencies: []

- name: "Phase 2 — UI (depends on Phase 1)"
  workstreams:
    - feature_lead: FeatureLead-UI
      model: sonnet
      prd: .claude/FRACTAL/workstreams/ui.md
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
| `sonnet` | Claude Sonnet | All Feature Lead workstreams, Angular/TypeScript, multi-file reasoning |
| `opus` | Claude Opus | Architect-level orchestration, BLUEPRINT authoring, HANDOFF eval |
| `inherit` | Parent session model | Sub-sessions that should match the caller's tier |

**Context window (200K vs 1M):** This is controlled by your Claude Code plan, **not** by the `model` field in agent frontmatter. If your plan includes 1M context, all `sonnet` and `opus` agents automatically benefit. Check your plan at https://claude.ai/settings or search "Claude Code 1M context plan".

**FRACTAL recommended tiers:**
- `sub-agent` → `sonnet` — upgraded from `haiku`; sonnet handles typed Angular 21 signals/computed correctly
- `feature-lead` → `sonnet` — reads full multi-file manifests, needs reliable framework knowledge
- `architect` → `opus` — strategic decisions, dependency graph reasoning, HANDOFF evaluation

---

## 8. Write Workstream PRDs

Each workstream needs a PRD at `.claude/FRACTAL/workstreams/{kebab-name}.md`. The PRD is the **complete context** a Feature Lead gets — it must be self-contained.

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

---

## 9. Initialize and Run

```bash
# Initialize state
python3 .claude/FRACTAL/router.py init

# See what's ready
python3 .claude/FRACTAL/router.py next

# Claim a workstream
python3 .claude/FRACTAL/router.py update FeatureLead-MyWorkstream IN_PROGRESS

# Start a Feature Lead session in Claude Code:
# - Open a new session
# - Reference the workstream PRD: .claude/FRACTAL/workstreams/my-workstream.md
# - Invoke the feature-lead agent

# After HANDOFF accepted:
python3 .claude/FRACTAL/router.py update FeatureLead-MyWorkstream COMPLETE
python3 .claude/FRACTAL/router.py next
```

---

## 10. Switching Epics

When starting a new epic:
1. Create `BLUEPRINT-{NewEpic}.yaml` in `.claude/FRACTAL/`
2. Update `BLUEPRINT_PATH` in `router.py` to point to the new file
3. Run `python3 .claude/FRACTAL/router.py init` — this overwrites `.state.json`
4. Old workstream PRDs remain as historical reference

To run two epics concurrently, use separate state files:
```python
# In router.py — use a different STATE_PATH per concurrent epic
STATE_PATH = os.path.join(os.path.dirname(__file__), ".state-epic2.json")
```

---

## Lessons from Production Pilots

These are concrete issues encountered during Claude Code integration:

| Issue | What happened | Fix |
|-------|---------------|-----|
| YAML TypeError | Blueprint wrapped in `phases:` dict; router expects top-level list | Remove wrapper, start file with `- name:` |
| router.py only handled `.md` files | Original source extracted YAML from fenced blocks; pure `.yaml` files caused parse errors | Added `.yaml`/`.yml` detection branch in `load_blueprint()` |
| No model shown in `next` output | Original `router.py next` didn't display the `model` field | Added model display to `cmd_next()` output |
| `.state.json` not gitignored | State file would conflict across branches | Add to `.gitignore` before first commit |
| PULSE file path convention | `/pulse` skill needs to know the kebab-name → file path mapping | Standardize: `FeatureLead-PreferencesUI` → `workstreams/preferences-ui/PULSE.md` |

---

## Full Directory Reference

After setup, your project should look like:

```
.claude/
├── agents/
│   ├── your-architect.md       # Architect — add FRACTAL Architect Mode section
│   ├── feature-lead.md         # Feature Lead — Sonnet
│   └── sub-agent.md            # Sub-Agent — Sonnet (use Haiku only for pure text/SQL)
├── skills/
│   ├── fractal-init/SKILL.md
│   ├── pulse/SKILL.md
│   └── handoff/SKILL.md
└── FRACTAL/
    ├── router.py               # Deterministic state machine
    ├── BLUEPRINT-{Epic}.yaml   # One per epic (committed)
    ├── .state.json             # Runtime state (gitignored)
    └── workstreams/
        ├── {workstream-1}.md   # Workstream PRDs (committed)
        ├── {workstream-2}.md
        └── {workstream-1}/     # Created at runtime (gitignored)
            ├── PULSE.md
            └── HANDOFF.md
```
