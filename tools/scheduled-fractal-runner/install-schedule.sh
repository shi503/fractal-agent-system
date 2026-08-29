#!/usr/bin/env bash
# install-schedule.sh — install (or remove) the hourly schedule for the Scheduled FRACTAL Runner.
# Cross-platform: systemd --user timer on Linux, launchd LaunchAgent on macOS.
#
# It bakes the correct absolute paths + a resolved PATH (so claude/gh/git/jq/make/npm are found
# under the minimal scheduler environment) into the generated unit/plist. No hand-editing.
#
# NOTE: running this script installs a real schedule on the current machine. Its presence in
# this directory does not install anything by itself — `install` must be invoked explicitly.
#
# Usage:
#   FRACTAL_REPOS_ROOT=/path/to/sibling/repos ./install-schedule.sh install   [--job pr-review|all] [--mode review|live]
#   ./install-schedule.sh status
#   ./install-schedule.sh uninstall
#   ./install-schedule.sh run-now          # fire one run immediately via the scheduler
set -euo pipefail

RUNNER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACTION="${1:-status}"; shift || true
JOB="pr-review"; MODE="review"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --job)  JOB="$2"; shift 2 ;;
    --mode) MODE="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

OS="$(uname -s)"
LABEL="com.fractal-agent-system.fractal-runner"
SVC="fractal-runner"

# Resolve a PATH that contains every binary the runner + headless claude need. Schedulers start
# with a minimal PATH (launchd especially), so we compute it from where the tools actually are.
resolve_path() {
  local dirs=() b d
  for b in claude gh git jq make npm node bash; do
    d="$(command -v "$b" 2>/dev/null || true)"
    [[ -n "$d" ]] && dirs+=("$(dirname "$d")")
  done
  # de-dupe, then append common locations
  printf '%s\n' "${dirs[@]}" /usr/local/bin /opt/homebrew/bin /usr/bin /bin "$HOME/.local/bin" \
    | awk '!seen[$0]++' | paste -sd: -
}

require_root_env() {
  if [[ -z "${FRACTAL_REPOS_ROOT:-}" ]]; then
    echo "ERROR: set FRACTAL_REPOS_ROOT to the directory containing your sibling repos." >&2
    echo "  e.g. FRACTAL_REPOS_ROOT=\$HOME/dev/repos ./install-schedule.sh install" >&2
    exit 2
  fi
  [[ -d "$FRACTAL_REPOS_ROOT" ]] || { echo "ERROR: FRACTAL_REPOS_ROOT '$FRACTAL_REPOS_ROOT' is not a directory." >&2; exit 2; }
}

install_linux() {
  require_root_env
  local path_val unit_dir="$HOME/.config/systemd/user"
  path_val="$(resolve_path)"
  mkdir -p "$unit_dir"
  cat > "$unit_dir/${SVC}.service" <<EOF
[Unit]
Description=Scheduled FRACTAL Runner (hourly PR review)
After=network-online.target

[Service]
Type=oneshot
Environment=FRACTAL_REPOS_ROOT=${FRACTAL_REPOS_ROOT}
Environment=PATH=${path_val}
WorkingDirectory=${RUNNER_DIR}
ExecStart=${RUNNER_DIR}/run.sh --mode ${MODE} --job ${JOB}
TimeoutStartSec=50m
Nice=10
EOF
  cat > "$unit_dir/${SVC}.timer" <<EOF
[Unit]
Description=Daily (02:00 UTC) trigger for the Scheduled FRACTAL Runner

[Timer]
OnCalendar=*-*-* 02:00:00 UTC
Persistent=true
RandomizedDelaySec=120
Unit=${SVC}.service

[Install]
WantedBy=timers.target
EOF
  systemctl --user daemon-reload
  systemctl --user enable --now "${SVC}.timer"
  # so timers fire even when the user is not logged in (optional; ignore failure if not permitted)
  loginctl enable-linger "$USER" 2>/dev/null || echo "NOTE: 'loginctl enable-linger $USER' needs sudo; without it the timer only runs while you're logged in."
  echo "Installed systemd --user timer (${MODE}/${JOB}, daily 02:00 UTC)."
  systemctl --user list-timers "${SVC}.timer" --no-pager || true
}

install_macos() {
  require_root_env
  local path_val plist="$HOME/Library/LaunchAgents/${LABEL}.plist"
  path_val="$(resolve_path)"
  mkdir -p "$HOME/Library/LaunchAgents"
  cat > "$plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${RUNNER_DIR}/run.sh</string>
    <string>--mode</string><string>${MODE}</string>
    <string>--job</string><string>${JOB}</string>
  </array>
  <key>WorkingDirectory</key><string>${RUNNER_DIR}</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>FRACTAL_REPOS_ROOT</key><string>${FRACTAL_REPOS_ROOT}</string>
    <key>PATH</key><string>${path_val}</string>
    <key>HOME</key><string>${HOME}</string>
  </dict>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key><integer>2</integer>
    <key>Minute</key><integer>0</integer>
  </dict>
  <key>RunAtLoad</key><false/>
  <key>StandardOutPath</key><string>${RUNNER_DIR}/launchd.out.log</string>
  <key>StandardErrorPath</key><string>${RUNNER_DIR}/launchd.err.log</string>
</dict>
</plist>
EOF
  launchctl unload "$plist" 2>/dev/null || true
  launchctl load -w "$plist"
  echo "Installed launchd agent ${LABEL} (${MODE}/${JOB}, daily 02:00 local — launchd has no UTC calendar; adjust Hour if UTC alignment matters)."
  echo "NOTE (macOS): the Mac must be awake at fire time; 'pmset' naps are skipped, not caught up."
  launchctl list | grep "$LABEL" || true
}

case "$OS" in
  Linux)  PLATFORM=linux ;;
  Darwin) PLATFORM=macos ;;
  *) echo "unsupported OS: $OS" >&2; exit 2 ;;
esac

case "$ACTION" in
  install)
    [[ "$PLATFORM" == linux ]] && install_linux || install_macos
    echo "Reminder: pilot mode is '${MODE}'. Flip to live only after dry-run sign-off (see README.md)."
    ;;
  uninstall)
    if [[ "$PLATFORM" == linux ]]; then
      systemctl --user disable --now "${SVC}.timer" 2>/dev/null || true
      rm -f "$HOME/.config/systemd/user/${SVC}.service" "$HOME/.config/systemd/user/${SVC}.timer"
      systemctl --user daemon-reload
    else
      launchctl unload "$HOME/Library/LaunchAgents/${LABEL}.plist" 2>/dev/null || true
      rm -f "$HOME/Library/LaunchAgents/${LABEL}.plist"
    fi
    echo "Uninstalled."
    ;;
  status)
    if [[ "$PLATFORM" == linux ]]; then
      systemctl --user list-timers "${SVC}.timer" --no-pager 2>/dev/null || echo "not installed"
    else
      launchctl list | grep "$LABEL" || echo "not installed"
    fi
    ;;
  run-now)
    if [[ "$PLATFORM" == linux ]]; then systemctl --user start "${SVC}.service"; journalctl --user -u "${SVC}.service" -n 30 --no-pager
    else launchctl start "$LABEL"; echo "started; tail ${RUNNER_DIR}/run.log"; fi
    ;;
  *) echo "usage: install-schedule.sh {install|uninstall|status|run-now} [--job ...] [--mode ...]" >&2; exit 2 ;;
esac
