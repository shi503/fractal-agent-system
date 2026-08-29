#!/usr/bin/env bash
# normalize-raw.sh — enforce the raw-file naming convention on a raw drop.
#
# Convention: wiki/raw/{YYYY}/{MM}/{YYYY-MM-DD}-{INITIALS}-{slug}.{ext}
#   - Flat wiki/raw/ is valid when total file count is below the FLAT_THRESHOLD (20).
#   - Month subfolders {YYYY}/{MM}/ are created automatically beyond the threshold.
#
# Usage:
#   normalize-raw.sh <path-to-raw-file>
#     <path>   Absolute or relative path to the dropped file.
#
# Output:
#   Prints the canonical path (renamed if non-conforming, unchanged if already correct).
#   Exits 0 on success; exits non-zero on error.
#
# Initials auto-derived from git config user.name / user.email; prompts if unavailable.
set -euo pipefail

FLAT_THRESHOLD=20

find_repo_root() {
  local dir
  dir="$(cd "$(dirname "${1}")" && pwd)"
  while [[ "${dir}" != "/" ]]; do
    if [[ -d "${dir}/wiki" && -f "${dir}/wiki/log.md" ]]; then echo "${dir}"; return 0; fi
    dir="$(dirname "${dir}")"
  done
  # Fallback: search upward from PWD
  dir="${PWD}"
  while [[ "${dir}" != "/" ]]; do
    if [[ -d "${dir}/wiki" && -f "${dir}/wiki/log.md" ]]; then echo "${dir}"; return 0; fi
    dir="$(dirname "${dir}")"
  done
  echo "ERROR: could not locate repo root (no wiki/log.md found)." >&2
  return 1
}

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

# Pattern: YYYY-MM-DD-INITIALS-slug.ext  (flat or in a YYYY/MM/ subfolder)
CONVENTION_PATTERN='^[0-9]{4}-[0-9]{2}-[0-9]{2}-[A-Z??]{2,4}-.+\.[a-zA-Z0-9]+$'

if [[ $# -lt 1 ]]; then
  echo "Usage: normalize-raw.sh <path-to-raw-file>" >&2
  exit 2
fi

INPUT_PATH="$1"
if [[ ! -f "${INPUT_PATH}" ]]; then
  echo "ERROR: file not found: ${INPUT_PATH}" >&2
  exit 2
fi

ROOT="$(find_repo_root "${INPUT_PATH}")" || exit 1
RAW_DIR="${ROOT}/wiki/raw"
ABS_INPUT="$(cd "$(dirname "${INPUT_PATH}")" && pwd)/$(basename "${INPUT_PATH}")"
FILENAME="$(basename "${ABS_INPUT}")"
EXT="${FILENAME##*.}"
BASENAME="${FILENAME%.*}"

# Check if the file is already under wiki/raw/ (flat or subfoldered)
if [[ "${ABS_INPUT}" != "${RAW_DIR}/"* ]]; then
  echo "ERROR: file is not under wiki/raw/: ${ABS_INPUT}" >&2
  exit 2
fi

# Count existing files in wiki/raw/ (excluding README.md, assets/, subdirs)
FILE_COUNT=$(find "${RAW_DIR}" -maxdepth 1 -type f -name "*.md" ! -name "README.md" | wc -l)
FILE_COUNT=$((FILE_COUNT + $(find "${RAW_DIR}" -maxdepth 3 -mindepth 2 -type f ! -name "README.md" | wc -l)))

# Determine target directory (flat vs. month-subfolder)
TODAY="$(date +%Y-%m-%d)"
YYYY="${TODAY:0:4}"
MM="${TODAY:5:2}"

if [[ ${FILE_COUNT} -ge ${FLAT_THRESHOLD} ]]; then
  TARGET_DIR="${RAW_DIR}/${YYYY}/${MM}"
else
  TARGET_DIR="${RAW_DIR}"
fi

# Check if filename already conforms
if echo "${FILENAME}" | grep -Eq "${CONVENTION_PATTERN}"; then
  # Already conforming — may need to move to correct subfolder if volume threshold crossed
  if [[ "$(dirname "${ABS_INPUT}")" == "${TARGET_DIR}" ]]; then
    echo "${ABS_INPUT}"
    exit 0
  fi
  # File is in wrong location (e.g. flat but should be subfoldered)
  mkdir -p "${TARGET_DIR}"
  DEST="${TARGET_DIR}/${FILENAME}"
  if [[ "${ABS_INPUT}" != "${DEST}" ]]; then
    mv "${ABS_INPUT}" "${DEST}"
    echo "Moved: ${ABS_INPUT} → ${DEST}" >&2
  fi
  echo "${DEST}"
  exit 0
fi

# Non-conforming: build a canonical name
INITIALS="$(derive_initials)"

# Attempt to extract a date prefix if present
DATE_PREFIX=""
if echo "${BASENAME}" | grep -Eq '^[0-9]{4}-[0-9]{2}-[0-9]{2}'; then
  DATE_PREFIX="${BASENAME:0:10}"
  SLUG_PART="${BASENAME:11}"
else
  DATE_PREFIX="${TODAY}"
  SLUG_PART="${BASENAME}"
fi

# Slugify: lowercase, replace spaces/underscores/dots with hyphens, collapse repeats
SLUG="$(echo "${SLUG_PART}" | tr '[:upper:]' '[:lower:]' | sed 's/[[:space:]_.]/-/g; s/-\+/-/g; s/^-//; s/-$//')"

CANONICAL_NAME="${DATE_PREFIX}-${INITIALS}-${SLUG}.${EXT}"

mkdir -p "${TARGET_DIR}"
DEST="${TARGET_DIR}/${CANONICAL_NAME}"

if [[ "${ABS_INPUT}" == "${DEST}" ]]; then
  echo "${DEST}"
  exit 0
fi

if [[ -e "${DEST}" ]]; then
  echo "ERROR: target already exists: ${DEST}" >&2
  exit 3
fi

mv "${ABS_INPUT}" "${DEST}"
echo "Normalized: $(basename "${ABS_INPUT}") → ${DEST}" >&2
echo "${DEST}"
