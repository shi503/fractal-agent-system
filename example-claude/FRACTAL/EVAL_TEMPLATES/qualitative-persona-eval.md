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

## Personas (Customize)

_Define 1–3 key user personas for your product. For each, list 3–5 evaluation questions._

**Example structure:**

| Persona | Role / Segment | Evaluation focus |
|---------|----------------|------------------|
| [Persona A] | e.g. Economic buyer | Defensibility, workflow fit, audit readiness |
| [Persona B] | e.g. Integration owner | API-first, schema stability, observability |
| [Persona C] | e.g. End operator | Trust, clarity, speed under pressure |

**Per-persona questions (replace with your own):**
1. Does this meet [persona]'s bar for [criterion 1]?
2. Would [persona] trust this in production?
3. [Add 1–3 more questions per persona.]

**Scoring:** Pass / Partial / Fail for each question. Document any Partial or Fail with a brief remediation note.

## Output Format

```markdown
## Qualitative Persona Evaluation — [Workstream Name]

**Date:** YYYY-MM-DD
**Personas evaluated:** [list]

### [Persona Name]
| # | Question | Score | Notes |
|---|----------|-------|-------|
| 1 | ... | Pass/Partial/Fail | ... |

### Overall Result
- **Result:** PASS / CONDITIONAL PASS / FAIL
- **Remediation:** [if any Partial/Fail, what needs to happen]
```

## Relationship to Other Evals

```
ARCHITECT-OWNED (blocks HANDOFF):
  Layer 1: Deterministic Eval → PASS required
  Layer 2: LLM Judgment Eval → PASS required → mark COMPLETE

STRATEGIST-OWNED (informs backlog):
  Layer 3: Qualitative Persona Eval ← THIS TEMPLATE
  Layer 4: Strategic Benchmark Eval (milestone-level)
```
