# Strategic Benchmark Evaluation — Layer 4

**Milestone-level evaluation. Run at each milestone boundary alongside `/gap-analysis`.**
**Owner: Strategist (user)** — NOT the Architect. This eval does not block workstream completion.

This template measures your product's progression toward your strategic vision (e.g. "best-in-class in our category"). It is a strategic product assessment, not a code review.

## Ownership & Flow

- The Strategist runs this at milestone boundaries (not per-workstream).
- Results inform **strategic decisions**: roadmap adjustments, milestone re-scoping, investment priorities.
- Results do NOT block individual workstream completion — the Architect owns mechanical quality.
- Low scores may generate new epics or shift priorities for the next milestone.

## How to Customize

1. **Define your strategic pillars** (3–5 areas that matter for "what good looks like").
2. **Define scoring criteria** per pillar (0–5 or Pass/Partial/Fail).
3. **Reference material:** Link to your STRATEGIST doc, competitive analysis, or benchmark docs.
4. **Run at milestone boundaries** and store results (e.g. in `docs/strategic-benchmark-YYYY-MM.md`).

## Example Pillar Structure

| Pillar | What you're measuring | Example criteria |
|--------|------------------------|------------------|
| [Pillar 1] | e.g. Core product completeness | Features shipped, parity with reference |
| [Pillar 2] | e.g. Platform / API readiness | API coverage, docs, SDK |
| [Pillar 3] | e.g. Trust / compliance | Audit trail, security, certifications |
| [Pillar 4] | e.g. Ecosystem / integration | Embeddability, partner readiness |

**Scoring:** 0 = Not started, 1 = Planned, 2 = Shell exists, 3 = Functional but incomplete, 4 = Production-grade, 5 = Best-in-class.

## Output Format

```markdown
## Strategic Benchmark — [Milestone Name] — [Date]

### Pillar Scores
| Pillar | Score | Target | Notes |
|--------|-------|--------|-------|
| ... | /5 | | |

### Gap Summary
- **Strongest area:** [...]
- **Biggest gap:** [...]
- **Recommended focus for next milestone:** [...]
```

## Relationship to Other Evals

```
ARCHITECT-OWNED (blocks HANDOFF — per workstream):
  Layer 1: Deterministic Eval
  Layer 2: LLM Judgment Eval → mark COMPLETE

STRATEGIST-OWNED (informs backlog):
  Layer 3: Qualitative Persona Eval
  Layer 4: Strategic Benchmark Eval ← THIS TEMPLATE (milestone-level only)

/gap-analysis → WHAT to fix (tactical backlog)
Strategic Benchmark → WHETHER we're building the right thing (strategic direction)
```
