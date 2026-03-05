---
name: pulse
description: "Emit a structured heartbeat from the current Feature Lead session and check for escalation"
argument-hint: "[FeatureLead name, e.g. FeatureLead-PreferencesUI]"
disable-model-invocation: true
---

# Pulse — Feature Lead Heartbeat

You are emitting a heartbeat from the current Feature Lead session. The argument is the Feature Lead name (e.g. `FeatureLead-PreferencesUI`).

## Steps

1. **Collect status** — Answer these questions from the current session state:
   - How many tasks are complete out of total? (e.g. "2/5")
   - Any blockers? Describe them briefly or say "none"
   - Is escalation needed? (true only if you cannot continue without external input)

2. **Determine pulse file path:**
   Convert the FeatureLead name to kebab-case for the workstream folder:
   - `FeatureLead-PreferencesUI` → `.claude/FRACTAL/workstreams/preferences-ui/PULSE.md`
   - `FeatureLead-EventWiring-FileProcessing` → `.claude/FRACTAL/workstreams/event-wiring-files/PULSE.md`

   Create the directory if it doesn't exist.

3. **Append heartbeat entry** to the PULSE.md file:
   ```json
   {
     "timestamp": "<current ISO-8601 timestamp>",
     "status": "IN_PROGRESS",
     "tasks_completed": "<N/total>",
     "blockers": "<none or description>",
     "escalation_needed": <true|false>
   }
   ```
   Wrap in a markdown code fence (` ```json ... ``` `).

4. **Run deterministic check:**
   ```bash
   python3 .claude/FRACTAL/router.py pulse <pulse-file-path>
   ```

5. **If HEARTBEAT_ALERT:** Surface the escalation immediately. Stop work. Report the blocker to the user for Architect review.

6. **If HEARTBEAT_OK:** Print a one-line status summary and continue working.
