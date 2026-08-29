#!/usr/bin/env bash
# lib.sh — deterministic helpers for the Scheduled FRACTAL Runner.
# No model calls live here; this is the router.py-style shell layer:
# logging, single-flight locking, and JSON state read/write.
#
# Sourced by run.sh. Assumes: RUNNER_DIR, RUN_LOG, STATE_FILE, LOCK_FILE are exported.

set -euo pipefail

# --- timestamps (UTC, ISO-8601, no Date.now ambiguity) ----------------------
now_utc() { date -u +%Y-%m-%dT%H:%M:%SZ; }

# --- logging: one line to stdout (journald captures it) AND to RUN_LOG -------
log() {
  local level="$1"; shift
  local line
  line="$(now_utc) [${level}] $*"
  printf '%s\n' "$line" | tee -a "$RUN_LOG" >&2
}
log_info()  { log INFO  "$@"; }
log_warn()  { log WARN  "$@"; }
log_error() { log ERROR "$@"; }

# --- single-flight lock: never let two runs overlap ---------------------
# Linux: flock on a dedicated fd (auto-releases on process exit).
# macOS: flock is not available (Linux util; absent without Homebrew), so fall
# back to an atomic mkdir lock with stale-PID detection (released via EXIT trap).
acquire_lock() {
  if command -v flock >/dev/null 2>&1; then
    exec 9>"$LOCK_FILE"
    if ! flock -n 9; then
      log_warn "another run holds $LOCK_FILE — exiting (single-flight)"
      exit 0
    fi
    printf 'pid=%s started=%s\n' "$$" "$(now_utc)" >&9 || true
    return 0
  fi
  # flock absent (macOS): mkdir is atomic across POSIX; a leftover lock from a
  # crashed run is reclaimed only if its recorded PID is no longer alive.
  local lockdir="${LOCK_FILE}.d"
  if ! mkdir "$lockdir" 2>/dev/null; then
    local holder; holder="$(cat "$lockdir/pid" 2>/dev/null || true)"
    if [[ -n "$holder" ]] && kill -0 "$holder" 2>/dev/null; then
      log_warn "another run holds $lockdir (pid $holder) — exiting (single-flight)"
      exit 0
    fi
    log_warn "reclaiming stale lock $lockdir (holder ${holder:-unknown} not running)"
    rm -rf "$lockdir"; mkdir "$lockdir"
  fi
  printf '%s' "$$" > "$lockdir/pid"
  # Use the module-global LOCK_FILE (not the function-local $lockdir, which is out
  # of scope when the EXIT trap fires under `set -u`).
  trap 'rm -rf "${LOCK_FILE}.d"' EXIT
}

# --- gh auth assertion: fail loud if scopes drift -----------------------
assert_gh() {
  if ! command -v gh >/dev/null 2>&1; then
    log_error "gh CLI not found on PATH"; exit 3
  fi
  if ! gh auth status >/dev/null 2>&1; then
    log_error "gh not authenticated (gh auth status failed)"; exit 3
  fi
  local scopes
  scopes="$(gh auth status 2>&1 | grep -i 'Token scopes' || true)"
  case "$scopes" in
    *repo*) : ;;
    *) log_error "gh token missing 'repo' scope: ${scopes:-<none>}"; exit 3 ;;
  esac
  log_info "gh auth OK ($(gh api user -q .login 2>/dev/null || echo '?')); ${scopes}"
}

# --- JSON state ledger (router.py .state.json ethos) -------------------------
# Schema: { "<repo_slug>#<pr>": {"last_reviewed_sha": "...", "last_reviewed_at": "..."} }
state_init() {
  [[ -f "$STATE_FILE" ]] || printf '{}\n' > "$STATE_FILE"
}

# Echo the last-reviewed SHA for a key, or empty string if unseen.
state_get_sha() {
  local key="$1"
  jq -r --arg k "$key" '.[$k].last_reviewed_sha // ""' "$STATE_FILE"
}

# Record a reviewed head SHA. Atomic write via temp file (never half-write state).
state_set_sha() {
  local key="$1" sha="$2" tmp
  tmp="$(mktemp "${STATE_FILE}.XXXXXX")"
  jq --arg k "$key" --arg s "$sha" --arg t "$(now_utc)" \
    '.[$k] = {last_reviewed_sha:$s, last_reviewed_at:$t}' "$STATE_FILE" > "$tmp"
  mv "$tmp" "$STATE_FILE"
}

# --- registry accessors ------------------------------------------------------
reg() { jq -r "$1" "$REGISTRY_FILE"; }

# IN_PROGRESS workstreams in a target's FRACTAL .state.json (scope guard).
in_progress_workstreams() {
  local state_file="$1"
  [[ -f "$state_file" ]] || return 0
  jq -r 'to_entries[] | select(.value=="IN_PROGRESS") | .key' "$state_file" 2>/dev/null || true
}
