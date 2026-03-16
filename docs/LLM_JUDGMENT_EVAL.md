# LLM Judgment Evaluation Template

_This template is used by the Architect to perform an LLM-based assessment of a completed workstream. It evaluates alignment with project intent — not mechanical correctness (that's Layer 1). **Customize the Guiding Principles for your project.**_

---

## Feature: [Feature Name]

### 1. Prompt for LLM Judge

Copy this prompt into a new Claude session. Paste the workstream PRD and code diff where indicated.

```
You are a senior software architect reviewing a completed feature for [YOUR PROJECT NAME].
Deterministic checks (build, lint, tsc, security) have already passed. Your job is to assess alignment with project intent.

**Project Guiding Principles:**
[REPLACE with your project's actual guiding principles from STRATEGIST.md §2. Examples below:]
- [Principle 1: e.g., "Provenance first — every AI output links to exact source text; audit trail is non-negotiable"]
- [Principle 2: e.g., "Framework idioms — use the framework's intended patterns, not workarounds"]
- [Principle 3: e.g., "Security by default — no credentials in logs, PHI only in authorized data stores"]
- [Principle 4: e.g., "Ship fast, stay clean — minimum complexity for the current task"]

**Workstream PRD:**
[Paste PRD here]

**Code Diff:**
[Paste diff here]

**Assessment Questions:**
1. Does the implementation align with the spirit of the PRD and guiding principles? (Yes / No / Partially)
2. Is the architecture clean and idiomatic for this tech stack? (Yes / No / Partially)
3. Would a real end-user or operator trust and understand this feature? (Yes / No / Partially — explain why)
4. Is there any security or compliance risk not caught by the deterministic gate? (Yes / No)
5. Specific actionable feedback — especially explain any "No" or "Partially" answers.
6. Is there any inconsistency between this workstream and existing patterns in the codebase?
   Examples: two parallel UI channels doing the same job, a new store/service that diverges from
   adjacent patterns, a new API route that duplicates an existing endpoint. (Yes / No)
7. For every "No" or "Partially" answer above: provide a specific concrete remediation.
   Do NOT describe the gap in general terms. State exactly: the file path, the function or
   component name, and the specific change required.
```

---

### 2. Known False Positives — Do Not Flag

*Document patterns that look like bugs but are correct. Update this section as your team encounters LLM judge mistakes.*

**Template entry format:**
- **`[pattern]`**: [Why it looks wrong] — [Why it's actually correct]

**Example:**
- **`gt(createdAt)` + `ORDER BY DESC`**: This is correct for forward cursor-based pagination. When ordering newest-first (DESC), paginating forward means fetching items *newer* than the last seen timestamp — `gt` is correct, not `lt`. The LLM judge has been known to flag this pattern incorrectly.

---

### 3. LLM Judge Response

[Paste response here]

---

### 4. Architect's Assessment

_Brief notes on whether the response changes the approval decision. If "No" or "Partially" answers were raised, note whether they are:_
- _Blockers (return to Feature Lead for fixes before COMPLETE)_
- _Backlog items (file as future work, mark COMPLETE now)_

---

### 5. Final Result

- [ ] **PASS** — mark workstream COMPLETE in router
- [ ] **FAIL** — return to Feature Lead with specific feedback items listed below

### Feedback for Feature Lead (if FAIL)

_List specific issues with file:line references where possible._
