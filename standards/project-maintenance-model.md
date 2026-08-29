# Project Maintenance Model

> How this project authors, inherits, reviews, and refreshes the guides that keep the codebase healthy. Companion doc: `standards/distribution-model.md` (where artifacts live and how they propagate). Principle throughout: one concern per guide, one phase per skill or agent role — don't build guides that try to do everything.

## 1. Three phases, kept separate

Writing code, reviewing code, and simplifying code after it works are **distinct phases**. A single guide must not try to span more than one — that produces a bloated document nobody reads end to end and nobody can apply consistently.

| Phase | Concern | Posture |
|---|---|---|
| **Development** | Write the feature | Author produces code against `standards/engineering-principles.md` and `standards/architecture-patterns.md` |
| **Review** | Find defects | A reviewer (human or agent) checks a diff against the same standards plus `standards/pr-review-guides/` |
| **Simplification** | Reduce complexity once it's correct | A separate pass, after the diff already works, focused only on clarity and redundancy |

A backend PR-review guide reviews backend diffs. It does not also teach how to write the backend framework in question, and it does not also teach how to simplify code after the fact — those belong to the other two phases.

## 2. Guide inheritance contract

```
standards/                                  ← canonical tier: universal, framework-agnostic
  └── <project>/references/ (if present)    ← project tier: inherits the canonical tier, adds project context
        └── <sub-app>/references/ (if any)  ← app tier: inherits the project tier, adds app specifics
```

1. **Reference, never copy.** A lower tier opens with a pointer up to what it inherits, then adds only what's specific to it. A universal rule lives once, at the top of the chain — not restated with drift at every level.
2. **Tighten, never contradict.** A lower tier may add a stricter check on top of a canonical rule. It may never override or weaken one. If a canonical rule is actually wrong, the fix happens in `standards/` itself, not by a lower tier quietly disagreeing with it.
3. **Worked example:** a project-specific PR-review guide for this stack would open with "inherits `standards/engineering-principles.md` and `standards/architecture-patterns.md`" and then add only what's specific to this project's domain — e.g. a checklist entry for the `teamId` scoping pattern used across every repository in `lib/repositories/`.

## 3. Intake for a contributed guide or finding

The repeatable flow for bringing an externally contributed guide, or a recurring review finding, into the canonical tier:

1. **Stage it separately first.** Land the raw contribution somewhere it can be read without being treated as canon yet — a draft location, or simply an unmerged PR. Don't merge straight into `standards/`.
2. **Separate substance from form.** The content is usually worth keeping; the placement or packaging is usually what needs to change (wrong tier, wrong path assumptions, stale spec conventions).
3. **Split by altitude.** Content that's true regardless of project or stack goes to the canonical tier. Content specific to this project's domain goes to the project-reference tier. Personal or experimental material stays local and does not graduate yet.
4. **Freshness pass (§4)** — bring the guide to current convention before it graduates, so a stale pattern never gets propagated as if it were current guidance.
5. **Place it.** Move the content to its actual tier's home; add the inheritance pointer if it's a project-tier guide; fix any internal links so they point at the new location.
6. **Reconcile, don't duplicate.** Fold the content into an existing guide covering the same topic rather than adding a second, parallel one that will drift out of sync with the first.
7. **Close the loop.** Record where each piece of the contribution landed, so the person who wrote it (or the next contributor) can see the disposition and follow the same shape next time.

## 4. The freshness pass

Every guide this project authors or touches is brought to current convention *before it graduates into the canonical tier*, so a stale pattern is never propagated as if it were still recommended practice. Minimum checklist:

- The guide states what it covers and, for a project-tier guide, what canonical guide it inherits from — explicitly, at the top.
- Any code example in the guide actually reflects the current stack (framework version, library choice) — not a pattern from a prior stack that was since replaced.
- The guide is scoped to one phase (§1) — it does not silently expand into teaching a different phase's concerns.
- Cross-references to other guides use a stable path or a stable name, not a description that could match more than one file.
- A guide meant to travel outside this repo cites the canonical tier by name, per the distribution rule in `standards/distribution-model.md` — it does not hard-link a path that assumes this repo's layout.

This is required before a guide graduates into `standards/`, and it's a periodic sweep target too — re-run it across the existing guide set whenever the stack's conventions move (a major framework upgrade, a new lint rule set) so the canonical tier doesn't quietly go stale underneath everyone relying on it.
