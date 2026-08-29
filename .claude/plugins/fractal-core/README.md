# fractal-core

The FRACTAL orchestration loop itself. Skills a repo needs to run FRACTAL end to end: bootstrap an epic, emit heartbeats, hand off a completed workstream, cut a release, and keep quality gates honest.

## Skills

| Skill | Purpose |
|-------|---------|
| `fractal-init` | Bootstrap a FRACTAL epic session — verify router.py, initialize state, display ready workstreams |
| `fractal-maintenance` | Cut a release archive and lint the FRACTAL tree |
| `pulse` | Emit a structured heartbeat from a Feature Lead session and check for escalation |
| `handoff` | Generate HANDOFF.md for a completed workstream, run the eval gate, update router state |
| `quality-pass` | Review recent changes for AI slop and code quality issues before handoff |
| `gap-analysis` | Run a structured gap analysis at a milestone boundary |
| `claude-md-audit` | Score a CLAUDE.md file against the FRACTAL rubric and propose improvements |
| `commit-summarize` | Commit work in progress with a concise, scannable, review-gated summary |

## Install target

Every repo adopting FRACTAL.
