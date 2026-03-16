---
name: fractal-init
description: "Bootstrap a FRACTAL epic session — verify router.py, initialize state, display ready workstreams"
argument-hint: "[blueprint filename, e.g. BLUEPRINT-MyEpic.yaml]"
disable-model-invocation: true
---

# FRACTAL Init

You are bootstrapping a new FRACTAL epic session. The argument is the blueprint filename (located in `.claude/fractal/`).

## Steps

1. **Verify infrastructure:**
   ```bash
   ls .claude/fractal/router.py
   ls .claude/fractal/$ARGUMENTS
   ```
   If either is missing, stop and report the missing file.

2. **Initialize state:**
   ```bash
   python3 .claude/fractal/router.py init
   ```
   Display the full output.

3. **Display ready workstreams:**
   ```bash
   python3 .claude/fractal/router.py next
   ```
   Display the full output including model tier for each workstream.

4. **Print session brief:**
   - Epic name (from blueprint filename)
   - Total workstream count
   - Which workstreams can run in parallel (no dependencies)
   - Which are blocked (have dependencies)
   - Recommended next step: "Start with workstream X using the feature-lead agent"

5. **Remind:**
   Before starting each workstream, run:
   ```bash
   python3 .claude/fractal/router.py update <FeatureLeadName> IN_PROGRESS
   ```
   After HANDOFF accepted, run:
   ```bash
   python3 .claude/fractal/router.py update <FeatureLeadName> COMPLETE
   python3 .claude/fractal/router.py next
   ```
