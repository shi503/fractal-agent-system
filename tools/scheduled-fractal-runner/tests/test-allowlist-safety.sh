#!/usr/bin/env bash
# test-allowlist-safety.sh — static guard against the porous-allowlist class.
# Per-command Bash allowlisting is bypassable when an allowlisted "read" tool can
# exec a child (find -exec, rg --pre, sed e, awk system, xargs, gh api mutations,
# language interpreters). This test fails the build if any such token re-enters
# claude_allowed_tools_review / _live, so a future well-meaning edit can't silently
# reopen the hole. It does NOT prove Claude's runtime matcher denies them — it
# guarantees they're never granted in the first place.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REG="${DIR}/registry.json"
fail=0

# Exec/mutation-capable tokens that must NEVER appear in EITHER allowlist.
FORBIDDEN_BOTH=(find rg sed awk xargs eval env perl python python3 ruby node bash sh 'gh gist' 'gh secret' 'gh auth' 'gh repo' 'gh run' 'gh workflow')
# `gh api` is mutation-capable (POST/DELETE) — forbidden in REVIEW (read-only); allowed in LIVE (gated).
REVIEW="$(jq -r '.config.claude_allowed_tools_review' "$REG")"
LIVE="$(jq -r '.config.claude_allowed_tools_live' "$REG")"
DENY="$(jq -r '.config.claude_disallowed_tools' "$REG")"

check() { # list-name haystack token
  if grep -qE "Bash\($2[ :)]" <<<"$3"; then
    echo "FAIL: '$2' is exec/mutation-capable but present in $1"; fail=1
  fi
}

for t in "${FORBIDDEN_BOTH[@]}"; do
  check claude_allowed_tools_review "$t" "$REVIEW"
  check claude_allowed_tools_live   "$t" "$LIVE"
done
# gh api: must be absent from review, and must be in the deny list's intent for review.
grep -qE 'Bash\(gh api[ :)]' <<<"$REVIEW" && { echo "FAIL: 'gh api' (mutation-capable) present in review allowlist"; fail=1; }

# permission mode must not be acceptEdits/bypassPermissions.
mode="$(jq -r '.config.claude_permission_mode' "$REG")"
[[ "$mode" == "default" || "$mode" == "plan" ]] || { echo "FAIL: claude_permission_mode='$mode' (expected default/plan)"; fail=1; }

# Edit/Write must be denied.
grep -q 'Edit' <<<"$DENY" && grep -q 'Write' <<<"$DENY" || { echo "FAIL: Edit/Write not in deny list"; fail=1; }

# Untrusted sweep must stay disabled until a sandbox/classifier exists.
[[ "$(jq -r '.sweep.enabled' "$REG")" == "false" ]] || { echo "FAIL: sweep.enabled must be false until --permission-prompt-tool/sandbox lands"; fail=1; }

if [[ $fail -eq 0 ]]; then echo "PASS: allowlist safety guards hold"; fi
exit $fail
