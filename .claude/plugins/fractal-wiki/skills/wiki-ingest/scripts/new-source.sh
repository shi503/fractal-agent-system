#!/usr/bin/env bash
# new-source.sh — scaffold a source-summary page and append the log line for the ingest loop.
# Creates wiki/sources/<slug>.md from a template, then appends a dated row to wiki/log.md.
# The LLM fills the summary body; this script only does the deterministic file/log bookkeeping.
#
# Usage:
#   new-source.sh <slug> <raw-relpath> "<one-line summary>"
#     <slug>         kebab-case page name (becomes wiki/sources/<slug>.md)
#     <raw-relpath>  path of the ingested file under wiki/raw/ (for the source link)
#     <summary>      one-line summary recorded in wiki/log.md
#
# Stamps created_by frontmatter from git identity (user.name / user.email).
set -euo pipefail

find_repo_root() {
  local dir="${PWD}"
  while [[ "${dir}" != "/" ]]; do
    if [[ -d "${dir}/wiki" && -f "${dir}/wiki/log.md" ]]; then echo "${dir}"; return 0; fi
    dir="$(dirname "${dir}")"
  done
  echo "ERROR: could not locate repo root (no wiki/log.md found above ${PWD})." >&2
  return 1
}

# Provenance initials. Resolution order:
#   1. Real "First Last" name (contains whitespace) -> first letter of each:
#        "Alex Rivera" -> AR,  "Rowan Vance" -> RV.
#   2. Username-form name (e.g. "arivera-eng", no space) -> email local-part's leading
#      letters before any separator ("arivera@..." -> AR). A single token is NOT treated as
#      initials — that produced the single-letter bug this guards against.
#   3. Else first two chars of whatever name is set.
#   4. Prompt if interactive, else "??".
derive_initials() {
  local git_name git_email
  git_name="$(git config --global user.name 2>/dev/null || git config user.name 2>/dev/null || true)"
  git_email="$(git config --global user.email 2>/dev/null || git config user.email 2>/dev/null || true)"

  if [[ "${git_name}" == *[[:space:]]* ]]; then
    local -a _w
    read -r -a _w <<< "${git_name}"
    if [[ ${#_w[@]} -ge 2 && -n "${_w[1]}" ]]; then
      printf '%s' "${_w[0]:0:1}${_w[1]:0:1}" | tr '[:lower:]' '[:upper:]'
      return 0
    fi
  fi

  if [[ -n "${git_email}" ]]; then
    local prefix="${git_email%%@*}"
    prefix="${prefix%%[-_.]*}"
    printf '%s' "${prefix:0:2}" | tr '[:lower:]' '[:upper:]'
    return 0
  fi

  if [[ -n "${git_name}" ]]; then
    printf '%s' "${git_name:0:2}" | tr '[:lower:]' '[:upper:]'
    return 0
  fi

  if [[ -t 0 ]]; then
    read -r -p "Enter your initials for provenance (e.g. AR): " user_initials
    printf '%s' "${user_initials}" | tr '[:lower:]' '[:upper:]'
  else
    printf '%s' "??"
  fi
}

if [[ $# -lt 3 ]]; then
  echo "Usage: new-source.sh <slug> <raw-relpath> \"<one-line summary>\"" >&2
  exit 2
fi

SLUG="$1"; RAW_REL="$2"; SUMMARY="$3"
ROOT="$(find_repo_root)" || exit 1
DATE="$(date +%Y-%m-%d)"
SRC="${ROOT}/wiki/sources/${SLUG}.md"
AUTHOR="$(derive_initials)"

if [[ -e "${SRC}" ]]; then
  echo "ERROR: ${SRC} already exists — choose a different slug or edit in place." >&2
  exit 3
fi

cat > "${SRC}" <<EOF
---
okf_version: "0.2"
type: source
title: "${SLUG}"
tier: sources
source:
  - "wiki/raw/${RAW_REL}"
created: "${DATE}"
updated: "${DATE}"
created_by: "${AUTHOR}"
updated_by: "${AUTHOR}"
status: ACTIVE
---

# ${SLUG}

> Source: [\`wiki/raw/${RAW_REL}\`](../raw/${RAW_REL})

## Summary

<!-- LLM: write a faithful 3-8 sentence summary of the source here. Cite section/page where useful. -->

## Key points

<!-- LLM: bulleted extraction of the load-bearing claims. -->

## Cross-links

<!-- LLM: link related wiki/entities/ and wiki/synthesis/ pages with [[wikilinks]]. -->
EOF

# Append-only log row (newest above the trailing marker handled by the LLM; here we append at EOF tail-safe).
printf '| %s | ingest | wiki/sources/%s.md | %s |\n' "${DATE}" "${SLUG}" "${SUMMARY}" >> "${ROOT}/wiki/log.md"

echo "Created: ${SRC}"
echo "Author:  ${AUTHOR}"
echo "Logged:  ${DATE} | ingest | wiki/sources/${SLUG}.md | ${SUMMARY}"
echo "NEXT: LLM fills the summary body, then updates wiki/index.md if a new category appeared."
