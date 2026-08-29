# FRACTAL Archive

Release-batched history of completed BLUEPRINTs and workstreams.

## Layout

```
_archive/
└── r{NN}-{slug}/
    ├── MANIFEST.md           ← release summary, workstream list, commit SHA
    ├── blueprints/           ← BLUEPRINT-*.yaml that drove this release
    └── workstreams/
        └── {kebab-name}/
            ├── prd-{kebab-name}.md
            └── HANDOFF.md    ← PULSE is not archived (gitignored in life)
```

## Release slug convention

`r{NN}-{slug}`

- **`r{NN}`** — monotonic zero-padded release counter. `r01` is the earliest; each subsequent release cut increments.
- **`{slug}`** — short, descriptive, kebab-case. Either time-based (e.g. `2026-q1`) or theme-based (e.g. `core-data-model`, `auth-and-invites`).

Example: `r01-core-data-model/` — the M1 blueprint + workstreams, archived once M1 closes.

## When to cut a release archive

Cut an archive when:
1. All workstreams in the active BLUEPRINT are COMPLETE.
2. The phase commit has landed on `main` (or the release branch).
3. The next BLUEPRINT is about to become ACTIVE.

Don't cut mid-phase — the archive should reflect a coherent, shipped unit of work.

## Automated maintenance

Run `/fractal-maintenance` (see `.claude/plugins/fractal-core/skills/fractal-maintenance/`) to:
- `git mv` completed workstreams and their blueprint into `_archive/r{NN}-{slug}/`.
- Generate a `MANIFEST.md` with workstream list, dates, and commit SHA.
- Lint the live tree for layout violations (stray PRDs at root, case-variants, missing `prd-*.md` in a folder that has HANDOFF, etc.).

Dry-run by default; pass `--apply` to execute.

## What is **never** archived here

- `ISSUES.md` — append-only, lives at the FRACTAL root across all releases. It is the persistent audit trail for framework errors and handoff mistakes.
- `router.py`, `.state.json`, `templates/`, `EVAL_TEMPLATES/` — harness-level files; they evolve in place.
- `benchmarks/`, `intake/` — reference material (quality anchors, strategist intake staging), where present.
