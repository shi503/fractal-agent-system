# Installable FRACTAL setup for Claude Code

This folder is a **ready-to-install** FRACTAL structure. Copy it into your project so adopters see exactly what a configured FRACTAL setup looks like.

## Quick install

From your project root (where you want `.claude` to live):

```bash
# Copy the example as your .claude folder
cp -r path/to/fractal-agent-system/example-claude .claude

# Or if you're inside the fractal-agent-system repo:
cp -r example-claude ../.claude
```

Then:

1. **Configure the router** — Edit `.claude/FRACTAL/router.py` and set `BLUEPRINT_PATH` to your blueprint file (e.g. `BLUEPRINT-MyEpic.yaml`).
2. **Add .gitignore entries** in your project root:
   ```gitignore
   .claude/FRACTAL/.state.json
   .claude/FRACTAL/workstreams/*/PULSE.md
   .claude/FRACTAL/workstreams/*/HANDOFF.md
   .claude/FRACTAL/intake/*
   !.claude/FRACTAL/intake/README.md
   ```
3. **Create your BLUEPRINT** — Replace or edit `BLUEPRINT-Example.yaml` and add workstream PRDs under `.claude/FRACTAL/workstreams/`.
4. **Customize agents** — Replace `{project}` and paths in `.claude/agents/` with your project name and guide paths.
5. **Customize eval templates** — Edit `.claude/FRACTAL/EVAL_TEMPLATES/*.md` with your build commands and guiding principles.

## What's included

| Path | Purpose |
|------|--------|
| `agents/` | Architect, Strategist, Feature Lead, Sub-Agent definitions |
| `skills/` | fractal-init, pulse, handoff, gap-analysis, commit-summarize |
| `FRACTAL/router.py` | Deterministic state machine (copy from ROUTING_LOGIC) |
| `FRACTAL/BLUEPRINT-Example.yaml` | Example blueprint — replace with your epic |
| `FRACTAL/workstreams/` | Example workstream PRD; add one per workstream |
| `FRACTAL/intake/README.md` | Strategist intake folder guide (intake itself is gitignored) |
| `FRACTAL/ISSUES.md` | Template for logging framework-level issues |
| `FRACTAL/EVAL_TEMPLATES/` | Layer 1–4 eval templates (deterministic, LLM judgment, persona, strategic) |

## Prerequisites

- Python 3.8+ with `pyyaml` (`pip install pyyaml`)
- Claude Code CLI with Agent and Skill support

Full setup and usage: see the repo root [SETUP-CLAUDE-CODE.md](../SETUP-CLAUDE-CODE.md) and [BEST-PRACTICES.md](../BEST-PRACTICES.md).
