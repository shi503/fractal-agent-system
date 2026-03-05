---
name: handoff
description: "Generate HANDOFF.md for a completed Feature Lead workstream, run the eval gate, and update router state"
argument-hint: "[FeatureLead name, e.g. FeatureLead-PreferencesUI]"
---

# Handoff — Feature Lead Completion (Cursor)

You are completing a Feature Lead workstream. The argument is the Feature Lead name (e.g. `FeatureLead-PreferencesUI`).

**CRITICAL:** Do not generate the HANDOFF or mark COMPLETE if the build gate fails.

## Steps

### Step 1: Run deterministic eval gate

Run your project's build and typecheck (e.g. `npm run build`, `npx tsc --noEmit`). If build fails: stop, report errors, fix, re-run. Do not proceed to Step 2 until clean.

### Step 2: Generate HANDOFF.md

Path from FeatureLead name: `FeatureLead-PreferencesUI` → `.fractal/workstreams/preferences-ui/HANDOFF.md`

Structure:
- **Completed**, **Blueprint**, **Workstream PRD**
- **Summary of Work Completed** (file paths, function names)
- **Summary of Work Not Completed** (honest)
- **Technical Debt**
- **Key Decisions**
- **Deterministic Eval** (build: PASS/FAIL, typecheck: PASS/FAIL or N/A)

### Step 3: Update router state

```bash
python3 .fractal/router.py update <FeatureLeadName> COMPLETE
```

### Step 4: Display next ready workstreams

```bash
python3 .fractal/router.py next
```

If all COMPLETE, print: "Epic complete — review all HANDOFF.md files before closing."

### Step 5: Remind

"Review `.fractal/workstreams/<name>/HANDOFF.md` before accepting. Verify acceptance criteria before marking the phase complete."
