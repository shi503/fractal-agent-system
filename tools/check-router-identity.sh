#!/usr/bin/env bash
# check-router-identity.sh — verify the two router.py copies never drift.
#
# ROUTING_LOGIC/router.py is canonical. .claude/fractal/router.py is a
# synced copy the harness invokes directly from the fractal state dir.
# Edit the canonical copy and re-sync the other; never edit them
# independently. This check fails loudly (and non-zero) the moment they
# diverge, instead of the two copies silently drifting apart by luck.
#
# Usage: bash tools/check-router-identity.sh
# Run from the repo root (paths below are repo-relative).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

CANONICAL="$REPO_ROOT/ROUTING_LOGIC/router.py"
SYNCED="$REPO_ROOT/.claude/fractal/router.py"

if [[ ! -f "$CANONICAL" ]]; then
  echo "error: canonical router not found at ROUTING_LOGIC/router.py" >&2
  exit 2
fi
if [[ ! -f "$SYNCED" ]]; then
  echo "error: synced router not found at .claude/fractal/router.py" >&2
  exit 2
fi

if diff -q "$CANONICAL" "$SYNCED" >/dev/null; then
  echo "OK: ROUTING_LOGIC/router.py and .claude/fractal/router.py are byte-identical."
  exit 0
else
  echo "FAIL: router.py copies have diverged." >&2
  echo "--- diff (ROUTING_LOGIC/router.py vs .claude/fractal/router.py) ---" >&2
  diff "$CANONICAL" "$SYNCED" >&2 || true
  echo "" >&2
  echo "Fix: copy ROUTING_LOGIC/router.py over .claude/fractal/router.py (canonical wins)." >&2
  exit 1
fi
