# LLM Judgment Eval — [WorkstreamName] | [Date]

_Used by Architect after deterministic eval passes. Apply for non-mechanical workstreams (new components, new services, multi-file features). Skip for purely mechanical work (migrations, config, single-field additions)._

---

## When to Use This Eval

**Use:** New components, new stores, new API routes, integration work, anything user-facing.

**Skip:** Schema migrations, single computed/derived additions, config changes, pure refactors with no behavior change.

---

## Prompt for LLM Judge

Copy the prompt below into a new Claude session. Paste the workstream PRD and code diff where indicated. Replace the bracketed sections with your project's actual values.

> **Example (TaskFlow kanban tracker):** The guiding principles would be:
> 1. Speed is the feature — every interaction < 100ms perceived latency
> 2. Keyboard-first, mouse-optional — power users never touch the mouse
> 3. Opinionated defaults over configuration — one board layout, one workflow
> 4. Local-first optimistic updates — UI never waits for the server

```
You are a senior architect reviewing a completed feature for [YOUR PROJECT NAME].
Deterministic checks (lint, build, typecheck, tests) have already passed. Your job is to assess alignment with project intent.

**Project Guiding Principles:**
[REPLACE with your project's actual guiding principles from STRATEGIST.md §2.]
- [Principle 1]
- [Principle 2]
- [Principle 3]
- [Principle 4]

**Workstream PRD:**
[Paste PRD here]

**Code Diff (git diff main...HEAD):**
[Paste diff here]

**Assessment Questions:**
1. Does the implementation align with the spirit of the PRD and guiding principles? (Yes / No / Partially)
2. Is the architecture clean and idiomatic for this tech stack? (Yes / No / Partially)
3. Would a real end-user or operator trust and understand this feature? (Yes / No / Partially — explain why)
4. Is there any security or compliance risk not caught by the deterministic gate? (Yes / No)
5. Specific actionable feedback — especially explain any "No" or "Partially" answers.
6. Is there any inconsistency between this workstream and existing patterns in the codebase?
   Examples: two parallel UI flows doing the same job, a new store that diverges from established patterns,
   a new API route that duplicates an existing endpoint. (Yes / No)
7. For every "No" or "Partially" answer above: provide a specific concrete remediation.
   Do NOT describe the gap in general terms. State exactly: the file path, the function or
   component name, and the specific change required.
```

---

## Known False Positives — Do Not Flag

_Document patterns that the LLM judge has incorrectly flagged in the past. Update as you find them._

**Format:** `[pattern]`: [Why it looks wrong] — [Why it's actually correct]

**Example:**
- **`gt(createdAt)` + `ORDER BY DESC`**: Correct for forward cursor-based pagination when ordering newest-first; fetching "next page" means items *newer* than the cursor — `gt` is correct, not `lt`.

---

## LLM Judge Response

_Paste response here._

---

## Architect's Assessment

_Brief notes on whether the response changes the approval decision._

---

## Final Result

- [ ] **PASS** — mark workstream COMPLETE in router
- [ ] **FAIL** — return to Feature Lead with specific feedback items listed below

### Feedback for Feature Lead (if FAIL)

_List specific issues with file:line references where possible._
