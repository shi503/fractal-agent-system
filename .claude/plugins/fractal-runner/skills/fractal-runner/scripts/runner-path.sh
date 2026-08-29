#!/usr/bin/env bash
# runner-path.sh — resolve the absolute path to the runner from the plugin install location.
#
# The runner lives at tools/scheduled-fractal-runner/ inside this repo checkout.
# This plugin is installer-only (no runner code is duplicated here).
# The repo root is three plugin-layout levels above ${CLAUDE_PLUGIN_ROOT}:
#   ${CLAUDE_PLUGIN_ROOT} = <repo>/.claude/plugins/fractal-runner
#   repo root             = ${CLAUDE_PLUGIN_ROOT}/../../..
#
# Usage (source this file, then use $RUNNER_DIR):
#   source "${CLAUDE_PLUGIN_ROOT}/skills/fractal-runner/scripts/runner-path.sh"
#   echo "Runner: $RUNNER_DIR"

set -euo pipefail

REPO_ROOT="$(cd "${CLAUDE_PLUGIN_ROOT}/../../.." && pwd)"
RUNNER_DIR="${REPO_ROOT}/tools/scheduled-fractal-runner"

if [[ ! -f "${RUNNER_DIR}/run.sh" ]]; then
  echo "ERROR: runner not found at '${RUNNER_DIR}/run.sh'" >&2
  echo "  Expected: this repo's checkout at '${REPO_ROOT}'" >&2
  exit 1
fi

export RUNNER_DIR
export REPO_ROOT
