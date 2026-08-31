# Archive

Superseded `docs/` content, kept for history rather than deleted. Nothing here is current — do not follow it as a contract for how the ported FRACTAL machinery works today. See `docs/README.md` for the live reading order.

| File | Last commit | Inbound links (pre-archive) | Why archived |
|---|---|---|---|
| `ARCHITECT.md - The Orchestrator.md` | 2026-03-16 | 0 | Early conceptual draft of the Architect role, written against a generic "generate ARCHITECT.md" contract this repo never implements. Superseded by the live agent/skill definitions and `.claude/FRACTAL/templates/`. |
| `BLUEPRINT.md - The Deterministic Execution Plan.md` | 2026-03-16 | 0 | Early draft BLUEPRINT format (prose + embedded YAML, fictional sports-league example). Superseded by the canonical `.claude/FRACTAL/BLUEPRINT-Example.yaml` and `.claude/FRACTAL/templates/blueprint-template.yaml`, which reflect the actual schema `router.py` consumes. |
| `STRATEGIST.md - The Seed of Intent.md` | 2026-03-16 | 0 | Early draft Strategist-doc template (fictional sports-league example). Superseded by the canonical `.claude/FRACTAL/STRATEGIST-example.md`, a real completed Strategist interview output for this repo's own TaskFlow demo project. |
| `The Four Disciplines of Prompting: A New Framework for AI-Powered Work.md` | 2026-03-16 | 0 | External framework summary (Nate B. Jones) that informed FRACTAL's design. Background/inspiration only — never wired into any workflow or referenced elsewhere. Kept for provenance. |

Disposition recorded 2026-08-30: deprecation triage, not renaming.

`docs/The FRACTAL Multi-Agent System.pptx` (2026-03-16, 0 inbound doc links) was deleted rather than archived in the same pass — its content is fully superseded 1:1 by the actively maintained `The FRACTAL Multi-Agent System.md` at the repo root (last touched 2026-08-28, 4 inbound links). The binary added no information the live doc lacks, so archiving it would have preserved dead weight rather than history. `tools/release-gate.sh`'s 2 MB allowlist entry for it was removed in the same commit.
