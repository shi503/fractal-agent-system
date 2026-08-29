#!/usr/bin/env python3
"""
FRACTAL Deterministic Router

Manages deterministic routing for FRACTAL multi-agent sessions.
Reads the blueprint YAML, tracks workstream status in a state file,
and resolves the dependency graph without LLM involvement.

Usage:
    python3 router.py init                              # Initialize state from blueprint
    python3 router.py next                              # Get next ready workstreams
    python3 router.py update <workstream_name> <status> # Update workstream status
    python3 router.py status                            # Print full state overview
    python3 router.py pulse <path_to_PULSE.md>          # Check heartbeat for escalation

    # Override blueprint path without editing BLUEPRINT_PATH.
    # A relative path resolves, in order: against the current working
    # directory, against this script's own directory, then against the
    # repo root (found by walking up from this file to the nearest `.git`).
    python3 router.py --blueprint fixtures/taskflow/blueprints/BLUEPRINT-NOVA-P3-Hardening.yaml init
    python3 router.py --blueprint BLUEPRINT-Example.yaml next

Statuses: NOT_STARTED | IN_PROGRESS | COMPLETE

To switch epics: use --blueprint <path> on the command line,
or update BLUEPRINT_PATH below.
"""

import yaml
import json
import sys
import os
import re
from datetime import datetime

ROUTER_VERSION = "2.0.0"

# ---------------------------------------------------------------------------
# Configuration — use --blueprint <path> on CLI to switch epics,
# or update BLUEPRINT_PATH below as a persistent default.
# ---------------------------------------------------------------------------

def _find_repo_root(start):
    """Walk upward from `start` looking for a `.git` directory; fall back to `start`."""
    current = start
    while True:
        if os.path.isdir(os.path.join(current, ".git")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return start
        current = parent


_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = _find_repo_root(_SCRIPT_DIR)

BLUEPRINT_PATH = os.path.join(
    _REPO_ROOT,
    "fixtures", "taskflow", "blueprints", "BLUEPRINT-NOVA-P1-NotificationCore.yaml"
)
STATE_PATH = os.path.join(_SCRIPT_DIR, ".state.json")


# ---------------------------------------------------------------------------
# Blueprint Normalization
# ---------------------------------------------------------------------------
#
# Two blueprint shapes exist in the wild:
#
#   "phased" (a top-level list of phases):
#     - name: "Phase name"
#       workstreams:
#         - feature_lead: FeatureLead-X
#           dependencies: [...]
#
#   "flat"   (a single mapping with a top-level `workstreams` list):
#     name: Epic-Name
#     workstreams:
#       - id: WS-0
#         name: Some-Workstream
#         depends_on: [...]
#
# _normalize_blueprint returns a canonical list-of-phases shape with a
# stable `feature_lead` key and `dependencies` list on every workstream.
# ---------------------------------------------------------------------------

def _workstream_id(ws):
    """Return a stable string identifier for a workstream in either schema."""
    if "feature_lead" in ws:
        return ws["feature_lead"]
    # Flat schema: prefer `name`, fall back to `id`.
    name = ws.get("name") or ws.get("id")
    if not name:
        raise ValueError(f"Workstream has no feature_lead, name, or id: {ws!r}")
    return f"FeatureLead-{name}" if not str(name).startswith("FeatureLead-") else str(name)


def _normalize_blueprint(raw):
    """Coerce either blueprint shape into list[{name, workstreams:[...]}]."""
    # Phased (list of dicts with `workstreams`).
    if isinstance(raw, list):
        phases = raw
    # Flat (single dict with top-level `workstreams`).
    elif isinstance(raw, dict) and "workstreams" in raw:
        phases = [{"name": raw.get("name", "default"), "workstreams": raw["workstreams"]}]
    else:
        raise ValueError("Blueprint must be a list of phases or a dict with `workstreams`.")

    # Pass 1: assign canonical feature_lead ids and build a ref→id lookup so that
    # `depends_on: [WS-1]` resolves against the workstream whose `id: WS-1` even
    # though its feature_lead is `FeatureLead-EventFanout`.
    ref_to_id = {}
    for phase in phases:
        for ws in phase["workstreams"]:
            ws["feature_lead"] = _workstream_id(ws)
            for ref in (ws.get("id"), ws.get("name"), ws["feature_lead"]):
                if ref:
                    ref_to_id[str(ref)] = ws["feature_lead"]

    # Pass 2: normalize dependencies — accept `depends_on` or `dependencies`,
    # resolve each ref against the lookup, fall back to FeatureLead-<ref> prefix.
    for phase in phases:
        for ws in phase["workstreams"]:
            deps = ws.get("dependencies") or ws.get("depends_on") or []
            resolved = []
            for d in deps:
                d = str(d)
                if d in ref_to_id:
                    resolved.append(ref_to_id[d])
                elif d.startswith("FeatureLead-"):
                    resolved.append(d)
                else:
                    resolved.append(f"FeatureLead-{d}")
            ws["dependencies"] = resolved
    return phases


# ---------------------------------------------------------------------------
# Blueprint Path Resolution
# ---------------------------------------------------------------------------

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
        if os.path.isabs(bp_file):
            bp_path = bp_file
        else:
            # Resolve a relative path, in order: against the current working
            # directory, against this script's own directory, then against
            # the repo root — first match wins, cwd falls back if none exist.
            bp_path = os.path.join(os.getcwd(), bp_file)
            for base in (os.getcwd(), _SCRIPT_DIR, _REPO_ROOT):
                candidate = os.path.join(base, bp_file)
                if os.path.exists(candidate):
                    bp_path = candidate
                    break
        return bp_path, remaining
    return BLUEPRINT_PATH, args


# ---------------------------------------------------------------------------
# Blueprint Parsing
# ---------------------------------------------------------------------------

def load_blueprint(blueprint_path=None):
    """
    Loads the blueprint file and returns the parsed, normalized blueprint.

    Handles two file formats:
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
        raw = yaml.safe_load(content)
    else:
        with open(path, "r") as f:
            for line in f:
                if line.strip() == "```yaml":
                    break
            yaml_content = f.read().strip().replace("```", "")
        raw = yaml.safe_load(yaml_content)
    return _normalize_blueprint(raw)


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
