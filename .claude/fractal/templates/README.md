# FRACTAL Templates

Canonical skeletons for the four artifact types. Agents (Architect, Feature Lead, Sub-Agent) reference these by path — do **not** copy-paste-and-drift.

| Template | Authored by | Consumed by | When |
|---|---|---|---|
| [`prd-template.md`](./prd-template.md) | Architect | Feature Lead | When authoring a workstream PRD |
| [`handoff-template.md`](./handoff-template.md) | Feature Lead | Architect (evaluation) | On workstream completion, before marking COMPLETE |
| [`pulse-template.md`](./pulse-template.md) | Feature Lead | Architect (monitor) | During execution, ~30 min cadence. File is gitignored. |
| [`blueprint-template.yaml`](./blueprint-template.yaml) | Architect | `router.py` + Feature Leads | When decomposing a new epic phase |

## Conventions

- **Workstream file shape:** `.claude/fractal/workstreams/{kebab-name}.md`, with a companion `PULSE.md` (gitignored) and `HANDOFF.md` produced alongside it during execution.
- **Blueprint location:** `.claude/fractal/BLUEPRINT-*.yaml`.
- **Decision references:** link by whatever ID scheme this repo already tracks (issue link, ADR filename, short slug); do not restate decisions inline.
- **Guide references:** link by path to `docs/guides/…`; do not paste guide content.

See the eval templates in `.claude/fractal/EVAL_TEMPLATES/` for the 4-layer evaluation pipeline these artifacts feed into.
