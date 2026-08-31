#!/usr/bin/env bash
# release-gate.sh — target-side release gate (WS-19 FinalGateAndRC).
#
# Runs the structural checks named in the contamination-gate spec (private
# planning repo: projects/fractal-oss-port/references/contamination-gate.md,
# "Structural gates (not grep — WS-19)") over this repo's tracked files, then
# calls the hashed contamination scanner (tools/repo-hygiene/contamination_scan.py)
# so this one script is a self-contained release gate for CI.
#
# Checks:
#   1. Zero tracked *.pdf
#   2. No tracked file over 2 MB except the allowlist below
#   3. No file named people.yaml tracked outside fixtures/
#   4. No tracked .env* file (except the demo app's .env.example placeholder
#      template) and no tracked settings.local.json
#   5. No absolute home-directory path (either platform's user-home prefix)
#      in any tracked file's content
#   6. tools/repo-hygiene/contamination_scan.py over this repo, clean
#
# Usage: bash tools/release-gate.sh [<repo-root>]
# <repo-root> defaults to the git repo this script lives in; an explicit
# argument lets the gate logic be exercised against a throwaway repo for
# self-testing without touching this repo's own tracked state.
#
# Exit code: 0 = every check passes. Non-zero = at least one check failed
# (each failure is printed as `FAIL: <check>` with the offending paths).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${1:-$(cd "$SCRIPT_DIR/.." && pwd)}"

if ! git -C "$ROOT" rev-parse --show-toplevel >/dev/null 2>&1; then
  echo "error: not a git repo: $ROOT" >&2
  exit 2
fi
ROOT="$(git -C "$ROOT" rev-parse --show-toplevel)"

# Large tracked files exempt from the 2 MB cap — deliberately vetted content,
# not a general escape hatch. Matched against the end of the tracked path.
ALLOW_LARGE=(
  "tools/wiki-index/taskflow.sqlite"
)
MAX_BYTES=$((2 * 1024 * 1024))

STATUS=0
fail() {
  echo "FAIL: $1"
  STATUS=1
}
pass() {
  echo "PASS: $1"
}

FILES_TMP="$(mktemp)"
trap 'rm -f "$FILES_TMP"' EXIT
git -C "$ROOT" ls-files > "$FILES_TMP"

# --- 1. Zero tracked *.pdf ---
PDF_HITS="$(grep -iE '\.pdf$' "$FILES_TMP" || true)"
if [[ -n "$PDF_HITS" ]]; then
  fail "zero tracked *.pdf"
  echo "$PDF_HITS" | sed 's/^/  /'
else
  pass "zero tracked *.pdf"
fi

# --- 2. No tracked file over 2 MB outside the allowlist ---
LARGE_HITS=""
while IFS= read -r f; do
  [[ -z "$f" ]] && continue
  size=0
  if [[ -f "$ROOT/$f" ]]; then
    size=$(wc -c < "$ROOT/$f" | tr -d ' ')
  fi
  if (( size > MAX_BYTES )); then
    allowed=0
    for a in "${ALLOW_LARGE[@]}"; do
      if [[ "$f" == "$a" || "$f" == *"/$a" ]]; then
        allowed=1
        break
      fi
    done
    if [[ $allowed -eq 0 ]]; then
      LARGE_HITS="${LARGE_HITS}  ${f} (${size} bytes)"$'\n'
    fi
  fi
done < "$FILES_TMP"
if [[ -n "$LARGE_HITS" ]]; then
  fail "no tracked file over 2 MB outside the allowlist"
  printf '%s' "$LARGE_HITS"
else
  pass "no tracked file over 2 MB outside the allowlist"
fi

# --- 3. No file named people.yaml tracked outside fixtures/ ---
PEOPLE_HITS="$(grep -E '(^|/)people\.yaml$' "$FILES_TMP" | grep -v '^fixtures/' || true)"
if [[ -n "$PEOPLE_HITS" ]]; then
  fail "no people.yaml tracked outside fixtures/"
  echo "$PEOPLE_HITS" | sed 's/^/  /'
else
  pass "no people.yaml tracked outside fixtures/"
fi

# --- 4. No tracked .env* / settings.local.json ---
# .env.example is the demo app's committed placeholder template — no real
# values, only bracketed substitution markers. It predates this branch and is
# the conventional way a Next.js app documents its required variables. Every
# other .env* form is a hard failure.
ENV_HITS="$(grep -E '(^|/)\.env[^/]*$' "$FILES_TMP" | grep -vx '.env.example' || true)"
if [[ -n "$ENV_HITS" ]]; then
  fail "no tracked .env* file"
  echo "$ENV_HITS" | sed 's/^/  /'
else
  pass "no tracked .env* file"
fi

SLJ_HITS="$(grep -E '(^|/)settings\.local\.json$' "$FILES_TMP" || true)"
if [[ -n "$SLJ_HITS" ]]; then
  fail "no tracked settings.local.json"
  echo "$SLJ_HITS" | sed 's/^/  /'
else
  pass "no tracked settings.local.json"
fi

# --- 5. No absolute home path in any tracked file's content ---
# git grep -I skips files it detects as binary; searches tracked working-tree
# content, same convention as the cleartext scanner's file-mode.
HOME_PATH_HITS="$(git -C "$ROOT" grep -InE '(^|[^A-Za-z0-9_./-])(/Users/|/home/)[A-Za-z0-9_.-]+' -- . 2>/dev/null || true)"
if [[ -n "$HOME_PATH_HITS" ]]; then
  fail "no absolute home path in any tracked file"
  echo "$HOME_PATH_HITS" | sed 's/^/  /'
else
  pass "no absolute home path in any tracked file"
fi

# --- 6. Hashed contamination scanner ---
HASHED_SCANNER="$ROOT/tools/repo-hygiene/contamination_scan.py"
if [[ ! -f "$HASHED_SCANNER" ]]; then
  fail "hashed contamination scanner present at tools/repo-hygiene/contamination_scan.py"
else
  if python3 "$HASHED_SCANNER" "$ROOT"; then
    pass "hashed contamination scanner (tools/repo-hygiene/contamination_scan.py)"
  else
    fail "hashed contamination scanner (tools/repo-hygiene/contamination_scan.py) — see hits above"
  fi
fi

exit $STATUS
