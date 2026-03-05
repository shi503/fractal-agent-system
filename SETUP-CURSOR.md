# FRACTAL Setup Guide — Cursor

This guide walks through integrating FRACTAL into a Cursor project. Cursor uses rules (`.mdc` files) and skills (SKILL.md) instead of Claude Code's agent frontmatter. The deterministic router and BLUEPRINT format are the same; only the integration points differ.

**Time to set up:** ~30 minutes  
**Prerequisites:** Cursor, Python 3, `pyyaml`

---

## 1. Verify Prerequisites

```bash
python3 --version        # 3.8+
python3 -c "import yaml; print('pyyaml ok')"
# If missing: pip install pyyaml
```

---

## 2. Directory Structure

Use a single **FRACTAL root** in your project (e.g. `.fractal/`). Cursor does not use `.claude/` by default, so `.fractal/` keeps FRACTAL artifacts in one place.

```bash
mkdir -p .fractal/workstreams
mkdir -p .cursor/rules
mkdir -p .cursor/skills/fractal-init
mkdir -p .cursor/skills/pulse
mkdir -p .cursor/skills/handoff
mkdir -p .cursor/skills/commit-summarize
```

---

## 3. Copy Router and Configure

Copy the router from this repo into your project:

```bash
cp fractal-agents-system/ROUTING_LOGIC/router.py .fractal/router.py
# Or, if this repo IS your project: cp ROUTING_LOGIC/router.py .fractal/router.py
```

Edit `.fractal/router.py` and set the paths at the top:

```python
BLUEPRINT_PATH = os.path.join(os.path.dirname(__file__), "BLUEPRINT-MyEpic.yaml")
STATE_PATH     = os.path.join(os.path.dirname(__file__), ".state.json")
```

Use a real blueprint filename once you create one. The router supports `.yaml`/`.yml` (recommended) or `.md` with a fenced YAML block.

---

## 4. Add .gitignore Entries

Add to your project's `.gitignore`:

```gitignore
# FRACTAL runtime artifacts
.fractal/.state.json
.fractal/workstreams/*/PULSE.md
.fractal/workstreams/*/HANDOFF.md
```

Commit: `router.py`, `BLUEPRINT-*.yaml`, and workstream PRD `.md` files. Do not commit state, PULSE, or HANDOFF.

---

## 5. Install Cursor Rules

Copy the FRACTAL rule files from this repo into your project:

```bash
cp fractal-agents-system/cursor/rules/fractal-architect.mdc    .cursor/rules/
cp fractal-agents-system/cursor/rules/fractal-feature-lead.mdc .cursor/rules/
cp fractal-agents-system/cursor/rules/fractal-sub-agent.mdc    .cursor/rules/
```

- **fractal-architect.mdc** — Apply when working in `.fractal/` or on BLUEPRINT/workstreams. Architect mode: no implementation code, only BLUEPRINTs, PRDs, HANDOFF eval.
- **fractal-feature-lead.mdc** — Apply when executing a workstream (e.g. when the active file is a workstream PRD under `.fractal/workstreams/`).
- **fractal-sub-agent.mdc** — Apply manually or via instruction when delegating an atomic sub-task (e.g. in the same chat: "Act as the FRACTAL Sub-Agent for this task: ...").

Cursor does not have a "model" field in rules; model selection is per chat or per Task invocation. Use a capable model for Architect work (e.g. Opus-tier when available) and Sonnet-tier for Feature Lead and Sub-Agent when possible.

---

## 6. Install Cursor Skills

Copy the skill directories:

```bash
cp -r fractal-agents-system/cursor/skills/fractal-init     .cursor/skills/
cp -r fractal-agents-system/cursor/skills/pulse            .cursor/skills/
cp -r fractal-agents-system/cursor/skills/handoff         .cursor/skills/
cp -r fractal-agents-system/cursor/skills/commit-summarize .cursor/skills/
```

Skills are invoked by name in Cursor (e.g. fractal-init, pulse, handoff, commit-summarize). When you run a skill, pass the argument (e.g. blueprint filename or FeatureLead name) as specified in each SKILL.md.

---

## 7. Path Conventions in Skills

The Cursor skills in this repo use **`.fractal/`** as the FRACTAL root. If you use a different path (e.g. `.claude/FRACTAL/`), do a find-replace in the copied skills:

- `.fractal/` → your FRACTAL root
- `python3 .fractal/router.py` → `python3 <your-path>/router.py`

---

## 8. Create Your First BLUEPRINT

Create `.fractal/BLUEPRINT-{EpicName}.yaml`. **The file must be a top-level YAML list.** Do not wrap in a `phases:` key.

```yaml
- name: "Phase 1 — Core (parallel)"
  workstreams:
    - feature_lead: FeatureLead-Database
      model: sonnet
      prd: .fractal/workstreams/database.md
      dependencies: []

    - feature_lead: FeatureLead-API
      model: sonnet
      prd: .fractal/workstreams/api.md
      dependencies: []

- name: "Phase 2 — UI (depends on Phase 1)"
  workstreams:
    - feature_lead: FeatureLead-UI
      model: sonnet
      prd: .fractal/workstreams/ui.md
      dependencies:
        - FeatureLead-Database
        - FeatureLead-API
```

Update `BLUEPRINT_PATH` in `router.py` to this filename, then run:

```bash
python3 .fractal/router.py init
python3 .fractal/router.py next
```

---

## 9. Write Workstream PRDs

Each workstream needs a PRD at `.fractal/workstreams/{kebab-name}.md` with:

- **Goal** — One sentence
- **Context** — What the Feature Lead needs; reference project guides by path only
- **Acceptance Criteria** — Binary, verifiable
- **File Manifest** — Read list and Write list
- **Session Protocol** — Read manifest first, build gate, /pulse if >30 min or blocked, /handoff on completion

---

## 10. Run a Workstream in Cursor

1. **Init (once per epic):** Run the `fractal-init` skill with the blueprint filename (e.g. `BLUEPRINT-MyEpic.yaml`).
2. **Claim a workstream:** `python3 .fractal/router.py update FeatureLead-MyWorkstream IN_PROGRESS`
3. **Execute:** Open the workstream PRD (e.g. `.fractal/workstreams/my-workstream.md`) and ensure the Feature Lead rule is in effect (or @-mention it). Implement per the PRD, run build gate, then run the `handoff` skill with the FeatureLead name.
4. **Pulse (optional):** If the session runs long or you hit a blocker, run the `pulse` skill with the FeatureLead name.
5. **After HANDOFF:** Review HANDOFF.md, then `python3 .fractal/router.py update FeatureLead-MyWorkstream COMPLETE` and `python3 .fractal/router.py next`.

---

## 11. Task Tool (Sub-Agents)

Cursor's Task tool can run a sub-agent with a specific instruction set. To run a Sub-Agent for an atomic task:

1. In the same project, start a Task (or a new chat).
2. Provide: the Sub-Agent rule context (or paste the fractal-sub-agent.mdc content), the one-sentence task, the read/write file manifest, and 1–3 acceptance criteria.
3. The Sub-Agent executes and reports back; the Feature Lead (you or the main session) reviews and continues.

Model selection for the Task is independent of the rule; use Sonnet or similar for typed/framework code.

---

## 12. Differences from Claude Code

| Aspect | Claude Code | Cursor |
|--------|-------------|--------|
| Agent definitions | `.claude/agents/*.md` with `model:` frontmatter | `.cursor/rules/*.mdc` — no model in file; model at invocation |
| FRACTAL root | `.claude/FRACTAL/` | `.fractal/` (or your choice) |
| Skills | `.claude/skills/*/SKILL.md` | `.cursor/skills/*/SKILL.md` |
| Sub-agent spawn | Agent tool with agent name | Task tool + Sub-Agent rule / instructions |

The router (`router.py`), BLUEPRINT format, and HANDOFF/PULSE semantics are identical. Only the paths and how you invoke "agents" and "skills" differ.

---

## Full Directory Reference (Cursor)

After setup:

```
.fractal/
├── router.py
├── STRATEGIST-{project}.md    # Optional; from Strategist interview
├── BLUEPRINT-{Epic}.yaml
├── .state.json               # Gitignored
├── EVAL_TEMPLATES/           # Optional; copy from src/ or create
└── workstreams/
    ├── {workstream-1}.md     # PRDs (committed)
    ├── {workstream-2}.md
    └── {workstream-1}/       # Created at runtime (gitignored)
        ├── PULSE.md
        └── HANDOFF.md

.cursor/
├── rules/
│   ├── fractal-architect.mdc
│   ├── fractal-feature-lead.mdc
│   └── fractal-sub-agent.mdc
└── skills/
    ├── fractal-init/SKILL.md
    ├── pulse/SKILL.md
    ├── handoff/SKILL.md
    └── commit-summarize/SKILL.md
```
