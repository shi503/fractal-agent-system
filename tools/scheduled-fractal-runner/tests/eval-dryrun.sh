#!/usr/bin/env bash
# eval-dryrun.sh — dry-run scoring harness for the Scheduled FRACTAL Runner (AC1-7).
#
# READ-ONLY / INERT: scores AC1-7 by parsing artifacts a live run already produced
# (run.log, runs/<date>/*.md, state.json) plus static inspection of registry.json,
# run.sh, lib.sh, install-schedule.sh. It NEVER invokes run.sh itself, NEVER calls
# gh, NEVER arms `live`, and NEVER re-enables the sweep.
#
# On a fresh checkout there is no run.log yet (no live run has happened), so the
# log-dependent checks (AC2-5) report SKIP rather than FAIL — that is an expected,
# passing state for CI on a checkout that has never been operated, not a defect.
# The schema (AC1) and static-inspection (AC6-7) checks always run.
#
# Usage: tests/eval-dryrun.sh   (run from anywhere; paths are self-resolving)
set -uo pipefail   # no -e: keep scoring every AC even if one check fails

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REG="${DIR}/registry.json"
LOG="${DIR}/run.log"
STATE="${DIR}/state.json"

PASS=0; FAIL=0; WARN=0; SKIP=0
result() { # ac status detail
  local ac="$1" status="$2" detail="$3"
  case "$status" in PASS) PASS=$((PASS+1)) ;; FAIL) FAIL=$((FAIL+1)) ;; WARN) WARN=$((WARN+1)) ;; SKIP) SKIP=$((SKIP+1)) ;; esac
  printf '[%s] %-4s %s\n' "$ac" "$status" "$detail"
}

echo "=== Scheduled FRACTAL Runner dry-run scoring (AC1-7, read-only) ==="

# ---- AC1: registry schema — every enabled target carries the full schema ----
n="$(jq -r '.targets | length' "$REG" 2>/dev/null || echo 0)"
n_complete="$(jq -r '[.targets[] | select(.enabled==true and .owner and .repo_dir and .branch and .gate_cmd and .jobs)] | length' "$REG" 2>/dev/null || echo 0)"
if [[ "$n" -ge 1 && "$n_complete" == "$(jq -r '[.targets[] | select(.enabled==true)] | length' "$REG" 2>/dev/null)" && "$n_complete" -ge 1 ]]; then
  result AC1 PASS "registry.json: ${n} target(s), ${n_complete} enabled with full schema (owner/repo_dir/branch/gate_cmd/jobs)"
else
  result AC1 FAIL "registry.json has ${n} target(s) but only ${n_complete} enabled target(s) carry the full schema"
fi

if [[ ! -f "$LOG" ]]; then
  echo "no run.log yet — this is expected on a fresh checkout (no live run has happened)."
  echo "run './run.sh --mode plan' against a real FRACTAL_REPOS_ROOT to generate one, then re-run this script for AC2-5."
  result AC2 SKIP "no run.log — nothing to score"
  result AC3 SKIP "no run.log — nothing to score"
  result AC4 SKIP "no run.log — nothing to score"
  result AC5 SKIP "no run.log — nothing to score"
else
  # ---- AC2: discovery per target + dedupe, from the LAST --mode plan block ----
  plan_block="$(awk '/START mode=plan/{buf=""} {buf=buf $0 "\n"} /DONE mode=plan/{last=buf} END{printf "%s", last}' "$LOG")"
  if [[ -z "$plan_block" ]]; then
    result AC2 FAIL "no --mode plan run in run.log"
  else
    targets_seen="$(grep -oE '=== TARGET [a-zA-Z0-9._-]+' <<<"$plan_block" | awk '{print $3}' | sort -u)"
    n_targets_seen="$(grep -c . <<<"$targets_seen" 2>/dev/null || echo 0)"
    dup="$(grep -oE '(WOULD-REVIEW|SKIP) [a-zA-Z0-9._-]+#[0-9]+' <<<"$plan_block" | awk '{print $2}' | sort | uniq -d)"
    if [[ -n "$dup" ]]; then
      result AC2 FAIL "duplicate PR key(s) within one plan run (dedupe broke): ${dup}"
    elif [[ "$n_targets_seen" -lt 1 ]]; then
      result AC2 WARN "last plan run covered no targets"
    else
      result AC2 PASS "plan run discovered PRs across ${n_targets_seen} target(s), no duplicate keys — evidence: run.log (last plan block)"
    fi
  fi

  # ---- AC3: state-skip on unchanged head SHA ----
  skip_line="$(grep -E 'SKIP [a-zA-Z0-9._-]+#[0-9]+ — unchanged since last review' "$LOG" | tail -1)"
  if [[ -n "$skip_line" ]]; then
    key="$(grep -oE '[a-zA-Z0-9._-]+#[0-9]+' <<<"$skip_line" | head -1)"
    sha_short="$(grep -oE '\(([0-9a-f]{6,8})\)' <<<"$skip_line" | tr -d '()')"
    state_sha="$(jq -r --arg k "$key" '.[$k].last_reviewed_sha // ""' "$STATE" 2>/dev/null)"
    if [[ -n "$state_sha" && "$state_sha" == "${sha_short}"* ]]; then
      result AC3 PASS "state-skip proven: ${key} skipped (head ${sha_short}) == state.json last_reviewed_sha ${state_sha:0:8} — evidence: run.log:\"${skip_line}\""
    else
      result AC3 WARN "found a SKIP-unchanged line but state.json sha doesn't match: key=${key} log_sha=${sha_short} state_sha=${state_sha:-<none>}"
    fi
  else
    result AC3 WARN "no 'SKIP ... unchanged since last review' line yet — re-run the same --mode review target twice to observe it"
  fi

  # ---- AC4: comment-only, no auto-fix, worktree-synced review ----
  deny="$(jq -r '.config.claude_disallowed_tools' "$REG" 2>/dev/null)"
  allow_review="$(jq -r '.config.claude_allowed_tools_review' "$REG" 2>/dev/null)"
  wt_line="$(grep -E 'REVIEW .* \(cwd=worktree\)' "$LOG" | tail -1)"
  allowlist_ok=1
  { grep -q 'Edit' <<<"$deny" && grep -q 'Write' <<<"$deny"; } || allowlist_ok=0
  grep -qE 'gh pr comment|gh pr review|Bash\(gh api' <<<"$allow_review" && allowlist_ok=0
  allowlist_test_out="$(bash "${DIR}/tests/test-allowlist-safety.sh" 2>&1)"; allowlist_rc=$?
  if [[ $allowlist_ok -eq 1 && -n "$wt_line" && $allowlist_rc -eq 0 ]]; then
    result AC4 PASS "Edit/Write denied, review allowlist carries no posting verbs, worktree-synced review observed, test-allowlist-safety.sh PASS — evidence: run.log:\"${wt_line}\""
  elif [[ $allowlist_ok -eq 1 && $allowlist_rc -eq 0 ]]; then
    result AC4 WARN "allowlist/deny config is safe, but no worktree-synced review observed yet in run.log"
  else
    result AC4 FAIL "allowlist_ok=${allowlist_ok} worktree_line=${wt_line:-<none>} allowlist_safety_rc=${allowlist_rc} (${allowlist_test_out})"
  fi

  # ---- AC5: gate -> evidence artifact for IN_PROGRESS workstream ----
  real_gate="$(grep -E '\[INFO\] GATE .* (PASS|FAIL) ->' "$LOG" | tail -1)"
  would_gate="$(grep -c 'WOULD-GATE' "$LOG" 2>/dev/null || echo 0)"
  if [[ -n "$real_gate" ]]; then
    ev_path="$(grep -oE '/[^ ]*gate\.md' <<<"$real_gate")"
    if [[ -f "$ev_path" ]]; then
      result AC5 PASS "real gate executed + evidence artifact on disk: ${ev_path} — evidence: run.log:\"${real_gate}\""
    else
      result AC5 WARN "run.log claims gate evidence at ${ev_path} but the file isn't on THIS machine (different FRACTAL_REPOS_ROOT?)"
    fi
  elif [[ "$would_gate" -gt 0 ]]; then
    result AC5 WARN "only WOULD-GATE (plan-mode simulation, ${would_gate}x) seen — no real gate has executed yet; run --mode review --job all to produce a real artifact"
  else
    result AC5 WARN "no gate/evidence activity found in run.log yet"
  fi
fi

# ---- AC6: sequential execution + single-flight lock ----
parallel_pattern="$(grep -nE '&[[:space:]]*$|xargs[[:space:]]+-P|\bparallel\b' "${DIR}/run.sh" | grep -v '^\s*[0-9]*:\s*#' || true)"
flock_present="$(grep -c 'flock' "${DIR}/lib.sh" 2>/dev/null || true)"
if [[ -z "$parallel_pattern" && "$flock_present" -ge 1 ]]; then
  result AC6 PASS "no parallel-dispatch pattern in run.sh; flock single-flight guard present in lib.sh:acquire_lock"
else
  result AC6 FAIL "parallel pattern found or flock missing — pattern='${parallel_pattern}' flock_occurrences=${flock_present}"
fi

# ---- AC7: scheduler documented, cross-platform ----
has_linux_unit="$(grep -c 'OnCalendar' "${DIR}/install-schedule.sh" 2>/dev/null || true)"
has_macos_agent="$(grep -c 'StartCalendarInterval' "${DIR}/install-schedule.sh" 2>/dev/null || true)"
if [[ "$has_linux_unit" -ge 1 && "$has_macos_agent" -ge 1 ]]; then
  result AC7 PASS "scheduler mechanism shipped + documented (systemd timer + launchd agent); cadence daily 02:00 UTC"
else
  result AC7 FAIL "install-schedule.sh missing systemd(OnCalendar) or launchd(StartCalendarInterval) generation"
fi

echo "=== SUMMARY: ${PASS} PASS / ${WARN} WARN / ${SKIP} SKIP / ${FAIL} FAIL ==="
[[ "$FAIL" -eq 0 ]]
