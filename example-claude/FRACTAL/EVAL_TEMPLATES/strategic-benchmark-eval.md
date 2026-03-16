# Strategic Benchmark Evaluation — Layer 4

**Milestone-level evaluation. Run at each milestone boundary alongside `/gap-analysis`.**
**Owner: Strategist (user)** — NOT the Architect. This eval does not block workstream completion.

This template measures your product's progression toward your strategic vision (e.g. "best-in-class in our category"). It is a strategic product assessment, not a code review.

## Ownership & Flow

- The Strategist runs this at milestone boundaries (not per-workstream).
- Results inform **strategic decisions**: roadmap adjustments, milestone re-scoping, investment priorities.
- Results do NOT block individual workstream completion — the Architect owns mechanical and technical quality.
- Low scores may generate new epics or shift priorities for the next milestone.

## How to Customize

1. **Define your strategic pillars** (3–5 areas that matter for "what good looks like").
2. **Define scoring criteria** per pillar (0–5 scale).
3. **Reference material:** Link to your STRATEGIST doc Section 0 (What Right Looks Like) as the benchmark source.
4. **Run at milestone boundaries** and store results (e.g. in `docs/strategic-benchmark-YYYY-MM.md`).

## Example Pillars (TaskFlow kanban tracker)

| Pillar | What You're Measuring | Scoring Criteria |
|--------|----------------------|------------------|
| **Core Board UX** | Does the board feel as fast and responsive as Linear? | 0 = no board, 1 = renders but laggy, 2 = functional but perceptible latency, 3 = smooth for <50 issues, 4 = smooth for 100+ issues, 5 = indistinguishable from Linear |
| **Keyboard Navigation** | Can a power user complete a full workflow without a mouse? | 0 = no shortcuts, 1 = Cmd+K only, 2 = 5+ shortcuts, 3 = all CRUD via keyboard, 4 = full workflow mouse-free, 5 = matches Linear's keyboard coverage |
| **Data Integrity & Auth** | Are team boundaries enforced? Is data safe? | 0 = no auth, 1 = login works, 2 = RLS on some tables, 3 = RLS on all tables + tests, 4 = auth flow < 2 min + RLS complete, 5 = audit-ready with session management |
| **Visual Polish & UX** | Does the product look intentional, not like a hackathon project? | 0 = unstyled, 1 = basic Tailwind, 2 = shadcn/ui integrated, 3 = dark/light mode, 4 = visual density matches Linear, 5 = distinctive identity beyond "shadcn default" |

## Example Output (Milestone M1)

```markdown
## Strategic Benchmark — M1: Board + Drag-and-Drop — 2026-03-15

### Pillar Scores
| Pillar | Score | Target | Notes |
|--------|-------|--------|-------|
| Core Board UX | 3/5 | 5/5 | Smooth with <50 issues. Drag-and-drop has minor jank on rapid reorder. |
| Keyboard Navigation | 1/5 | 5/5 | Cmd+K exists but no single-key shortcuts yet. Expected — M3 scope. |
| Data Integrity & Auth | 0/5 | 4/5 | No auth yet. Expected — M2 scope. |
| Visual Polish & UX | 2/5 | 4/5 | shadcn/ui integrated, dark mode works. Cards lack visual density. |

### Gap Summary
- **Strongest area:** Core Board UX — interaction model validated, drag-and-drop foundation solid
- **Biggest gap:** Visual density — cards are too spacious, need compact mode
- **Recommended focus for next milestone:** Invest in M2 (data layer + auth). Visual density is a polish task, not a blocker.
```

## Template for Your Project

Replace the pillar names and criteria with your project's strategic priorities from your Strategist doc Section 0.

```markdown
## Strategic Benchmark — [Milestone Name] — [Date]

### Pillar Scores
| Pillar | Score | Target | Notes |
|--------|-------|--------|-------|
| [Pillar 1] | /5 | /5 | |
| [Pillar 2] | /5 | /5 | |
| [Pillar 3] | /5 | /5 | |
| [Pillar 4] | /5 | /5 | |

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
