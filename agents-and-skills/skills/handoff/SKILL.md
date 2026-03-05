---
name: handoff
description: "Generate HANDOFF.md for a completed Feature Lead workstream, run the eval gate, and update router state"
argument-hint: "[FeatureLead name, e.g. FeatureLead-PreferencesUI]"
disable-model-invocation: true
---

# Handoff — Feature Lead Completion

You are completing a Feature Lead workstream. The argument is the Feature Lead name (e.g. `FeatureLead-PreferencesUI`).

**CRITICAL:** Do not generate the HANDOFF or mark COMPLETE if the build gate fails.

## Steps

### Step 1: Run Deterministic Eval Gate

Run your project's build and typecheck commands. Examples (customize for your stack):

- **Frontend only:** `npm run build` or `ng build --configuration development` — then `npx tsc --noEmit` if applicable
- **Backend only:** `cd server && npx tsc --noEmit` or your backend's typecheck/build command
- **Full stack:** Run both frontend and backend checks

```bash
# Example (replace with your project's commands):
# npm run build 2>&1 | tail -30
# npx tsc --noEmit 2>&1 | tail -20
```

**If build fails:** Stop. Report the errors. Fix them. Re-run. Do not proceed to Step 2 until the build is clean.

### Step 2: Generate HANDOFF.md

Determine the output path from the FeatureLead name:
- `FeatureLead-PreferencesUI` → `.claude/FRACTAL/workstreams/preferences-ui/HANDOFF.md`

Write the HANDOFF.md with this structure:

```markdown
# HANDOFF — <FeatureLead Name>

**Completed:** <ISO date>
**Blueprint:** <blueprint filename>
**Workstream PRD:** <workstream PRD path>

## Summary of Work Completed

- [Specific outcomes: file paths, function names, line numbers where relevant]
- [E.g. "Created src/app/components/portal/account/notifications/notifications.ts — 180 lines, OnPush, per-category toggle grid"]

## Summary of Work Not Completed

- [Anything in the PRD acceptance criteria that was not done, with honest reason]
- [Or: "All acceptance criteria met"]

## Technical Debt

- [Any shortcuts, TODOs left in code, workarounds]
- [Or: "None"]

## Key Decisions

- [Any deviations from the PRD, with rationale]
- [Or: "Implemented as specified"]

## Deterministic Eval

- [Primary build command]: **PASS** / **FAIL**
- [Typecheck / secondary check]: **PASS** / **FAIL** / N/A
```

### Step 3: Update Router State

```bash
python3 .claude/FRACTAL/router.py update <FeatureLeadName> COMPLETE
```

### Step 4: Display Next Ready Workstreams

```bash
python3 .claude/FRACTAL/router.py next
```

Print the output. If all workstreams are COMPLETE, print: "Epic complete — review all HANDOFF.md files before closing."

### Step 5: Remind

"Review `.claude/FRACTAL/workstreams/<name>/HANDOFF.md` before accepting. Verify all acceptance criteria are checked off before marking the epic phase complete."
