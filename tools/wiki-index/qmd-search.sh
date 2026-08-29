#!/usr/bin/env bash
# qmd-search.sh — canonical resolver for the vendored search-tool CLI.
#
# Resolves the vendored binary and the committed BM25 index relative to this
# script's own location (so it works from any cwd and regardless of where a
# consuming plugin is installed), then runs the requested subcommand against
# the committed index by default.
#
# Usage:
#   qmd-search.sh search "<keywords>" [-c <collection>]   # BM25 only (fast, no model) — DEFAULT
#   qmd-search.sh query  "<question>" [--no-rerank]        # hybrid semantic (opt-in, local host only)
#   qmd-search.sh get    "<result-ref>"                     # fetch a document (line-numbered)
#   qmd-search.sh status                                    # index + collection health
#
# Configuration (env vars, both optional):
#   QMD_BIN     — override the resolved binary path.
#   INDEX_PATH  — override the resolved index path (default: tools/wiki-index/taskflow.sqlite,
#                 the fixture's committed index; a real deployment should set
#                 INDEX_PATH=tools/wiki-index/wiki.sqlite or similar).
#
# `query`/full rerank loads a local embedding + reranker model — several GB
# resident. It is opt-in and intended for a capable local workstation, not a
# CI runner or small VM. See tools/wiki-index/README.md for the full ladder.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

QMD_BIN="${QMD_BIN:-${SCRIPT_DIR}/node_modules/.bin/qmd}"
INDEX_PATH="${INDEX_PATH:-${SCRIPT_DIR}/taskflow.sqlite}"

if [[ ! -x "${QMD_BIN}" ]]; then
  echo "ERROR: search-tool binary not found at ${QMD_BIN}." >&2
  echo "  Fix: cd ${SCRIPT_DIR} && bun install && bun pm trust --all" >&2
  exit 1
fi

if [[ ! -f "${INDEX_PATH}" ]]; then
  echo "ERROR: index not found at ${INDEX_PATH}." >&2
  echo "  Fix: tools/wiki-index/refresh-bm25-index.sh" >&2
  exit 1
fi

export INDEX_PATH
export QMD_FORCE_CPU="${QMD_FORCE_CPU:-1}"

# Note: --full-path is deliberately NOT passed. It resolves each hit's qmd://
# reference to an absolute filesystem path, but that resolution needs the
# original collection config (QMD_CONFIG_DIR) that built the index, which is
# a throwaway temp dir by design (see refresh-bm25-index.sh) — outside that
# context it always fails and just adds a noisy warning. The qmd://<path>:<line>
# reference every hit already carries is a sufficient, stable citation.
exec node "${QMD_BIN}" "$@"
