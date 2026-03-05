---
name: pulse
description: "Emit a structured heartbeat from the current Feature Lead session and check for escalation"
argument-hint: "[FeatureLead name, e.g. FeatureLead-PreferencesUI]"
---

# Pulse — Feature Lead Heartbeat (Cursor)

You are emitting a heartbeat from the current Feature Lead session. The argument is the Feature Lead name (e.g. `FeatureLead-PreferencesUI`).

## Steps

1. **Collect status** — From the current session state:
   - Tasks complete out of total (e.g. "2/5")
   - Blockers (brief or "none")
   - Escalation needed? (true only if you cannot continue without external input)

2. **Determine pulse file path:**
   Convert FeatureLead name to kebab-case:
   - `FeatureLead-PreferencesUI` → `.fractal/workstreams/preferences-ui/PULSE.md`
   - `FeatureLead-EventWiring-Files` → `.fractal/workstreams/event-wiring-files/PULSE.md`
   Create the directory if it doesn't exist.

3. **Append heartbeat entry** to PULSE.md:
   ```json
   {
     "timestamp": "<ISO-8601>",
     "status": "IN_PROGRESS",
     "tasks_completed": "<N/total>",
     "blockers": "<none or description>",
     "escalation_needed": false
   }
   ```
   Wrap in a markdown code fence.

4. **Run deterministic check:**
   ```bash
   python3 .fractal/router.py pulse <pulse-file-path>
   ```

5. **If HEARTBEAT_ALERT:** Surface the escalation. Stop work. Report the blocker for Architect review.

6. **If HEARTBEAT_OK:** Print a one-line status summary and continue.
