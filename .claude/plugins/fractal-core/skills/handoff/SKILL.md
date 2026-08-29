---
name: handoff
description: "Generate HANDOFF.md for a completed Feature Lead workstream, run the eval gate, and update router state. Use when the user asks to hand off a workstream, close out a Feature Lead session, or mark a workstream complete."
argument-hint: "[FeatureLead name, e.g. FeatureLead-PreferencesUI]"
disable-model-invocation: true
---

# Handoff — Feature Lead Completion

You are completing a Feature Lead workstream. The argument is the Feature Lead name (e.g. `FeatureLead-PreferencesUI`).

When the Feature Lead runs as a background agent, they use the bash steps in `feature-lead.md` instead of this skill; this skill runs when the Feature Lead is in an interactive Claude Code session.

**CRITICAL:** Do not generate the HANDOFF or mark COMPLETE if the build gate fails.

## Steps

### Step 1: Run Quality Pass

Before the eval gate, run `/quality-pass` to catch AI slop introduced during implementation:

```bash
git diff HEAD
```

Review output for: excessive comments, unsafe type casts, missing error handling conventions, hardcoded config, `console.log`/`print()` left in, files over 300 lines. Fix what you find. Record the result in the Verification Evidence table.

### Step 2: Run Deterministic Eval Gate

Run your project's build and typecheck commands. Examples (customize for your stack):

- **Frontend only:** the project's build command — then a standalone typecheck pass if the language supports one
- **Backend only:** the project's build/typecheck command
- **Full stack:** run both frontend and backend checks

```bash
# Example (replace with your project's commands):
# npm run build 2>&1 | tail -30
# npx tsc --noEmit 2>&1 | tail -20
```

**If build fails:** Stop. Report the errors. Fix them. Re-run. Do not proceed to Step 3 until the build is clean.

### Step 3: Generate HANDOFF.md

Determine the output path from the FeatureLead name:
- `FeatureLead-PreferencesUI` → `.claude/fractal/workstreams/preferences-ui/HANDOFF.md`

Write the HANDOFF.md with this structure:

```markdown
# HANDOFF — <FeatureLead Name>

**Completed:** <ISO date>
**Blueprint:** <blueprint filename>
**Workstream PRD:** <workstream PRD path>

## Summary of Work Completed

- [Specific outcomes: file paths, function names, line numbers where relevant]

## Summary of Work Not Completed

- [Anything in the PRD acceptance criteria that was not done, with honest reason]
- [Or: "All acceptance criteria met"]

## Technical Debt

- [Any shortcuts, TODOs left in code, workarounds]
- [Or: "None"]

## Key Decisions

- [Any deviations from the PRD, with rationale]
- [Or: "Implemented as specified"]

## Verification Evidence

| Gate | Command | Result | Notes |
|------|---------|--------|-------|
| Quality pass | `/quality-pass` | PASS / SKIP | [slop items removed, if any] |
| Build | `[project build command]` | PASS / FAIL | |
| Typecheck | `[project typecheck command]` | PASS / FAIL / N/A | |
| Backend build/typecheck | `[project backend command]` | PASS / FAIL / N/A | |
| Tests | `[project test command]` | PASS (X/Y) / FAIL / N/A | [new specs added, if any] |
| Secrets scan | `grep -rn 'password\|api_key\|token'` | PASS / FAIL | |
```

### Step 4: Update Router State

```bash
python3 .claude/fractal/router.py update <FeatureLeadName> COMPLETE
```

### Step 5: Display Next Ready Workstreams

```bash
python3 .claude/fractal/router.py next
```

Print the output. If all workstreams are COMPLETE, print: "Epic complete — review all HANDOFF.md files before closing."

### Step 6: Remind

"Review `.claude/fractal/workstreams/<name>/HANDOFF.md` before accepting. Verify all acceptance criteria are checked off before marking the epic phase complete."

## Gotchas

- The build gate is a hard stop — never write the HANDOFF or run Step 4 if Step 2 fails. A HANDOFF with a failing gate is worse than no HANDOFF.
- Router `update ... COMPLETE` is idempotent per workstream but does not itself validate the HANDOFF content — that review is the Architect's job, not this skill's.
