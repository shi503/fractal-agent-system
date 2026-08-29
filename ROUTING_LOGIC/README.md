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

The router accepts **two blueprint shapes**:

- **Phased** — a top-level YAML *list* of phases, each with a `workstreams:` list using `feature_lead:` and `dependencies:` keys.
- **Flat** — a single top-level mapping with a `workstreams:` list using `id:`/`name:` and `depends_on:` keys.

`_normalize_blueprint()` in `router.py` coerces either shape into a canonical list-of-phases form before the rest of the router touches it, so `init`/`next`/`update` work identically regardless of which shape an epic's BLUEPRINT file uses. See `fixtures/taskflow/blueprints/` for one worked example of each shape.

A `.yaml`/`.yml` file is read directly; a `.md` file has its fenced ```` ```yaml ```` block extracted and parsed.

See `../SETUP-CLAUDE-CODE.md` §7 for the full blueprint authoring rules.

## Configuration

`router.py` resolves paths without hardcoding a location:

```python
ROUTER_VERSION = "2.0.0"
BLUEPRINT_PATH  # defaults to fixtures/taskflow/blueprints/BLUEPRINT-NOVA-P1-NotificationCore.yaml
                # at the repo root, found by walking up from this file to the nearest `.git`
STATE_PATH      # .state.json next to this script
```

Override the default per-invocation with `--blueprint <path>` instead of editing the constant — a relative path resolves first against the current working directory, then this script's directory, then the repo root:

```bash
python3 ROUTING_LOGIC/router.py --blueprint fixtures/taskflow/blueprints/BLUEPRINT-NOVA-P3-Hardening.yaml init
```

The `.state.json` file is a runtime artifact — it is gitignored.

## Canonical copy + identity check

`ROUTING_LOGIC/router.py` is the canonical source. `.claude/fractal/router.py` is a synced copy kept byte-identical to it — see `tools/check-router-identity.sh`. Edit the `ROUTING_LOGIC/` copy and re-sync the `.claude/fractal/` copy; never edit them independently.

## Smoke test

`tools/router-smoke.sh` exercises `init`/`next`/`update`/`status`/`pulse` end-to-end against the fixture blueprint, using a throwaway state file so it never touches `.claude/fractal/.state.json`.
