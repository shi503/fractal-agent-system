#!/usr/bin/env bash
# run.sh — Scheduled FRACTAL Runner (ported from the FRACTAL machinery reference implementation).
#
# One engine, one schedule, two scopes:
#   - REGISTRY targets (registry.json .targets[]): PR review + HANDOFF evidence.
#   - SWEEP (--review-requested=@me): review-only; repos with no local checkout are SKIPPED.
#
# SAFETY LADDER (--mode):
#   plan    (default) — discover + state-diff + print the plan. No model, no posting, no gates run. SAFE.
#   review            — pr-review runs the TRIAGE skill to a file (never posts); evidence runs gates -> artifacts. No GitHub writes.
#   live              — pr-review runs the POSTING skill (inline comments only; auto-fix DISABLED); evidence runs gates -> artifacts.
#
# Concurrency is hard-capped at 1 (a parallel headless-claude fan-out can OOM a small VM).
# Targets run sequentially; there is no parallel path in this script by design.
#
# Usage:
#   run.sh [--mode plan|review|live] [--job pr-review|handoff-evidence|all]
#          [--only <repo_slug>] [--registry <path>]
set -euo pipefail

# --- resolve paths -----------------------------------------------------------
RUNNER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REGISTRY_FILE="${RUNNER_DIR}/registry.json"
STATE_FILE="${RUNNER_DIR}/state.json"
LOCK_FILE="${RUNNER_DIR}/.run.lock"
RUNS_DIR="${RUNNER_DIR}/runs"
RUN_DATE="$(date -u +%Y-%m-%d)"
RUN_LOG="${RUNNER_DIR}/run.log"

# --- args --------------------------------------------------------------------
MODE="plan"
JOB="all"
ONLY=""
ONLY_PR=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)     MODE="$2"; shift 2 ;;
    --job)      JOB="$2"; shift 2 ;;
    --only)     ONLY="$2"; shift 2 ;;
    --pr)       ONLY_PR="$2"; shift 2 ;;   # restrict to one PR number (use with --only <slug>)
    --registry) REGISTRY_FILE="$2"; shift 2 ;;
    -h|--help)  grep '^#' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
case "$MODE" in plan|review|live) ;; *) echo "bad --mode: $MODE" >&2; exit 2 ;; esac
case "$JOB"  in all|pr-review|handoff-evidence) ;; *) echo "bad --job: $JOB" >&2; exit 2 ;; esac

# shellcheck source=lib.sh
source "${RUNNER_DIR}/lib.sh"

# --- config from registry ----------------------------------------------------
MODEL="$(reg '.config.model')"
OWNER_FILTER="$(reg '.config.owner_filter')"
PERMISSION_MODE="$(reg '.config.claude_permission_mode')"
# Per-mode tool allowlist (review = read-only; live = + gh pr comment/review). Deny list takes precedence.
ALLOWED_TOOLS_REVIEW="$(reg '.config.claude_allowed_tools_review')"
ALLOWED_TOOLS_LIVE="$(reg '.config.claude_allowed_tools_live')"
DISALLOWED_TOOLS="$(reg '.config.claude_disallowed_tools')"
REVIEW_SKILL="$(reg '.config.pr_review_skill')"     # posting (live)
TRIAGE_SKILL="$(reg '.config.pr_triage_skill')"     # never-posts (review)

# --- portable path derivation (no machine-specific absolute paths in registry) ----
# Sibling repos: FRACTAL_REPOS_ROOT env wins, else config.repos_root. So each machine sets ONE var.
REPOS_ROOT="${FRACTAL_REPOS_ROOT:-$(reg '.config.repos_root')}"
if [[ -z "$REPOS_ROOT" || ! -d "$REPOS_ROOT" ]]; then
  echo "ERROR: repos root '${REPOS_ROOT}' not found. Set FRACTAL_REPOS_ROOT to the dir containing your sibling repos." >&2
  exit 3
fi
# This runner's own plugin dirs derive from the script location (RUNNER_DIR = <repo>/tools/scheduled-fractal-runner).
REPO_ROOT="$(cd "${RUNNER_DIR}/../.." && pwd)"
WT_BASE="${FRACTAL_WORKTREE_BASE:-${REPOS_ROOT}/.fractal-runner-worktrees}"
PLUGIN_FLAGS=()
for d in "${REPO_ROOT}/.claude/plugins/fractal-tools" "${REPO_ROOT}/.claude/plugins/fractal-pr-review"; do
  [[ -d "$d" ]] && PLUGIN_FLAGS+=(--plugin-dir "$d")
done

mkdir -p "$RUNS_DIR/$RUN_DATE" "$WT_BASE"
state_init
acquire_lock
log_info "START mode=${MODE} job=${JOB} only=${ONLY:-<all>} model=${MODEL}"
assert_gh

REVIEWED=0; SKIPPED=0; GATED=0; FAILED=0

# --- worktree lifecycle (sync local checkout to PR head) ---------------------
# Design decision: review must match the contributor's environment, not a stale local branch.
# We fetch pull/<n>/head and check it out into an isolated, detached worktree, then remove it.
make_worktree() {
  local repo_path="$1" slug="$2" pr="$3" wt="${WT_BASE}/${2}-pr${3}"
  rm -rf "$wt" 2>/dev/null || true
  git -C "$repo_path" worktree prune >/dev/null 2>&1 || true
  if ! git -C "$repo_path" fetch -q origin "pull/${pr}/head" 2>/dev/null; then
    log_warn "fetch pull/${pr}/head failed in ${slug}"; return 1
  fi
  if ! git -C "$repo_path" worktree add -q --detach "$wt" FETCH_HEAD 2>/dev/null; then
    log_warn "worktree add failed for ${slug}#${pr}"; return 1
  fi
  printf '%s\n' "$wt"
}
remove_worktree() {
  local repo_path="$1" wt="$2"
  [[ -n "$wt" && -d "$wt" ]] || return 0
  git -C "$repo_path" worktree remove --force "$wt" >/dev/null 2>&1 || rm -rf "$wt"
}

# --- PR review job -----------------------------------------------------------
# Args: repo_path owner slug pr scope(full|review-only)
review_pr() {
  local repo_path="$1" owner="$2" slug="$3" pr="$4" scope="$5"
  local key="${slug}#${pr}"

  # head SHA + branch + draft state
  local meta head_sha head_branch is_draft title
  if ! meta="$(gh pr view "$pr" --repo "${owner}/${slug}" \
      --json headRefOid,headRefName,isDraft,title 2>/dev/null)"; then
    log_warn "SKIP ${key} — gh pr view failed"; SKIPPED=$((SKIPPED+1)); return 0
  fi
  head_sha="$(jq -r '.headRefOid' <<<"$meta")"
  head_branch="$(jq -r '.headRefName' <<<"$meta")"
  is_draft="$(jq -r '.isDraft' <<<"$meta")"
  title="$(jq -r '.title' <<<"$meta")"

  if [[ "$is_draft" == "true" ]]; then
    log_info "SKIP ${key} — draft"; SKIPPED=$((SKIPPED+1)); return 0
  fi

  # state guard: skip unchanged heads
  local last; last="$(state_get_sha "$key")"
  if [[ "$last" == "$head_sha" ]]; then
    log_info "SKIP ${key} — unchanged since last review (${head_sha:0:8})"; SKIPPED=$((SKIPPED+1)); return 0
  fi

  if [[ "$MODE" == "plan" ]]; then
    log_info "WOULD-REVIEW ${key} [${scope}] head=${head_sha:0:8} branch=${head_branch} :: ${title}"
    REVIEWED=$((REVIEWED+1)); return 0
  fi

  # review/live: sync to PR head in an isolated worktree
  local wt; if ! wt="$(make_worktree "$repo_path" "$slug" "$pr")"; then
    log_warn "SKIP ${key} — worktree/fetch failed"; SKIPPED=$((SKIPPED+1)); return 0
  fi
  # trap-free cleanup: explicit remove after the run (sequential, so safe)
  local skill out rc=0 allowed
  if [[ "$MODE" == "live" ]]; then skill="$REVIEW_SKILL"; allowed="$ALLOWED_TOOLS_LIVE"; else skill="$TRIAGE_SKILL"; allowed="$ALLOWED_TOOLS_REVIEW"; fi
  out="${RUNS_DIR}/${RUN_DATE}/${slug}-pr${pr}.md"

  log_info "REVIEW ${key} [${scope}] mode=${MODE} skill=${skill} head=${head_sha:0:8} (cwd=worktree)"
  # SECURITY: PR code here is UNTRUSTED. The headless session is constrained by:
  #   --permission-mode default (only the allowlist runs unattended)
  #   --allowedTools  : read-only in review mode; + gh pr comment/review in live mode
  #   --disallowedTools (precedence): blocks code mutation, git push, exfil (curl/ssh/gist), account/infra reach
  # This — not merely the absence of Edit — is what enforces comment-only / auto-fix-disabled.
  if ! ( cd "$wt" && claude -p "${skill} ${owner}/${slug} #${pr}" \
        --model "$MODEL" \
        --permission-mode "$PERMISSION_MODE" \
        --allowedTools "$allowed" \
        --disallowedTools "$DISALLOWED_TOOLS" \
        "${PLUGIN_FLAGS[@]}" \
        --add-dir "$wt" ) >"$out" 2>>"$RUN_LOG"; then
    rc=$?
  fi
  remove_worktree "$repo_path" "$wt"

  if [[ $rc -ne 0 ]]; then
    log_error "REVIEW ${key} FAILED rc=${rc} (see ${out})"; FAILED=$((FAILED+1)); return 0
  fi
  state_set_sha "$key" "$head_sha"
  log_info "REVIEWED ${key} -> ${out}"; REVIEWED=$((REVIEWED+1))
}

# --- HANDOFF evidence job ----------------------------------------------------
# Only registered targets, only when a workstream is IN_PROGRESS.
evidence_target() {
  local slug="$1" gate_cmd="$2" gate_cwd="$3" fractal_dir="$4" state_file="$5"
  local wips; wips="$(in_progress_workstreams "$state_file")"
  if [[ -z "$wips" ]]; then
    log_info "EVIDENCE ${slug} — no IN_PROGRESS workstream, skip"; return 0
  fi
  local ws; ws="$(head -n1 <<<"$wips")"   # evidence anchored to the first IN_PROGRESS ws
  local ev_dir="${fractal_dir}/evidence" ev_file
  ev_file="${ev_dir}/${RUN_DATE}-${ws}-gate.md"

  if [[ "$MODE" == "plan" ]]; then
    log_info "WOULD-GATE ${slug} ws=${ws} cmd='${gate_cmd}' (cwd=${gate_cwd}) -> ${ev_file}"
    GATED=$((GATED+1)); return 0
  fi

  mkdir -p "$ev_dir"
  local rc=0 stdout_file; stdout_file="$(mktemp)"
  log_info "GATE ${slug} ws=${ws} :: ${gate_cmd}"
  if ! ( cd "$gate_cwd" && eval "$gate_cmd" ) >"$stdout_file" 2>&1; then rc=$?; fi

  {
    printf -- '---\n'
    printf 'target: %s\nworkstream: %s\ngate: "%s"\nrun_at: %s\nresult: %s\n' \
      "$slug" "$ws" "$gate_cmd" "$(now_utc)" "$([[ $rc -eq 0 ]] && echo PASS || echo FAIL)"
    printf -- '---\n\n'
    printf '# Gate evidence — %s / %s\n\n' "$slug" "$ws"
    printf 'Machine-verified by the Scheduled FRACTAL Runner. "Reading is not verification. Run it."\n\n'
    printf '## Result: **%s** (exit %s)\n\n' "$([[ $rc -eq 0 ]] && echo PASS || echo FAIL)" "$rc"
    printf '## Command output\n\n```\n'
    tail -c 60000 "$stdout_file"
    printf '\n```\n'
  } > "$ev_file"
  rm -f "$stdout_file"

  if [[ $rc -ne 0 ]]; then log_error "GATE ${slug} FAILED rc=${rc} -> ${ev_file}"; FAILED=$((FAILED+1));
  else log_info "GATE ${slug} PASS -> ${ev_file}"; fi
  GATED=$((GATED+1))
}

# --- scope A: registry targets ----------------------------------------------
n_targets="$(reg '.targets | length')"
for i in $(seq 0 $(( n_targets - 1 ))); do
  enabled="$(reg ".targets[$i].enabled")"
  slug="$(reg ".targets[$i].repo_slug")"
  [[ "$enabled" == "true" ]] || { log_info "target ${slug} disabled, skip"; continue; }
  [[ -z "$ONLY" || "$ONLY" == "$slug" ]] || continue

  owner="$(reg ".targets[$i].owner")"
  repo_dir="$(reg ".targets[$i].repo_dir")"
  gate_subdir="$(reg ".targets[$i].gate_subdir // \"\"")"
  gate_cmd="$(reg ".targets[$i].gate_cmd")"
  # derived (portable): repo_path = ${REPOS_ROOT}/${repo_dir}
  repo_path="${REPOS_ROOT}/${repo_dir}"
  fractal_dir="${repo_path}/.claude/FRACTAL"
  state_f="${fractal_dir}/.state.json"
  gate_cwd="${repo_path}${gate_subdir:+/$gate_subdir}"

  if [[ ! -d "$repo_path" ]]; then
    log_warn "target ${slug} repo_path missing (${repo_path}) — not checked out on this machine, skip"; SKIPPED=$((SKIPPED+1)); continue
  fi
  log_info "=== TARGET ${slug} (${owner}/${slug}) ==="

  if [[ "$JOB" == "all" || "$JOB" == "pr-review" ]]; then
    # discover open PRs for THIS repo. Use `gh pr list --repo` (correctly repo-scoped);
    # `gh search prs --owner ... --repo ...` ignores the repo filter and returns org-wide PRs.
    if [[ -n "$ONLY_PR" ]]; then
      prs="$ONLY_PR"
    else
      prs="$(gh pr list --repo "${owner}/${slug}" --state open --limit 200 \
              --json number -q '.[].number' 2>/dev/null || true)"
    fi
    if [[ -z "$prs" ]]; then log_info "no open PRs for ${slug}"; fi
    for pr in $prs; do
      review_pr "$repo_path" "$owner" "$slug" "$pr" "full"
    done
  fi

  if [[ "$JOB" == "all" || "$JOB" == "handoff-evidence" ]]; then
    if reg ".targets[$i].jobs | index(\"handoff-evidence\")" | grep -qv null; then
      evidence_target "$slug" "$gate_cmd" "$gate_cwd" "$fractal_dir" "$state_f"
    fi
  fi
done

# --- scope B: review-requested sweep (review-only) ---------------------------
if [[ "$JOB" == "all" || "$JOB" == "pr-review" ]] && [[ "$(reg '.sweep.enabled')" == "true" ]] && [[ -z "$ONLY" ]]; then
  log_info "=== SWEEP (review-requested=@me, review-only) ==="
  sweep_q="$(reg '.sweep.query')"
  # shellcheck disable=SC2086
  sweep_json="$(gh search prs $sweep_q --json number,repository 2>/dev/null || echo '[]')"
  count="$(jq 'length' <<<"$sweep_json")"
  log_info "sweep returned ${count} review-requested PR(s)"
  for row in $(jq -r '.[] | @base64' <<<"$sweep_json"); do
    _j() { base64 -d <<<"$row" | jq -r "$1"; }
    s_owner="$(_j '.repository.owner.login // (.repository.nameWithOwner|split("/")[0])')"
    s_name="$(_j '.repository.name')"
    s_pr="$(_j '.number')"
    # map to a registered local checkout; skip if none (no clone-on-demand by design)
    rdir="$(reg ".targets[] | select(.repo_slug==\"${s_name}\") | .repo_dir" | head -n1)"
    rp=""; [[ -n "$rdir" ]] && rp="${REPOS_ROOT}/${rdir}"
    if [[ -z "$rp" || ! -d "$rp" ]]; then
      log_info "SWEEP SKIP ${s_name}#${s_pr} — no registered local checkout (review-only sweep)"; SKIPPED=$((SKIPPED+1)); continue
    fi
    review_pr "$rp" "$s_owner" "$s_name" "$s_pr" "review-only"
  done
fi

log_info "DONE mode=${MODE} reviewed=${REVIEWED} skipped=${SKIPPED} gated=${GATED} failed=${FAILED}"
[[ $FAILED -eq 0 ]]
