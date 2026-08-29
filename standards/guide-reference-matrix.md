# Guide Reference Matrix

Committed guide-path → applies-to mapping. Agents authoring or reviewing a workstream PRD read this table to decide which guides to cite in a PRD's Context section, and reviewers use it to decide which guides apply to a given diff.

**Contract:** every path in the `Guide` column must exist in this repository. `tools/check-guide-matrix.sh` enforces this — it parses this file and fails loudly if any path is missing. Run it after adding, moving, or renaming any guide.

| Guide | Applies To | Category |
|---|---|---|
| `standards/engineering-principles.md` | Any workstream touching `app/`, `components/`, `lib/`, or `prisma/` | principles |
| `standards/architecture-patterns.md` | Any workstream adding a new API route, service module, port/adapter, or integration | architecture |
| `standards/distribution-model.md` | Any workstream that authors a guide, skill, or template meant to be reused outside this repo | operating-model |
| `standards/project-maintenance-model.md` | Any workstream that adds, promotes, or restructures a guide in `standards/` | operating-model |
| `standards/pr-review-guides/vacuous-test-assertion.md` | Any workstream with changes under `**/*.test.ts` or `**/*.spec.ts` | pr-review |
| `standards/pr-review-guides/silent-exception-swallow.md` | Any workstream with a new or modified `try`/`catch`, `.catch()`, or error boundary | pr-review |
| `standards/pr-review-guides/unstable-idempotency-key.md` | Any workstream adding a request-retry path, a webhook receiver, or a queue consumer | pr-review |
| `standards/pr-review-guides/unbounded-retry.md` | Any workstream adding a retry loop against a network call or external dependency | pr-review |
| `standards/pr-review-guides/mutable-default-argument.md` | Any workstream adding a function default value, module-level constant, or memoized default that could be shared across calls | pr-review |
| `standards/pr-review-guides/missing-authorization-check.md` | Any workstream touching `app/api/` or a Server Action that reads or mutates a team-scoped or user-scoped resource | pr-review |

## How to use this table

- **Authoring a PRD:** match the workstream's write manifest against the `Applies To` column; inject the matched `Guide` paths into the PRD's Context section as read-manifest entries.
- **Reviewing a diff:** match the changed files against `Applies To`; the matched guides are the review checklist for that diff, in addition to any project-tier guide that inherits from them.
- **Adding a new guide:** add a row here in the same PR that adds the file. Run `tools/check-guide-matrix.sh` before committing — a guide that exists but isn't listed here won't be picked up by agents reading this table, and a row pointing at a path that doesn't exist fails the check.
