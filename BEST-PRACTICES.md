# FRACTAL Best Practices & Lessons Learned

*Captured from a production pilot running FRACTAL end-to-end on an Angular/TypeScript SaaS project. These are concrete findings — not theory.*

---

## 1. BLUEPRINTs

**Use pure `.yaml` files, not `.md` fenced blocks.**
The original router only supported `.md` blueprints with a fenced `yaml` block. Pure `.yaml` support was added during the pilot because it's cleaner, easier to validate, and avoids parse errors when the YAML is malformed inside a markdown document. Always create `BLUEPRINT-{EpicName}.yaml` as a standalone file.

**Top-level list, never a dict wrapper.**
The most common rookie mistake: wrapping the blueprint in a `phases:` key. The router iterates the list directly and throws `TypeError: string indices must be integers` on a dict wrapper. Every BLUEPRINT must start with `- name:` at the root level.

**Most workstreams should have `dependencies: []`.**
The value of the dependency graph is identifying what can run in parallel, not creating artificial sequences. In a well-decomposed epic, the majority of workstreams have no hard dependencies. Reserve `dependencies:` for true sequential constraints (e.g., a UI workstream that consumes an API contract that doesn't exist yet).

**Model tier assignments matter.**
- `haiku`: pure text transforms, simple SQL with no framework code — nothing else
- `sonnet`: everything that touches typed TypeScript, Angular, React, or any framework
- `opus`: Architect role only — BLUEPRINT authoring, HANDOFF evaluation, strategic decisions

The pilot upgraded Sub-Agents from `haiku` to `sonnet` mid-flight. Haiku hallucinates on typed framework code (e.g. signals, computed properties, generics). Don't use haiku for framework code.

---

## 2. Workstream PRDs

**The PRD is the only context a Feature Lead gets.** It starts fresh with no memory of previous sessions. If the PRD is ambiguous, the work will be ambiguous. Write each PRD as if the reader has never seen the codebase.

**File manifests must be exhaustive.** If a file isn't in the read manifest, the Feature Lead won't read it. If it's not in the write manifest, the Feature Lead shouldn't touch it. Missing a read-only context file is the most common cause of Feature Lead mistakes.

**Acceptance criteria must be binary.** "Improve UX" is not a criterion. "Badge shows count 1–99, then 99+ above that limit" is. Every criterion must be provably pass/fail from the HANDOFF.md.

**Reference guides by path, never paste inline.** Guide content pasted into PRDs bloats the context window without adding value — the Feature Lead can read the guide directly. Only reference guides that are genuinely relevant to the workstream type.

**Context section explains WHY, not just WHAT.** "Add a guard to the markRead method" is not sufficient context. "The markRead optimistic decrement doesn't check if the item was already read, causing the badge count to go negative on double-click" gives the Feature Lead the information needed to write the correct guard.

---

## 3. Evaluation Pipeline

**Layer 2 produces false positives — document them.** The LLM judge incorrectly flagged `gt(createdAt)` + `ORDER BY DESC` as a pagination bug during the pilot. This is correct for forward cursor-based pagination (you're fetching items *newer* than the cursor in descending order). The fix: maintain a "Known False Positives" section in your `llm-judgment-eval.md` template. Every time the judge makes a mistake, document the pattern so future evaluations skip it.

**Add Q6 and Q7 to your Layer 2 prompt.** The default Layer 2 template misses architectural inconsistencies. The pilot missed that a static upgrade banner coexisted with a new notification system (two parallel upgrade channels). Q6 catches this: "Is there any inconsistency between this workstream and existing UI/architectural patterns in the codebase?" Q7 forces concrete remediation: "State the exact file, function, and change required" — not vague descriptions.

**Each evaluation layer must produce differentiated output.** If two layers say the same things, one is redundant. The 4-layer pipeline only works when:
- Layer 1 (deterministic) catches build/lint/security failures that the LLM would miss
- Layer 2 (LLM) catches architecture smells and intent misalignment that deterministic checks miss
- Layer 3 (persona) catches user-experience gaps that neither code-level review would surface
- Layer 4 (strategic) asks "are we building the right thing?" — a question the other three don't ask

**Qualitative layers (3-4) must NOT block shipping.** They inform the backlog. The eval pipeline stalls if persona feedback blocks individual workstreams. Only escalate Layer 3/4 findings as blockers if they violate a core guiding principle (e.g., provenance is non-functional, PHI is exposed).

---

## 4. The Router

**Always use `.yaml` blueprints.** The router's `.md` support (extracting fenced blocks) is a legacy compatibility path. Use standalone `.yaml` files for all new epics.

**`router.py update COMPLETE` without `/handoff` produces no audit trail.** Marking a workstream COMPLETE by calling the router directly bypasses the HANDOFF generation. You end up with a state file that says "COMPLETE" but no record of what was built, what wasn't, or whether the build passed. Always go through the `/handoff` skill for workstream completion.

**`router.py status` is your dashboard.** Run it after every state change to see the full epic progress. It shows completed/in-progress/not-started groupings and the overall N/M percentage.

**Mark `IN_PROGRESS` before starting, COMPLETE only after HANDOFF accepted.** The state file is the ground truth for parallel orchestration. If you start work without marking IN_PROGRESS, you risk another session starting the same workstream. If you mark COMPLETE before reviewing the HANDOFF, you lose the review gate.

**`.state.json` is a runtime artifact — gitignore it.** It will conflict across branches. Add `.claude/FRACTAL/.state.json` to `.gitignore` before the first commit.

---

## 5. Model Tiers

**Sub-Agents need Sonnet for typed code.** Haiku reliably hallucinates on TypeScript generics, Angular 21 signal patterns (`computed()`, `input.required<T>()`), and framework-specific decorators. The cost saving is not worth the hallucination rate. Use Sonnet for all code-writing tasks.

**Context window (200K vs 1M) is set by your plan, not the `model` field.** The `model: sonnet` in an agent's frontmatter specifies which model family to use. Whether it runs with 200K or 1M context depends on your Claude Code subscription tier. If your plan includes 1M context, Sonnet and Opus agents benefit automatically.

**Opus for Architect-only decisions.** Opus's value is strategic reasoning, dependency graph analysis, and HANDOFF evaluation — not speed. Don't use Opus for Feature Lead workstreams. The latency is noticeable and the additional quality over Sonnet isn't worth it for implementation tasks.

---

## 6. PULSE and HANDOFF Artifacts

**No PULSE artifacts = no escalation trail.** If Feature Leads complete work without emitting PULSE heartbeats, you have no record of what happened during execution, where blockers occurred, or whether the 2-attempt retry policy was applied. PULSE is cheap — require it for any workstream taking more than 30 minutes.

**Interactive sessions have no audit trail.** Running the FRACTAL pipeline yourself (evaluating workstreams, marking state) is not the same as running it through agents. Interactive sessions produce no PULSE.md, no HANDOFF.md, and no escalation chain artifacts. Use agents for real work. The conversation history is the only trail for interactive sessions.

**HANDOFF.md must include build gate results.** A HANDOFF without build evidence is opinion, not evidence. The template includes a §5 Deterministic Eval section. Require Feature Leads to fill it in. A HANDOFF that says "ng build: PASS" is substantially more trustworthy than one that says "all acceptance criteria met."

**Stray HANDOFF.md files are runtime artifacts — don't commit them.** The correct path for a HANDOFF is `.claude/FRACTAL/workstreams/{kebab-name}/HANDOFF.md`. Files that land at `.claude/FRACTAL/HANDOFF.md` (missing the workstream subdirectory) are stray artifacts. Add `.claude/FRACTAL/workstreams/*/HANDOFF.md` and `.claude/FRACTAL/workstreams/*/PULSE.md` to `.gitignore`.

---

## 7. Source Control

**Capture commit/PR preferences in the Strategist doc before starting an epic.** Without documented preferences, each session independently decides when to commit. This produces either no commits (all work uncommitted at session end) or too many commits (every file save committed). The Strategist's §9 Source Control Preferences section resolves this once and stores the decision where the Architect reads it.

**Per-phase commits keep git history coherent with BLUEPRINT structure.** When a git commit maps to a BLUEPRINT phase, the history is self-documenting: "feat: Phase 1 — Database + API workstreams complete." Reviewers can understand the git log without reading the internal FRACTAL artifacts.

**Never commit with a failing build.** The Architect's epic wrap-up protocol includes a hard rule: if `ng build` (or your project's equivalent) is failing, do not create a commit. Surface the failure and block. A failing-build commit creates confusion about whether the codebase was ever clean.

---

## 8. Anti-Patterns to Avoid

| Anti-Pattern | Why It's Harmful | Correct Approach |
|---|---|---|
| Skip `/handoff`, use `router.py update COMPLETE` directly | No HANDOFF.md — no audit trail, no build gate evidence | Always use `/handoff` skill for workstream completion |
| Run FRACTAL pipeline interactively in conversation | No PULSE/HANDOFF artifacts, conversation history is the only trail | Use Feature Lead agents for real implementation work |
| Hardcode epic-specific references in general-purpose skills | Misleads future epics (e.g., `PRD-017-03` in `handoff/SKILL.md`) | Skills must be generic; epic context lives in workstream PRDs |
| Keep duplicate `router.py` in multiple locations | They diverge independently — the canonical source falls behind the working version | One canonical source (`ROUTING_LOGIC/router.py`), copy to `.claude/FRACTAL/` per the setup guide |
| Make all workstreams sequential | Misses parallelism, epics take 4x longer than necessary | Default `dependencies: []`, add dependencies only for true sequential constraints |
| Paste guide content inline into workstream PRDs | Bloats context window, reduces Feature Lead focus | Reference guides by path only |
| Use haiku for Angular/TypeScript workstreams | Hallucination on typed code, incorrect signal patterns, framework misuse | Sonnet for all code-writing tasks; haiku only for pure text/SQL |
| Mark `COMPLETE` before reviewing HANDOFF | Loses the review gate, tech debt goes unregistered | Review HANDOFF.md, check build gate evidence, then accept |
