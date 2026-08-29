#!/usr/bin/env bash
# update-source-provenance.sh — stamp or refresh provenance frontmatter on a wiki/sources/ page.
#
# On first ingest, created_by is written by new-source.sh. On re-ingest of a source
# that already exists, this script updates (or adds) updated_by + updated frontmatter.
#
# Usage:
#   update-source-provenance.sh <source-page-path>
#     <source-page-path>   Absolute or relative path to wiki/sources/<slug>.md
set -euo pipefail

# Provenance initials. Resolution order:
#   1. Real "First Last" name (contains whitespace) -> first letter of each ("Alex Rivera" -> AR).
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

if [[ $# -lt 1 ]]; then
  echo "Usage: update-source-provenance.sh <source-page-path>" >&2
  exit 2
fi

SRC="$1"
if [[ ! -f "${SRC}" ]]; then
  echo "ERROR: file not found: ${SRC}" >&2
  exit 2
fi

DATE="$(date +%Y-%m-%d)"
AUTHOR="$(derive_initials)"

# Use awk to insert/update updated_by and updated fields within the YAML frontmatter.
# Strategy: locate the closing '---' of the frontmatter block and insert before it
# (or update existing fields in-place).
TMPFILE="$(mktemp)"

awk -v date="${DATE}" -v author="${AUTHOR}" '
BEGIN { in_front=0; found_front_end=0; added=0; has_updated_by=0; has_updated=0 }
/^---$/ && !found_front_end {
  if (!in_front) { in_front=1; print; next }
  # closing ---: inject missing fields before it
  if (!has_updated_by) { print "updated_by: \"" author "\"" }
  if (!has_updated)    { print "updated: \"" date "\"" }
  found_front_end=1; print; next
}
in_front && !found_front_end && /^updated_by:/ {
  has_updated_by=1
  print "updated_by: \"" author "\""
  next
}
in_front && !found_front_end && /^updated:/ {
  has_updated=1
  print "updated: \"" date "\""
  next
}
{ print }
' "${SRC}" > "${TMPFILE}"

mv "${TMPFILE}" "${SRC}"
echo "Provenance updated: updated_by=${AUTHOR}, updated=${DATE} in ${SRC}"
