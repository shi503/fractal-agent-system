#!/usr/bin/env bash
# check-prereqs.sh — fail loudly, with the remedy, before router.py gets a
# chance to throw a raw ImportError at a reader who has no PyYAML installed.
#
# Usage: bash tools/check-prereqs.sh
set -euo pipefail

FAIL=0

if ! command -v python3 >/dev/null 2>&1; then
  echo "MISSING: python3 not found on PATH." >&2
  echo "  Remedy: install Python 3.8+ (https://www.python.org/downloads/)." >&2
  FAIL=1
else
  PY_VERSION="$(python3 --version 2>&1)"
  if ! python3 -c "import yaml" >/dev/null 2>&1; then
    echo "MISSING: PyYAML is not installed for this python3 ($PY_VERSION)." >&2
    echo "  router.py imports PyYAML to parse BLUEPRINT files; without it," >&2
    echo "  every router.py command (including tools/router-smoke.sh) fails" >&2
    echo "  with a raw ImportError instead of a usable message." >&2
    echo "  Remedy: pip install pyyaml" >&2
    FAIL=1
  fi
fi

if [ "$FAIL" -ne 0 ]; then
  echo "" >&2
  echo "Prerequisite check FAILED. Fix the item(s) above, then re-run:" >&2
  echo "  bash tools/check-prereqs.sh" >&2
  exit 1
fi

echo "OK: python3 + PyYAML present."
