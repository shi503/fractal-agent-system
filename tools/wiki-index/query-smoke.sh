#!/usr/bin/env bash
# query-smoke.sh — deterministic gate for the committed wiki BM25 index.
#
# Runs three canned queries against tools/wiki-index/taskflow.sqlite (BM25,
# no model load) and checks:
#   1. each query returns at least one ranked hit
#   2. the three queries' TOP hits are three DISTINCT documents
#
# Prints the top hit per query either way. Exit 0 = both checks pass for all
# three queries. Exit 1 = a query returned nothing, or two top hits collided
# on the same document.
#
# Usage: bash tools/wiki-index/query-smoke.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WRAP="${SCRIPT_DIR}/qmd-search.sh"

QUERIES=(
  "websocket fanout latency"
  "offline conflict resolution"
  "notification preference defaults"
)

top_docs=()
fail=0

echo "Query smoke test — tools/wiki-index/taskflow.sqlite"
echo ""

for q in "${QUERIES[@]}"; do
  echo "=== Query: \"${q}\" ==="
  OUT="$(bash "${WRAP}" search "${q}" 2>&1)"
  echo "${OUT}"
  echo ""

  # First result line has the shape: qmd://<collection>/<path>:<line> #<docid>
  FIRST_REF="$(echo "${OUT}" | grep -m1 '^qmd://' || true)"
  if [[ -z "${FIRST_REF}" ]]; then
    echo "FAIL: no ranked hit for \"${q}\"" >&2
    fail=1
    top_docs+=("<none>")
    continue
  fi

  TOP_DOC="$(echo "${FIRST_REF}" | sed -E 's#^(qmd://[^:]+):.*#\1#')"
  top_docs+=("${TOP_DOC}")
  echo "Top hit: ${TOP_DOC}"
  echo ""
done

echo "=== Summary ==="
for i in "${!QUERIES[@]}"; do
  printf '%-38s -> %s\n' "${QUERIES[$i]}" "${top_docs[$i]}"
done
echo ""

# Distinctness check: all three top docs must differ pairwise.
if [[ "${top_docs[0]}" == "${top_docs[1]}" || \
      "${top_docs[0]}" == "${top_docs[2]}" || \
      "${top_docs[1]}" == "${top_docs[2]}" ]]; then
  echo "FAIL: top hits are not three distinct documents." >&2
  fail=1
fi

if [[ "${fail}" -eq 0 ]]; then
  echo "PASS: 3/3 queries returned hits; 3 distinct top documents."
  exit 0
else
  exit 1
fi
