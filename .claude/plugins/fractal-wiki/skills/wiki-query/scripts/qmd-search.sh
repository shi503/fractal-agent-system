#!/usr/bin/env bash
# qmd-search.sh — thin wrapper that locates the repo root and delegates to
# tools/wiki-index/qmd-search.sh, the canonical search-CLI resolver.
#
# This wrapper exists so a skill can call a stable, plugin-relative path
# (${CLAUDE_PLUGIN_ROOT}/skills/wiki-query/scripts/qmd-search.sh) regardless
# of the plugin's install location or the caller's cwd; the actual binary
# resolution and default index path live in one place: tools/wiki-index/.
#
# Usage: same as tools/wiki-index/qmd-search.sh — see that script's header.
set -euo pipefail

find_repo_root() {
  local dir="${PWD}"
  while [[ "${dir}" != "/" ]]; do
    if [[ -x "${dir}/tools/wiki-index/qmd-search.sh" ]]; then
      echo "${dir}"
      return 0
    fi
    dir="$(dirname "${dir}")"
  done
  echo "ERROR: could not locate tools/wiki-index/qmd-search.sh above ${PWD}." >&2
  return 1
}

ROOT="$(find_repo_root)" || exit 1
exec "${ROOT}/tools/wiki-index/qmd-search.sh" "$@"
