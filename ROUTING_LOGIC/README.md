_This file is machine-readable. Do not edit manually._

# Deterministic Routing Logic

This directory contains the code for the deterministic routing logic that the Architect agent uses to orchestrate the multi-agent workflow. The logic is implemented as a Python script that reads a BLUEPRINT file and determines which workstreams are ready to be executed based on their dependencies.

## How It Works

1. **State Management:** The script maintains a state file (`.state.json`) that tracks the status of each workstream (`NOT_STARTED`, `IN_PROGRESS`, `COMPLETE`).
2. **Blueprint Parsing:** The script parses the BLUEPRINT `.yaml` file (or a `.md` with a fenced `yaml` block) to understand the phases, workstreams, and their dependencies.
3. **Dependency Resolution:** For each workstream, the script checks if all of its dependencies have been marked as `COMPLETE` in the state file.
4. **Next Action Identification:** The script identifies the next workstream(s) that are ready to be executed and prints their names and model tiers to standard output.
5. **State Updates:** The script provides functions to update the state of a workstream.

## Commands

```bash
# Initialize state from BLUEPRINT file (run once at epic start)
python3 router.py init

# Show ready workstreams (dependencies met, NOT_STARTED)
python3 router.py next

# Update workstream status
python3 router.py update <workstream_name> <NOT_STARTED|IN_PROGRESS|COMPLETE>

# Show full epic progress overview (N/M complete, by status group)
python3 router.py status

# Check a PULSE.md file for escalation flags
python3 router.py pulse <path/to/PULSE.md>
```

## BLUEPRINT Format

Use a **pure `.yaml` file** (recommended). The file must be a **top-level list** — do NOT wrap in a `phases:` key.

See `../SETUP-CLAUDE-CODE.md` §7 for the full blueprint format and authoring rules.

## Configuration

At the top of `router.py`, update these two constants for each epic:

```python
BLUEPRINT_PATH = os.path.join(os.path.dirname(__file__), "BLUEPRINT-{EpicName}.yaml")
STATE_PATH     = os.path.join(os.path.dirname(__file__), ".state.json")
```

The `.state.json` file is a runtime artifact — add it to `.gitignore`.
