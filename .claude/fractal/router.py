#!/usr/bin/env python3
"""
FRACTAL Deterministic Router

Manages deterministic routing for FRACTAL multi-agent sessions.
Reads the blueprint YAML, tracks workstream status in a state file,
and resolves the dependency graph without LLM involvement.

Usage:
    python3 router.py init                                      # Initialize state from blueprint
    python3 router.py next                                      # Get next ready workstreams
    python3 router.py update <workstream_name> <status>         # Update workstream status
    python3 router.py status                                    # Print full state overview
    python3 router.py pulse <path_to_PULSE.md>                  # Check heartbeat for escalation

    # Override blueprint path (avoids editing the BLUEPRINT_PATH constant):
    python3 router.py --blueprint BLUEPRINT-MyEpic.yaml init
    python3 router.py --blueprint BLUEPRINT-MyEpic.yaml next

Statuses: NOT_STARTED | IN_PROGRESS | COMPLETE
"""

import yaml
import json
import sys
import os
import re
from datetime import datetime

# ---------------------------------------------------------------------------
# Configuration — update BLUEPRINT_PATH when switching epics,
# or use --blueprint <filename> on the command line to override.
# ---------------------------------------------------------------------------

BLUEPRINT_PATH = os.path.join(
    os.path.dirname(__file__),
    "BLUEPRINT-{EpicName}.yaml"  # Update for each epic
)
STATE_PATH = os.path.join(os.path.dirname(__file__), ".state.json")


def _resolve_blueprint_path(args):
    """
    Checks for --blueprint flag in args and returns (blueprint_path, remaining_args).
    Falls back to the BLUEPRINT_PATH constant if no flag is provided.
    """
    if "--blueprint" in args:
        idx = args.index("--blueprint")
        if idx + 1 >= len(args):
            print("Error: --blueprint requires a filename argument.")
            sys.exit(1)
        bp_file = args[idx + 1]
        remaining = args[:idx] + args[idx + 2:]
        bp_path = bp_file if os.path.isabs(bp_file) else os.path.join(
            os.path.dirname(__file__), bp_file
        )
        return bp_path, remaining
    return BLUEPRINT_PATH, args


# ---------------------------------------------------------------------------
# Blueprint Parsing
# ---------------------------------------------------------------------------

def load_blueprint(blueprint_path=None):
    """
    Loads the blueprint file and returns the parsed YAML data.

    Handles two formats:
    - Pure .yaml/.yml files: read directly
    - .md files: extract the fenced ```yaml block

    Args:
        blueprint_path: Override path. Falls back to the module-level BLUEPRINT_PATH.

    Returns:
        list[dict]: A list of phases, each containing a list of workstreams.
    """
    path = blueprint_path or BLUEPRINT_PATH
    if path.endswith(('.yaml', '.yml')):
        with open(path, "r") as f:
            content = f.read()
        return yaml.safe_load(content)
    else:
        with open(path, "r") as f:
            for line in f:
                if line.strip() == "```yaml":
                    break
            yaml_content = f.read().strip().replace("```", "")
        return yaml.safe_load(yaml_content)


# ---------------------------------------------------------------------------
# State Management
# ---------------------------------------------------------------------------

def load_state():
    """
    Loads the .state.json file and returns the parsed JSON data.

    Returns:
        dict: A dictionary mapping workstream names to their statuses.
    """
    if not os.path.exists(STATE_PATH):
        return {}
    with open(STATE_PATH, "r") as f:
        return json.load(f)


def save_state(state):
    """
    Saves the given state data to the .state.json file.

    Args:
        state (dict): A dictionary mapping workstream names to their statuses.
    """
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_init(blueprint_path=None):
    """
    Initializes the state file from the blueprint.

    Reads the blueprint file, extracts all workstream names, and creates
    a state file with each workstream set to NOT_STARTED.
    """
    blueprint = load_blueprint(blueprint_path)
    state = {}
    for phase in blueprint:
        for workstream in phase["workstreams"]:
            state[workstream["feature_lead"]] = "NOT_STARTED"
    save_state(state)
    print(f"State initialized with {len(state)} workstreams.")
    for name, status in state.items():
        print(f"  {name}: {status}")


def cmd_next(blueprint_path=None):
    """
    Gets the next workstream(s) that are ready to be executed.

    A workstream is "ready" when:
      1. Its status is NOT_STARTED.
      2. All of its dependencies have a status of COMPLETE.

    Prints the names of all ready workstreams to stdout, one per line.
    """
    blueprint = load_blueprint(blueprint_path)
    state = load_state()
    ready = []

    for phase in blueprint:
        for workstream in phase["workstreams"]:
            name = workstream["feature_lead"]
            if state.get(name) != "NOT_STARTED":
                continue
            deps = workstream.get("dependencies", [])
            if all(state.get(d) == "COMPLETE" for d in deps):
                ready.append((name, workstream.get("model", "sonnet")))

    if ready:
        print("Ready workstreams:")
        for name, model in ready:
            print(f"  -> {name}  [model: {model}]")
    else:
        if all(s == "COMPLETE" for s in state.values()):
            print("ALL WORKSTREAMS COMPLETE. Epic is done.")
        else:
            in_progress = [k for k, v in state.items() if v == "IN_PROGRESS"]
            print("No new workstreams ready. Waiting on:")
            for ws in in_progress:
                print(f"  [IN_PROGRESS] {ws}")


def cmd_update(workstream_name, status):
    """
    Updates the status of a workstream in the state file.

    Args:
        workstream_name (str): The name of the workstream to update.
        status (str): The new status. Must be NOT_STARTED | IN_PROGRESS | COMPLETE.
    """
    state = load_state()
    if workstream_name not in state:
        print(f"Error: Workstream '{workstream_name}' not found in state file.")
        print(f"Available workstreams: {list(state.keys())}")
        sys.exit(1)

    valid_statuses = ["NOT_STARTED", "IN_PROGRESS", "COMPLETE"]
    if status not in valid_statuses:
        print(f"Error: Invalid status '{status}'. Must be one of {valid_statuses}")
        sys.exit(1)

    old_status = state[workstream_name]
    state[workstream_name] = status
    save_state(state)
    print(f"'{workstream_name}': {old_status} -> {status}")


def cmd_status():
    """
    Prints a full overview of the current state of all workstreams,
    organized by status category with progress percentage.
    """
    state = load_state()
    if not state:
        print("No state file found. Run 'python3 router.py init' first.")
        return

    categories = {
        "COMPLETE": [],
        "IN_PROGRESS": [],
        "NOT_STARTED": [],
    }
    for name, status in state.items():
        categories.get(status, categories["NOT_STARTED"]).append(name)

    total = len(state)
    done = len(categories["COMPLETE"])
    progress_pct = (done / total * 100) if total > 0 else 0

    print(f"Epic Progress: {done}/{total} ({progress_pct:.0f}%)")
    print("=" * 50)

    for cat in ["COMPLETE", "IN_PROGRESS", "NOT_STARTED"]:
        items = categories[cat]
        if items:
            print(f"\n[{cat}] ({len(items)})")
            for name in items:
                print(f"  - {name}")


def cmd_pulse(pulse_path):
    """
    Reads a PULSE.md file and checks the most recent entry for escalation.

    Deterministic rule-based check — zero LLM tokens if HEARTBEAT_OK.
    Returns HEARTBEAT_ALERT if escalation_needed is true in the latest entry.

    Args:
        pulse_path (str): The path to the PULSE.md file to check.
    """
    if not os.path.exists(pulse_path):
        print(f"Error: Pulse file not found at '{pulse_path}'")
        sys.exit(1)

    with open(pulse_path, "r") as f:
        content = f.read()

    json_blocks = re.findall(r"```json\s*\n(.*?)\n```", content, re.DOTALL)

    if not json_blocks:
        print("HEARTBEAT_OK (no pulse entries found)")
        return

    try:
        latest = json.loads(json_blocks[-1])
    except json.JSONDecodeError:
        print("HEARTBEAT_ALERT: Could not parse latest pulse entry.")
        return

    status = latest.get("status", "UNKNOWN")
    escalation = latest.get("escalation_needed", False)
    blockers = latest.get("blockers", "none")
    tasks = latest.get("tasks_completed", "unknown")
    timestamp = latest.get("timestamp", "unknown")

    if escalation:
        print(f"HEARTBEAT_ALERT")
        print(f"  Timestamp:  {timestamp}")
        print(f"  Status:     {status}")
        print(f"  Progress:   {tasks}")
        print(f"  Blockers:   {blockers}")
        print(f"  Action:     Escalation required — review with Architect.")
    else:
        print(f"HEARTBEAT_OK")
        print(f"  Timestamp:  {timestamp}")
        print(f"  Status:     {status}")
        print(f"  Progress:   {tasks}")


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    bp_path, args = _resolve_blueprint_path(sys.argv[1:])
    if not args:
        print(__doc__)
        sys.exit(1)

    command = args[0]

    if command == "init":
        cmd_init(bp_path)
    elif command == "next":
        cmd_next(bp_path)
    elif command == "update":
        if len(args) != 3:
            print("Usage: python3 router.py update <workstream_name> <status>")
            sys.exit(1)
        cmd_update(args[1], args[2])
    elif command == "status":
        cmd_status()
    elif command == "pulse":
        if len(args) != 2:
            print("Usage: python3 router.py pulse <path_to_PULSE.md>")
            sys.exit(1)
        cmd_pulse(args[1])
    else:
        print(f"Error: Unknown command '{command}'")
        print(__doc__)
        sys.exit(1)
