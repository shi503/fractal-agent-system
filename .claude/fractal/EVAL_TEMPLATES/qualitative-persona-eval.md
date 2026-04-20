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
| **Engineering Lead** | Technical buyer, evaluating tools for their team | Keyboard efficiency, customizability, data export, self-hosting ease |
| **Individual Contributor** | Day-to-day user managing their tasks | Speed, clarity, reduced friction, "does this feel faster than what I use now?" |
| **Demo Observer** | Stakeholder watching a product demo | Visual polish, wow factor, "does this look professional and intentional?" |

### Engineering Lead — Evaluation Questions

1. Would this feature convince an engineering lead to adopt TaskFlow over Linear/Jira for their team?
2. Can the user discover this feature without reading documentation?
3. Is the keyboard workflow complete — can the user accomplish the task without a mouse?
4. Does the data model support future extensibility (custom fields, integrations)?
5. Would the engineering lead trust this with production team data?

### Individual Contributor — Evaluation Questions

1. Does this feature reduce friction compared to the user's current tool?
2. Is the interaction latency imperceptible (< 100ms)?
3. Is the visual hierarchy clear — does the user immediately know what to do?
4. Can the user undo a mistake easily?

### Demo Observer — Evaluation Questions

1. Does the feature look polished and intentional (not like a prototype)?
2. Does the animation/transition quality match modern SaaS products?
3. Would this create a "wow" moment in a 5-minute demo?

## Scoring

**Per question:** Pass / Partial / Fail

- **Pass** — Meets the persona's bar without caveats
- **Partial** — Functional but has notable gaps; document remediation
- **Fail** — Does not meet the persona's bar; requires rework

## Output Format

```markdown
## Qualitative Persona Evaluation — [Workstream Name]

**Date:** YYYY-MM-DD
**Personas evaluated:** Engineering Lead, Individual Contributor, Demo Observer

### Engineering Lead
| # | Question | Score | Notes |
|---|----------|-------|-------|
| 1 | Adopt over Linear/Jira? | Pass/Partial/Fail | ... |
| 2 | Discoverable without docs? | Pass/Partial/Fail | ... |
| 3 | Keyboard workflow complete? | Pass/Partial/Fail | ... |
| 4 | Extensible data model? | Pass/Partial/Fail | ... |
| 5 | Trust with production data? | Pass/Partial/Fail | ... |

### Individual Contributor
| # | Question | Score | Notes |
|---|----------|-------|-------|
| 1 | Reduces friction? | Pass/Partial/Fail | ... |
| 2 | Latency < 100ms? | Pass/Partial/Fail | ... |
| 3 | Visual hierarchy clear? | Pass/Partial/Fail | ... |
| 4 | Undo available? | Pass/Partial/Fail | ... |

### Demo Observer
| # | Question | Score | Notes |
|---|----------|-------|-------|
| 1 | Polished and intentional? | Pass/Partial/Fail | ... |
| 2 | Animation quality? | Pass/Partial/Fail | ... |
| 3 | "Wow" moment? | Pass/Partial/Fail | ... |

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
