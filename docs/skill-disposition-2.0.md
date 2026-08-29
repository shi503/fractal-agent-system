# Skill Disposition — 2.0

Disposition of all 18 source tools/runner/pr-review skills against the `fractal-core`,
`fractal-tools`, `fractal-runner`, and `fractal-pr-review` plugin split. `fractal-core`
already ships 8 skills (`fractal-init`, `fractal-maintenance`, `pulse`, `handoff`,
`gap-analysis`, `quality-pass`, `claude-md-audit`, `commit-summarize`) from an earlier
workstream — this table accounts for the remaining source skills and records which ones
are intentionally not duplicated.

| # | Source skill | Disposition | New path / reason |
|---|---------------|--------------|--------------------|
| 1 | `review` | Ported | `.claude/plugins/fractal-tools/skills/review/` — already generic, no changes beyond copy |
| 2 | `explore` | Ported | `.claude/plugins/fractal-tools/skills/explore/` — already generic, no changes beyond copy |
| 3 | `document` | Ported | `.claude/plugins/fractal-tools/skills/document/` — already generic, no changes beyond copy |
| 4 | `deslop` | Ported, genericized | `.claude/plugins/fractal-tools/skills/deslop/` — compliance-framework framing rewritten to generic "sensitive data / security posture" framing; name changed from an internal compliance-branded title to plain "Deslop" |
| 5 | `peer-review` | Ported, sanitized | `.claude/plugins/fractal-tools/skills/peer-review/` — "a different team lead within the company" framing rewritten to generic "a colleague" / "owner of this code" |
| 6 | `create-plan` | Ported, sanitized | `.claude/plugins/fractal-tools/skills/create-plan/` — filing convention generalized so `projects/<project>/` and `wiki/raw/` are presented as examples of an existing convention, not assumed to exist |
| 7 | source repo's setup/onboarding companion skill | Genericized | `.claude/plugins/fractal-tools/skills/fractal-setup/` — phase-detection rewritten against this repo's actual layout (`.claude-plugin/marketplace.json`, `tools/validate-plugins.sh`, `tools/router-smoke.sh`, `fixtures/taskflow/`) in place of the source's product-specific stack/phase model |
| 8 | `create-issue` | Genericized | `.claude/plugins/fractal-tools/skills/create-issue/` — ticketing-CLI filing lane replaced with `gh issue create`; offline fallback still writes to `_INBOX/` |
| 9 | `cb` | Dropped | Team chat/dispatcher onboarding menu hard-coded to one company's specific plugin inventory and onboarding flow — no generic equivalent needed once `fractal-setup` covers onboarding |
| 10 | issue-tracker integration skill | Dropped | Ticketing/issue-tracker integration skill scoped to one company's specific tracker and document-publish integration |
| 11 | `em-pr-review` | Dropped | Full-stack PR reviewer named after and tied to one company's specific frontend/backend stack conventions; superseded here by `pr-assist` + `review` |
| 12 | `claude-md-audit` | Already in `fractal-core` | Not duplicated — landed in an earlier workstream |
| 13 | `commit-summarize` | Already in `fractal-core` | Not duplicated — landed in an earlier workstream |
| 14 | `handoff` | Already in `fractal-core` | Not duplicated — landed in an earlier workstream |
| 15 | `pulse` | Already in `fractal-core` | Not duplicated — landed in an earlier workstream |
| 16 | `quality-pass` | Already in `fractal-core` | Not duplicated — landed in an earlier workstream |
| 17 | `fractal-runner` (runner plugin) | Relocated, sanitized | `.claude/plugins/fractal-runner/skills/fractal-runner/` — absolute machine paths and the source-repo-specific env var name replaced with `FRACTAL_REPOS_ROOT` and repo-relative paths; install-guide re-pathed to the runner already landed at `tools/scheduled-fractal-runner/`; references to a specific pair of sibling product repos replaced with generic `registry.json` target language |
| 18 | `pr-assist` (pr-review-bundle plugin) | Relocated, sanitized | `.claude/plugins/fractal-pr-review/skills/pr-assist/` — compounding-learnings sink repointed from a wiki-substrate path to `standards/pr-review-guides/` (six guides already live there); motivating-case narrative naming specific people/repos removed |

## Summary

- **Ported (as-is or lightly sanitized):** 6 — `review`, `explore`, `document`, `deslop`, `peer-review`, `create-plan`
- **Genericized:** 2 — source setup/onboarding companion → `fractal-setup`, `create-issue`
- **Dropped:** 3 — `cb`, issue-tracker integration skill, `em-pr-review`
- **Already in `fractal-core` (not duplicated):** 5 — `claude-md-audit`, `commit-summarize`, `handoff`, `pulse`, `quality-pass`
- **Relocated:** 2 — `fractal-runner`, `pr-assist`

Total accounted for: 6 + 2 + 3 + 5 + 2 = **18**.
