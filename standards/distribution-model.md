# Distribution & Storage Model

> Answers one question: where does a reference artifact live, and how does it reach a workstream that needs it? Companion doc: `standards/project-maintenance-model.md` (how artifacts are authored, inherited, reviewed, and kept fresh).

## The storage tiers

| Tier | Home | Holds | How it propagates |
|---|---|---|---|
| **Canonical (static)** | `standards/` | Framework-agnostic engineering standards — `engineering-principles.md`, `architecture-patterns.md`, the PR-review finding-class guides | Source of truth. Everything downstream references it by path or by name; it changes deliberately, by review, not by an automated pass. |
| **Compounding (dynamic)** | project-chosen, e.g. a findings log next to the review skill that grows it | Recurring finding-classes discovered during review, "what good looks like" write-ups | Read and appended to by the review tooling that produces it. A finding-class that keeps recurring is a candidate for promotion into the canonical tier — see below. |
| **Project references** | `.claude/fractal/intake/`, or a project's own `docs/references/` | Guides that **inherit the canonical tier and add project-specific context** — a stack-specific checklist, a domain glossary | Opens with a pointer up to the canonical guide it inherits from, then adds only what's specific to this project. |
| **Local / per-contributor** | gitignored scratch (an intake folder, a personal notes file) | Personal experiments, in-progress drafts, notes that aren't ready for review | Never propagates automatically. Promote deliberately, by opening a PR, when something here is ready to be shared. |

**Static vs. dynamic, canonical tier:** `standards/` is authored canon — it changes by review, not by every pass of automated tooling. A compounding findings log (if a project keeps one) is living memory: every review pass may append to it. They are counterparts, not duplicates. A recurring entry in the dynamic tier that hardens into a rule gets promoted *into* the canonical tier as a deliberate edit.

## The distribution rule — never hard-depend on another project's paths

A guide, skill, or agent definition that is meant to run outside the repo it was authored in — vendored into a sibling project, installed from a template, copied by a script — must never assume the *authoring* repo's paths exist on disk in the *target* repo. Concretely:

1. **A portable artifact never hard-depends on a path from the repo it came from.** It inlines what it needs (its own body, or a `references/` folder that travels with it) and **cites** any canonical guide *by name* ("the project's engineering-principles standard"), not by a relative link that only resolves in the repo that authored it.
2. **The canonical guide is the source; a copy carried into another repo is operational.** Keeping the two in sync is a deliberate maintenance step (a freshness pass — see `project-maintenance-model.md`), not something that happens by a live filesystem link.
3. **Links within one repo may be relative and direct.** A project-reference guide inside this repo linking to `standards/engineering-principles.md` is fine — that link never has to survive being copied elsewhere.

The failure mode this rule exists to prevent: an artifact that says "see `standards/X.md`" ships into a project that has no `standards/` directory at all, and the reference silently resolves to nothing. Test any artifact intended to travel by asking: does this reference still make sense if `standards/` from this repo isn't there?

## How a canonical guide reaches somewhere that isn't this repo

There are exactly two channels, and they carry different things:

| Channel | Mechanism | Carries |
|---|---|---|
| **Walk-up read** | A session in another project reads its own local config, then climbs to shared, repo-level conventions if the tooling supports it | Org-level context only — naming conventions, pointers to where things live. Not the full guide body. |
| **Packaged install** | A self-contained plugin, template, or package that bundles the content it needs | The guide's *content*, inlined or bundled as `references/`, so it works with zero assumption about the installing repo's layout. |

`standards/` itself is reachable by neither channel from outside this repo — it is canonical to this repo. Its *content* reaches another repo only by being deliberately inlined into something portable, never by the file traveling on its own.

## Status

This is a living document. Update it in the same PR that changes how the tiers are organized — don't let the description drift from what the repository actually does.
