# Qualitative Persona Evaluation — Layer 3

**Layer 3 of the FRACTAL evaluation pipeline.**
**Owner: Strategist (user)** — NOT the Architect. This eval does not block workstream completion.

Run AFTER the Architect marks the workstream COMPLETE (Layers 1–2 passed). The Strategist reviews at their discretion — per-workstream for high-stakes features, or at milestone boundaries.

## Ownership & Flow

- **Does NOT block HANDOFF approval.** The Architect marks COMPLETE when Layers 1–2 pass.
- Qualitative findings become **backlog items** for future work (feature requests, pivots, UX improvements).
- **Exception — CRITICAL failure:** If a finding fundamentally breaks a Guiding Principle, the Strategist can escalate it back to the Architect as a blocking remediation.
- **2-attempt limit on CRITICAL escalations:** If the Architect sends it to a Feature Lead and it fails twice, escalate to Strategist for a decision (rework, descope, defer, or accept with documented debt).

## When to Use

- User-facing workstreams: new pages, workflow UIs, data displays, onboarding flows
- Skip for: migrations, backend-only routes with no UI, config changes, refactors

## Example Personas (TaskFlow kanban tracker)

| Persona | Role / Segment | Evaluation Focus |
|---------|----------------|------------------|
| **Self-Hoster Admin** | Deploys and maintains the instance, no vendor support | Deployment/upgrade friction, resource footprint, backup/restore |
| **Keyboard Power-User** | Daily user who never reaches for the mouse | Keystroke coverage, focus handling, completing a flow keyboard-only |
| **Team Lead** | Manages a team's board, onboards new members | Cross-member visibility, board configuration, member onboarding |

### Self-Hoster Admin — Evaluation Questions

1. Can this be deployed and upgraded via the documented self-host path (e.g. Docker Compose) with no undocumented manual steps?
2. Does this keep the resource footprint predictable, or does it pull in a new required service or dependency?
3. Is any new data covered by the existing backup/restore process, or does it introduce a store that isn't backed up?
4. Are migrations safe to run against existing self-hosted data — no silent data loss on upgrade?
5. Would the admin trust this in a small-team production deployment with no vendor support to fall back on?

### Keyboard Power-User — Evaluation Questions

1. Is every action reachable by keyboard shortcut, with no action gated behind a mouse-only affordance?
2. Does focus move predictably — logical tab order, no focus trap outside an intentional modal?
3. Can the full flow (open → act → confirm/close) be completed start to finish without touching the mouse?
4. Is the keyboard shortcut discoverable (hint, command-palette entry) rather than something the user has to already know?
5. Does the interaction feel instant — no perceptible lag between keypress and UI update?

### Team Lead — Evaluation Questions

1. Can the team lead see cross-member workload or status at a glance, or does the feature only surface one person's view?
2. Can the team lead configure the board (columns, labels, permissions) to match the team's process without engineering help?
3. Does onboarding a new member into this feature require more than an invite plus default access?
4. Is data correctly scoped to the team lead's own team, with no leakage from or to other teams?
5. Would the team lead trust this enough to roll out to the whole team without a pilot caveat?

## Scoring

**Per question:** Pass / Partial / Fail

- **Pass** — Meets the persona's bar without caveats
- **Partial** — Functional but has notable gaps; document remediation
- **Fail** — Does not meet the persona's bar; requires rework

## Output Format

```markdown
## Qualitative Persona Evaluation — [Workstream Name]

**Date:** YYYY-MM-DD
**Personas evaluated:** Self-Hoster Admin, Keyboard Power-User, Team Lead

### Self-Hoster Admin
| # | Question | Score | Notes |
|---|----------|-------|-------|
| 1 | Deployable/upgradable via documented path? | Pass/Partial/Fail | ... |
| 2 | Resource footprint stays predictable? | Pass/Partial/Fail | ... |
| 3 | Covered by backup/restore? | Pass/Partial/Fail | ... |
| 4 | Migrations safe on existing data? | Pass/Partial/Fail | ... |
| 5 | Trusted without vendor support? | Pass/Partial/Fail | ... |

### Keyboard Power-User
| # | Question | Score | Notes |
|---|----------|-------|-------|
| 1 | Every action keyboard-reachable? | Pass/Partial/Fail | ... |
| 2 | Focus handling predictable? | Pass/Partial/Fail | ... |
| 3 | Full flow completable keyboard-only? | Pass/Partial/Fail | ... |
| 4 | Shortcut discoverable? | Pass/Partial/Fail | ... |
| 5 | Interaction feels instant? | Pass/Partial/Fail | ... |

### Team Lead
| # | Question | Score | Notes |
|---|----------|-------|-------|
| 1 | Cross-member visibility? | Pass/Partial/Fail | ... |
| 2 | Board configurable without engineering? | Pass/Partial/Fail | ... |
| 3 | Onboarding a new member is simple? | Pass/Partial/Fail | ... |
| 4 | Data scoped correctly to team? | Pass/Partial/Fail | ... |
| 5 | Trusted for full team rollout? | Pass/Partial/Fail | ... |

### Overall Result
- **Result:** PASS / CONDITIONAL PASS / FAIL
- **Remediation:** [if any Partial/Fail, what needs to happen]
```

## Customizing for Your Project

1. Replace the three personas above with your actual user segments.
2. Write 3–5 evaluation questions per persona that reflect what they care about.
3. Tie questions back to your Strategist doc's Guiding Principles and Failure Mode Register.

## Relationship to Other Evals

```
ARCHITECT-OWNED (blocks HANDOFF):
  Layer 1: Deterministic Eval → PASS required
  Layer 2: LLM Judgment Eval → PASS required → mark COMPLETE

STRATEGIST-OWNED (informs backlog):
  Layer 3: Qualitative Persona Eval ← THIS TEMPLATE
  Layer 4: Strategic Benchmark Eval (milestone-level)
```
