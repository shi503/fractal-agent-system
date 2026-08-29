#!/usr/bin/env bash
# sync-agents.sh — mirror the canonical agent definitions into .claude/agents/.
#
# The plugin is the distributable unit, so .claude/plugins/fractal-core/agents/
# is the single place an agent is edited. Claude Code loads project agents from
# .claude/agents/, so that directory is a generated, byte-identical mirror.
# Never hand-edit the mirror — the next sync overwrites it.
#
# Usage:
#   tools/sync-agents.sh            regenerate the mirror
#   tools/sync-agents.sh --check    verify the mirror is current (CI gate)
#
# Exit codes: 0 = in sync (or sync succeeded), 1 = drift found under --check,
#             2 = usage or environment error.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_DIR="$REPO_ROOT/.claude/plugins/fractal-core/agents"
DEST_DIR="$REPO_ROOT/.claude/agents"

CHECK_ONLY=0
for arg in "$@"; do
  case "$arg" in
    --check) CHECK_ONLY=1 ;;
    -h|--help)
      sed -n '2,14p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      echo "error: unknown argument: $arg" >&2
      echo "usage: $(basename "$0") [--check]" >&2
      exit 2
      ;;
  esac
done

if [[ ! -d "$SRC_DIR" ]]; then
  echo "error: canonical agent directory not found: $SRC_DIR" >&2
  exit 2
fi

shopt -s nullglob
SRC_FILES=("$SRC_DIR"/*.md)
shopt -u nullglob

if [[ ${#SRC_FILES[@]} -eq 0 ]]; then
  echo "error: no agent definitions found in $SRC_DIR" >&2
  exit 2
fi

drift=0

report_drift() {
  drift=1
  [[ $CHECK_ONLY -eq 1 ]] && echo "DRIFT: $1"
  return 0
}

# 1. Every canonical agent must exist in the mirror, byte-identical.
for src in "${SRC_FILES[@]}"; do
  name="$(basename "$src")"
  dest="$DEST_DIR/$name"
  if [[ ! -f "$dest" ]]; then
    report_drift "$name missing from .claude/agents/"
  elif ! cmp -s "$src" "$dest"; then
    report_drift "$name differs from the canonical copy"
  fi
done

# 2. The mirror must carry nothing the canonical directory does not.
if [[ -d "$DEST_DIR" ]]; then
  shopt -s nullglob
  for dest in "$DEST_DIR"/*.md; do
    name="$(basename "$dest")"
    if [[ ! -f "$SRC_DIR/$name" ]]; then
      report_drift "$name in .claude/agents/ has no canonical source"
    fi
  done
  shopt -u nullglob
fi

if [[ $CHECK_ONLY -eq 1 ]]; then
  if [[ $drift -eq 1 ]]; then
    echo "FAIL: .claude/agents/ is out of sync — run tools/sync-agents.sh" >&2
    exit 1
  fi
  echo "OK: .claude/agents/ matches $(printf '%s' "${SRC_DIR#"$REPO_ROOT"/}") (${#SRC_FILES[@]} agents)"
  exit 0
fi

mkdir -p "$DEST_DIR"

# Remove mirrored agents whose canonical source is gone, then copy the rest.
shopt -s nullglob
for dest in "$DEST_DIR"/*.md; do
  name="$(basename "$dest")"
  if [[ ! -f "$SRC_DIR/$name" ]]; then
    rm -f "$dest"
    echo "removed  .claude/agents/$name"
  fi
done
shopt -u nullglob

for src in "${SRC_FILES[@]}"; do
  name="$(basename "$src")"
  cp "$src" "$DEST_DIR/$name"
  echo "synced   .claude/agents/$name"
done

echo "OK: ${#SRC_FILES[@]} agents synced into .claude/agents/"
