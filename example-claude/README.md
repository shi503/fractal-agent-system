# FRACTAL for Claude Code — Installable Bundle

This folder is a **ready-to-install** FRACTAL setup. Copy it into your project as `.claude` and start using FRACTAL immediately.

---

## Quick Install

```bash
# From your project root:
cp -r path/to/fractal-agent-system/example-claude .claude
```

**That's it.** No file edits required for a first run. The agents, skills, eval templates, and a sample `CLAUDE.md` are pre-filled with a realistic demo project (TaskFlow kanban tracker).

---

## First Run

Open Claude Code in your project and try these prompts:

```
# 1. Run a Strategist interview (once per project):
Use the strategist agent to interview me and generate STRATEGIST-myapp.md

# 2. Plan an epic:
I want to build [your feature]. Use architect mode to create a BLUEPRINT and workstream PRDs.

# 3. Bootstrap the epic:
/fractal-init BLUEPRINT-MyEpic.yaml

# 4. Execute a workstream:
Use the feature-lead agent to execute workstream: .claude/fractal/workstreams/my-workstream.md
```

---

## Customize for Your Project

After the first run, customize these files for your project:

| File | What to Change |
|------|----------------|
| `CLAUDE.md` | Product identity, tech stack, commands, conventions, forbidden patterns |
| `agents/architect.md` | Project name in the preamble, tech stack, design principles, technical standards |
| `agents/feature-lead.md` | Add project-specific code standards (base standards work for most projects) |
| `fractal/EVAL_TEMPLATES/` | Replace build/lint/test commands with your stack's commands |

The **Strategist agent** (`agents/strategist.md`) usually doesn't need customization — it interviews you and adapts.

### Agent Overlay (Optional)

To keep base agent files upgradeable, create `*.local.md` files alongside any agent:

```
.claude/agents/
├── architect.md           # Base (replace on upgrade)
├── architect.local.md     # Your project overrides (persist across upgrades)
```

The `.local.md` content is appended to the base agent's context. Use it for project-specific tech stack, principles, or forbidden patterns.

---

## Project Guides

Your project may have guides for testing patterns, frontend conventions, compliance requirements, or API standards. These guides live in your project (not in `.claude/`) and plug into FRACTAL through the Architect's **Guide Reference Matrix**.

### How It Works

1. **Place guides in your project** — e.g. `.SPECS/guides/`, `docs/guides/`, or wherever your team keeps them.
2. **The Architect references them by path** — When writing workstream PRDs, the Architect uses the Guide Reference Matrix to decide which guides are relevant and includes their paths in the PRD context.
3. **Feature Leads read the referenced guides** — As part of step 2 ("Read all source files"), Feature Leads read any guides referenced in their PRD.

No new mechanism is needed — the Guide Reference Matrix in `agents/architect.md` already supports arbitrary guide paths.

### Common Guide Types

| Guide | Purpose | Referenced When |
|-------|---------|-----------------|
| Testing patterns | Stack-specific test conventions, mocking patterns, coverage targets | Workstreams that include tests |
| Frontend dev guide | Component anatomy, state management patterns, styling conventions | Frontend workstreams |
| SOC2 / compliance | Security guardrails, audit requirements, data handling rules | Regulated projects (all workstreams) |
| API conventions | Endpoint naming, error formats, versioning, auth patterns | Backend / API workstreams |
| Database guide | Migration conventions, naming, indexing, RLS policies | Database / schema workstreams |

### Example Guide Reference Matrix Entry

To add your project's guides, update the Guide Reference Matrix in `agents/architect.md`:

```markdown
| Workstream type | Include in PRD Context |
|-----------------|------------------------|
| Frontend component | `CLAUDE.md`, `.SPECS/guides/frontend-dev-guide.md` |
| Workstream includes tests | `CLAUDE.md`, `.SPECS/guides/testing-patterns.md` |
| Any (regulated project) | `CLAUDE.md`, `.SPECS/guides/soc2-guidance.md` |
```

---

## Prerequisites

- **Python 3.8+** with `pyyaml` (`pip install pyyaml`)
- **Claude Code CLI** with Agent and Skill support

---

## .gitignore Entries

Add to your project's `.gitignore`:

```gitignore
.claude/fractal/.state.json
.claude/fractal/workstreams/*/PULSE.md
.claude/fractal/workstreams/*/HANDOFF.md
.claude/fractal/intake/*
!.claude/fractal/intake/README.md
```

---

## What's Included

| Path | Purpose |
|------|---------|
| `CLAUDE.md` | Sample always-on context doc (TaskFlow demo — customize for your project) |
| `agents/` | Architect, Strategist, Feature Lead, Sub-Agent definitions |
| `skills/` | fractal-init, pulse, handoff, gap-analysis, commit-summarize |
| `fractal/router.py` | Deterministic state machine |
| `fractal/STRATEGIST-example.md` | Sample completed Strategist doc (reference) |
| `fractal/BLUEPRINT-Example.yaml` | Example blueprint — replace with your epic |
| `fractal/workstreams/` | Example workstream PRDs; add one per workstream |
| `fractal/intake/README.md` | Strategist intake folder guide with token budget rules |
| `fractal/ISSUES.md` | Template for logging framework-level issues |
| `fractal/EVAL_TEMPLATES/` | Layer 1–4 eval templates with realistic examples |

---

## Router Commands

```bash
# Initialize state from blueprint
python3 .claude/fractal/router.py init

# Or use --blueprint to avoid editing the constant:
python3 .claude/fractal/router.py --blueprint BLUEPRINT-MyEpic.yaml init

# See ready workstreams
python3 .claude/fractal/router.py next

# Update workstream status
python3 .claude/fractal/router.py update FeatureLead-MyWorkstream COMPLETE

# Full status overview
python3 .claude/fractal/router.py status

# Check pulse for escalation
python3 .claude/fractal/router.py pulse .claude/fractal/workstreams/my-workstream/PULSE.md
```

---

## Day-to-Day Workflow

| Mode | When | How |
|------|------|-----|
| **Strategist Interview** | New project, or priorities shift | `Use the strategist agent to interview me and update STRATEGIST.md` |
| **Architect (main session)** | Planning or managing an epic | `/fractal-init`, `/gap-analysis`, `/commit-summarize` |
| **Feature Lead Execution** | Running a workstream | Spawn via Agent tool (background) or new Claude Code window (interactive) |

### Typical Weekly Workflow

```
Starting a new epic:
  1. Plan the epic → BLUEPRINT + workstream PRDs
  2. /fractal-init BLUEPRINT-MyEpic.yaml
  3. router.py next → spawn Feature Lead agents

Ongoing:
  1. router.py status → check progress
  2. Spawn Feature Lead agents for ready workstreams
  3. Review HANDOFF.md files as they complete

Phase complete:
  1. Review all HANDOFF.md files
  2. /commit-summarize
  3. router.py next → begin next phase

Milestone boundary:
  1. /gap-analysis
  2. Review gap document and adjust priorities
```

---

## Full Setup Reference

For detailed setup instructions (manual setup, skills vs bash, model tiers, production lessons), see:

- [SETUP-CLAUDE-CODE.md](../SETUP-CLAUDE-CODE.md) — Full step-by-step Claude Code setup
- [BEST-PRACTICES.md](../BEST-PRACTICES.md) — Lessons from production use
