#!/usr/bin/env bash
# check-rules.sh — deterministic gate for the .claude/rules/ path-scoped rule layer.
#
# Checks, per file under .claude/rules/*.md:
#   1. the file opens with a `paths: [...]` frontmatter line followed by a bare
#      `---` delimiter within the first few lines, and the bracketed value
#      parses as a non-empty JSON array of strings
#   2. every path listed in the file's trailing
#      `<!-- referenced-paths ... -->` block (if present) resolves in this
#      repo, checked with `test -f` or `test -d`
#
# Usage: bash tools/check-rules.sh
# Exit code: 0 = all checks pass, 1 = at least one failure.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RULES_DIR="$REPO_ROOT/.claude/rules"

fail=0

shopt -s nullglob
rule_files=("$RULES_DIR"/*.md)
shopt -u nullglob

if [[ ${#rule_files[@]} -eq 0 ]]; then
  echo "check-rules: FAIL — no rule files found under $RULES_DIR" >&2
  exit 1
fi

echo "check-rules: found ${#rule_files[@]} rule file(s)"
echo ""

# --- Part A: frontmatter parse check (delegated to python for real parsing) ---
set +e
frontmatter_report="$(python3 - "${rule_files[@]}" <<'PYEOF'
import json
import sys

failures = []
passed = 0

for path in sys.argv[1:]:
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Find the bare "---" delimiter within the first 10 lines.
    delim_idx = None
    for i, line in enumerate(lines[:10]):
        if line.rstrip("\n") == "---":
            delim_idx = i
            break

    if delim_idx is None:
        failures.append(f"{path}: no bare '---' frontmatter delimiter in first 10 lines")
        continue

    frontmatter = "".join(lines[:delim_idx])

    paths_line = None
    for line in frontmatter.splitlines():
        stripped = line.strip()
        if stripped.startswith("paths:"):
            paths_line = stripped[len("paths:"):].strip()
            break

    if paths_line is None:
        failures.append(f"{path}: no 'paths:' key found before the '---' delimiter")
        continue

    try:
        value = json.loads(paths_line)
    except json.JSONDecodeError as e:
        failures.append(f"{path}: 'paths:' value does not parse as JSON: {paths_line!r} ({e})")
        continue

    if not isinstance(value, list) or not value or not all(isinstance(v, str) and v for v in value):
        failures.append(f"{path}: 'paths:' must be a non-empty JSON array of non-empty strings, got: {paths_line!r}")
        continue

    passed += 1

if failures:
    print(f"FRONTMATTER: FAIL ({len(failures)} issue(s), {passed} file(s) passed)")
    for msg in failures:
        print(f"  - {msg}")
    sys.exit(1)
else:
    print(f"FRONTMATTER: PASS ({passed} file(s))")
    sys.exit(0)
PYEOF
)"
frontmatter_status=$?
set -e
echo "$frontmatter_report"
echo ""
if [[ $frontmatter_status -ne 0 ]]; then
  fail=1
fi

# --- Part B: referenced-paths existence check (bash test -f / test -d) ---
ref_fail=0
ref_checked=0

for rf in "${rule_files[@]}"; do
  # Extract lines between "<!-- referenced-paths" and the closing "-->".
  block="$(sed -n '/<!-- referenced-paths/,/-->/p' "$rf" | sed '1d;$d')"
  if [[ -z "$block" ]]; then
    continue
  fi
  while IFS= read -r ref_path; do
    ref_path="$(echo "$ref_path" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
    [[ -z "$ref_path" ]] && continue
    ref_checked=$((ref_checked + 1))
    target="$REPO_ROOT/$ref_path"
    if test -f "$target" || test -d "$target"; then
      : # OK
    else
      echo "REFERENCED-PATH MISSING: $rf references '$ref_path' — not a file or directory in $REPO_ROOT" >&2
      ref_fail=1
    fi
  done <<< "$block"
done

if [[ $ref_fail -ne 0 ]]; then
  echo "REFERENCED-PATHS: FAIL"
  fail=1
else
  echo "REFERENCED-PATHS: PASS ($ref_checked path(s) checked)"
fi

echo ""
if [[ $fail -ne 0 ]]; then
  echo "check-rules: FAIL"
  exit 1
else
  echo "check-rules: PASS"
  exit 0
fi
