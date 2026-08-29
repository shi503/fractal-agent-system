paths: [".claude/fractal/**", "ROUTING_LOGIC/**"]
---

# FRACTAL Protocol

**Canonical reference:** `.claude/fractal/` — framework state, blueprints, and workstream
artifacts live here.

## Tier table

| Tier | Agent | Model | Role |
|---|---|---|---|
| 0 | Strategist | opus | Initiative intent, constraints, failure modes |
| 1 | Architect | opus | BLUEPRINT authoring, HANDOFF review, cross-workstream coordination |
| 2 | Feature Lead | sonnet | Single workstream end-to-end |
| 3 | Sub-Agent | sonnet | Atomic single-file task from a Feature Lead |

Agent definitions: `.claude/plugins/fractal-core/agents/{architect,strategist,feature-lead,sub-agent}.md`
(mirrored, byte-identical, at `.claude/agents/`).

## Key paths

| Path | Purpose |
|---|---|
| `.claude/fractal/BLUEPRINT-*.yaml` | Active blueprint(s) — top-level files, not a `blueprints/` subdirectory |
| `.claude/fractal/workstreams/` | Per-workstream artifacts: a single `<name>.md` (PRD), or a `<name>/` directory holding `HANDOFF.md` and, once emitted, `PULSE.md` |
| `.claude/fractal/templates/` | Canonical skeletons — `blueprint-template.yaml`, `prd-template.md`, `handoff-template.md`, `pulse-template.md` |
| `.claude/fractal/EVAL_TEMPLATES/` | Deterministic, LLM-judgment, qualitative-persona, and strategic-benchmark eval templates |
| `.claude/fractal/STRATEGIST-taskflow.md` | Tier 0 intent doc for the live project (`STRATEGIST-example.md` for the worked example) |
| `.claude/fractal/router.py` | Synced copy the harness invokes directly; canonical source is `ROUTING_LOGIC/router.py` — never edit them independently, use `tools/check-router-identity.sh` to catch drift |
| `.claude/fractal/ISSUES.md` | Append-only framework-error audit trail |
| `.claude/fractal/_archive/` | Release-batched historical handoffs |
| `.claude/fractal/.state.json` | Router state file — gitignored runtime artifact, not committed |

## Router commands (Feature Lead scope)

Feature Leads may ONLY run:

```bash
python3 .claude/fractal/router.py update <workstream_name> <status>
```

**Never run `router.py init`.** `cmd_init` in `router.py` sets every workstream in the
blueprint to `NOT_STARTED` and overwrites `.state.json` unconditionally — running it against
a blueprint with in-flight or completed workstreams silently wipes that progress. It is a
bootstrap-only command; only an Architect runs it, and only once per blueprint. This exact
foot-gun is called out in `.claude/plugins/fractal-core/skills/fractal-init/SKILL.md`'s
Gotchas section.

**Never run `router.py next`** to self-advance — workstream sequencing is Architect-controlled.

`router.py` defaults `BLUEPRINT_PATH` to the fixture corpus
(`fixtures/taskflow/blueprints/BLUEPRINT-NOVA-P1-NotificationCore.yaml`); pass
`--blueprint <path>` to target a different blueprint.

## HANDOFF requirements

Every Feature Lead `HANDOFF.md` includes: summary of work completed (file paths, function
names, line numbers), summary of work NOT completed, technical debt, key decisions
(deviations from the PRD), and a verification evidence table (build/test gates, secrets and
contamination scans).

## PULSE cadence

Emit a PULSE entry when a session exceeds 30 minutes, a milestone boundary is crossed, or a
blocker is encountered. Format:

```json
{
  "timestamp": "<ISO 8601 UTC>",
  "status": "IN_PROGRESS",
  "tasks_completed": "X/Y",
  "blockers": "none | <description>",
  "escalation_needed": false
}
```

<!-- referenced-paths
.claude/fractal/router.py
ROUTING_LOGIC/router.py
tools/check-router-identity.sh
.claude/fractal/templates
.claude/fractal/EVAL_TEMPLATES
.claude/fractal/ISSUES.md
.claude/fractal/_archive
.claude/fractal/workstreams
.claude/plugins/fractal-core/agents/architect.md
.claude/plugins/fractal-core/agents/feature-lead.md
.claude/plugins/fractal-core/agents/strategist.md
.claude/plugins/fractal-core/agents/sub-agent.md
.claude/agents
.claude/plugins/fractal-core/skills/fractal-init/SKILL.md
.claude/fractal/STRATEGIST-taskflow.md
.claude/fractal/STRATEGIST-example.md
fixtures/taskflow/blueprints/BLUEPRINT-NOVA-P1-NotificationCore.yaml
-->
