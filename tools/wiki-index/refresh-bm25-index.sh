#!/usr/bin/env bash
# refresh-bm25-index.sh — rebuild the committed BM25 (lex-only) index for the wiki substrate.
#
# The sanctioned discovery floor for this plugin is a committed, lexical-only
# search index — no vector/rerank models, no always-on MCP server. This
# script rebuilds that index from the live wiki corpus.
#
# It builds into an ISOLATED index config dir + index path (via QMD_CONFIG_DIR /
# INDEX_PATH) scoped to a single collection. It never runs the vector-embed
# step, so no vector tables are ever created — the output is BM25-only by
# construction, not by post-hoc stripping. It does NOT touch the caller's
# personal search-tool config or cache — safe to run on any box, including a
# machine with its own separate search-tool setup, without disturbing it.
#
# Configuration (env vars, both optional):
#   WIKI_SRC   — directory to index (default: fixtures/taskflow/wiki, this
#                repo's fixture corpus). A real deployment adopting this
#                plugin against its own wiki/ should set WIKI_SRC=wiki.
#   INDEX_DB   — output filename under tools/wiki-index/ (default: taskflow.sqlite,
#                matching the fixture). A real deployment should set
#                INDEX_DB=wiki.sqlite or similar.
#
# Usage:
#   tools/wiki-index/refresh-bm25-index.sh
#   WIKI_SRC=wiki INDEX_DB=wiki.sqlite tools/wiki-index/refresh-bm25-index.sh
#
# Output:
#   tools/wiki-index/${INDEX_DB:-taskflow.sqlite}
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

WIKI_SRC="${WIKI_SRC:-fixtures/taskflow/wiki}"
INDEX_DB="${INDEX_DB:-taskflow.sqlite}"

QMD_BIN="${QMD_BIN:-${SCRIPT_DIR}/node_modules/.bin/qmd}"
OUT_DB="${SCRIPT_DIR}/${INDEX_DB}"
SRC_DIR="${REPO_ROOT}/${WIKI_SRC}"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "${WORK_DIR}"' EXIT

if [[ ! -x "${QMD_BIN}" ]]; then
  echo "ERROR: search-tool binary not found at ${QMD_BIN}" >&2
  echo "  Fix: cd ${SCRIPT_DIR} && bun install && bun pm trust --all" >&2
  exit 1
fi

if [[ ! -d "${SRC_DIR}" ]]; then
  echo "ERROR: WIKI_SRC directory not found: ${SRC_DIR}" >&2
  exit 1
fi

cat > "${WORK_DIR}/index.yml" << YAML
collections:
  wiki:
    path: ${SRC_DIR}
    pattern: "**/*.md"
    ignore:
      - "**/_*/**"
      - "_*/**"
      - "**/_*.md"
      - "_*.md"
YAML

echo "Building lex-only index for ${WIKI_SRC} (no embed step run — BM25 only)..."
QMD_CONFIG_DIR="${WORK_DIR}" INDEX_PATH="${WORK_DIR}/index.sqlite" QMD_FORCE_CPU=1 \
  node "${QMD_BIN}" update

# The index is written in WAL mode: recent writes live in a -wal side file
# until checkpointed. Checkpoint (TRUNCATE folds -wal back into the main
# file and empties it) BEFORE moving/discarding side files, or the moved
# .sqlite is silently empty — recent data was never merged in.
if command -v sqlite3 >/dev/null 2>&1; then
  sqlite3 "${WORK_DIR}/index.sqlite" "PRAGMA wal_checkpoint(TRUNCATE);" >/dev/null
else
  echo "WARNING: sqlite3 CLI not found — cannot force a WAL checkpoint." >&2
  echo "  If ${OUT_DB} ends up empty, install sqlite3 and re-run." >&2
fi

mv "${WORK_DIR}/index.sqlite" "${OUT_DB}"
rm -f "${OUT_DB}-shm" "${OUT_DB}-wal"

SIZE=$(du -h "${OUT_DB}" | cut -f1)
echo ""
echo "Committed index refreshed: ${OUT_DB} (${SIZE})"
echo "Query it with:"
echo "  INDEX_PATH=${OUT_DB} QMD_FORCE_CPU=1 node ${QMD_BIN} search \"<query>\" --full-path"
echo "  or: tools/wiki-index/qmd-search.sh search \"<query>\""
echo ""
echo "Review the diff and commit ${OUT_DB} per the normal PR flow — this script"
echo "does not commit on your behalf."
