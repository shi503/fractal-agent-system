---
name: fractal-maintenance
description: "Cut a release archive and lint the FRACTAL tree. Moves completed workstreams and their blueprint into _archive/r{NN}-{slug}/, writes a MANIFEST, and reports layout violations. Dry-run by default; pass --apply to execute. Use when the user asks to cut a release, archive completed workstreams, or lint the FRACTAL directory layout."
argument-hint: "[release-slug] [--apply]"
disable-model-invocation: true
---

# FRACTAL Maintenance — Release Cut + Layout Lint

Invoked at release-cut time, or any time the tree may have drifted. Always read-only unless `--apply` is passed.

## Arguments

```
/fractal-maintenance <release-slug> [--apply]
```

- **`<release-slug>`** — optional. If provided, stages an archive cut under `_archive/r{NN}-{slug}/` where `{NN}` is the next unused release number (inspect existing `_archive/r*` folders to infer). If omitted, only layout lint runs.
- **`--apply`** — execute moves / writes. Without it, everything is printed as a dry-run.

## What this skill does

### Step 1 — Read the harness state

Always run first, regardless of mode:

```bash
python3 .claude/fractal/router.py status
ls .claude/fractal/blueprints/ 2>/dev/null
ls -d .claude/fractal/workstreams/*/ 2>/dev/null
ls -d .claude/fractal/_archive/*/ 2>/dev/null
grep -c "^| " .claude/fractal/ISSUES.md 2>/dev/null  # rough issue count
```

Capture: active blueprint name, COMPLETE workstreams, OPEN ISSUES count.

### Step 2 — Layout lint (always)

Emit a report listing any of these violations. Do NOT fix automatically — the Architect reviews first.

1. **Stray PRDs at `workstreams/` root** — any `.md` file directly under `workstreams/` (not inside a subfolder). Correct shape: `workstreams/{kebab}/prd-{kebab}.md`.
2. **Stray BLUEPRINTs at fractal root** — any `BLUEPRINT-*.yaml` at `.claude/fractal/` (not in `blueprints/`, when that subdirectory convention is in use).
3. **Workstream folder missing `prd-*.md`** — any folder under `workstreams/` that lacks its PRD (HANDOFF-only is a smell unless this is archived).
4. **Workstream folder with misnamed PRD** — PRD present but not named `prd-{folder-kebab}.md`.
5. **Case-variant duplicate folders** — two folders whose names match case-insensitively (e.g. `doc-review-x` + `doc-Review-x`).
6. **Tracked `PULSE.md`** — `git ls-files '.claude/fractal/workstreams/**/PULSE.md'` must return zero lines. PULSE is gitignored by convention.
7. **Archive path drift** — any `_archive/` content directly at `_archive/blueprints/` or `_archive/workstreams/` (not inside an `r{NN}-{slug}/` bucket).
8. **Template drift** — for each `workstreams/{kebab}/prd-{kebab}.md`, diff its section headers against `.claude/fractal/templates/prd-template.md` (canonical templates location). Warn on missing required sections (Feature Overview, Acceptance Criteria, File Manifest, CI Gate, Session Protocol, Out of Scope, Blockers).

Output format:

```
FRACTAL layout lint — {YYYY-MM-DD}

✅ PASS (N checks)
⚠️  WARN (M findings)
❌ FAIL (K findings)

<details per finding with file paths>
```

### Step 3 — Archive cut (only if `<release-slug>` provided)

Given a slug (e.g. `v1-handoff`), propose this plan as a dry-run:

1. Determine next release number: `N = max(existing _archive/r{NN}-* numbers) + 1` (pad to 2 digits).
2. Identify archivable workstreams — any folder under `workstreams/` whose:
   - `HANDOFF.md` exists AND passes the Layer-1 CI gate per the HANDOFF's Verification Evidence table, AND
   - Its workstream ID is in the active BLUEPRINT (or the BLUEPRINT is COMPLETE).
3. Identify the BLUEPRINT to archive — the currently ACTIVE one if all its workstreams are COMPLETE.
4. Plan the moves:
   ```
   git mv .claude/fractal/blueprints/BLUEPRINT-{active}.yaml \
     .claude/fractal/_archive/r{NN}-{slug}/blueprints/
   for each archivable workstream:
     git mv .claude/fractal/workstreams/{kebab}/ \
       .claude/fractal/_archive/r{NN}-{slug}/workstreams/{kebab}/
   ```
5. Generate `_archive/r{NN}-{slug}/MANIFEST.md` with: cut date, cut-by, blueprint name, workstream list (with HANDOFF presence), commit SHA placeholder.

**Never archive a workstream that is still NOT_STARTED or IN_PROGRESS.** If the active BLUEPRINT has any non-COMPLETE workstreams, refuse to cut and report why.

**Never mutate `ISSUES.md`.** It is the append-only audit trail and never moves into an archive.

### Step 4 — ISSUES.md summary

Read-only. Report:
- Count of `Status: OPEN` issues.
- Count of `Status: RESOLVED` issues.
- Any `CRITICAL` + `OPEN` combination — these must be addressed as workstreams in the next BLUEPRINT or explicitly deferred with a reason in that BLUEPRINT's `notes:` field.

### Step 5 — Apply (only if `--apply` present)

If `--apply` is passed and the dry-run plan has no blockers (no FAIL findings in Step 2, no in-flight workstreams in Step 3's planned archive), execute:

1. Create target directories.
2. `git mv` the files per the plan.
3. Write `MANIFEST.md` at the archive root.
4. Run layout lint a second time to confirm the tree is clean post-move.
5. Report to the user: what moved, final tree shape, next suggested step (commit + tag).

**Do NOT commit.** The user owns the commit. The skill leaves everything staged in the working tree.

## Example invocations

```
# Lint only — always safe
/fractal-maintenance

# Plan an archive cut for the 'v1-handoff' release — dry-run
/fractal-maintenance v1-handoff

# Execute the cut (after reviewing the dry-run plan)
/fractal-maintenance v1-handoff --apply
```

## What this skill never does

- Deletes files.
- Modifies `ISSUES.md`, `STRATEGIST-*.md`, agent definitions, or the `router.py` state file.
- Auto-commits. The user reviews the diff and commits.
- Re-runs a build or CI gate. It trusts the HANDOFF's recorded evidence (which was verified by the Architect at workstream completion).

## Gotchas

- Step 2's checks are advisory only — this skill never auto-fixes layout violations, even obvious ones. The Architect decides what to correct.
- Archive numbering (`r{NN}`) depends on scanning existing `_archive/r*` folders; if none exist yet, the first cut is `r01`.
- `--apply` still leaves the working tree unstaged for commit — the skill never runs `git commit`.
