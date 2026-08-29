#!/usr/bin/env bash
# check-guide-matrix.sh — verify every guide path listed in
# standards/guide-reference-matrix.md actually exists on disk.
#
# Usage: bash tools/check-guide-matrix.sh
# Run from the repository root (or anywhere inside the repo).
#
# Exit code: 0 = every listed path resolves. 1 = at least one path is
# missing (path and reason printed to stderr) or the matrix file itself
# is missing.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MATRIX="$REPO_ROOT/standards/guide-reference-matrix.md"

if [[ ! -f "$MATRIX" ]]; then
  echo "error: matrix file not found: $MATRIX" >&2
  exit 1
fi

# Extract every backtick-quoted path in the first table column that starts
# with "standards/". This matches rows like:
#   | `standards/engineering-principles.md` | ... | ... |
# Portable across bash 3.2 (macOS default) — no mapfile/readarray.
GUIDE_PATHS_FILE="$(mktemp)"
trap 'rm -f "$GUIDE_PATHS_FILE"' EXIT
grep -oE '`standards/[^`]+`' "$MATRIX" | tr -d '`' | sort -u > "$GUIDE_PATHS_FILE"

if [[ ! -s "$GUIDE_PATHS_FILE" ]]; then
  echo "error: no guide paths found in $MATRIX — matrix format may have changed" >&2
  exit 1
fi

MISSING=0
COUNT=0
while IFS= read -r rel_path; do
  [[ -z "$rel_path" ]] && continue
  COUNT=$((COUNT + 1))
  abs_path="$REPO_ROOT/$rel_path"
  if [[ -f "$abs_path" ]]; then
    echo "OK   $rel_path"
  else
    echo "MISSING $rel_path" >&2
    MISSING=1
  fi
done < "$GUIDE_PATHS_FILE"

if [[ $MISSING -ne 0 ]]; then
  echo "error: one or more paths in standards/guide-reference-matrix.md do not exist" >&2
  exit 1
fi

echo "check-guide-matrix: ${COUNT} guide path(s) verified, all present."
