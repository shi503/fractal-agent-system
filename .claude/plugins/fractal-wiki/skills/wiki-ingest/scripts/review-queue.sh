#!/usr/bin/env bash
# review-queue.sh — risk-based quarantine for LLM-written wiki edits.
#
# An LLM editing a wiki page can silently do damage: overwrite a page instead of
# merging into it, shrink a page's content substantially, or drop its provenance
# frontmatter. This script is the deterministic gate in front of any such edit —
# it never judges content quality, only three mechanical risk signals — and
# quarantines a risky edit under _review-queue/ instead of letting it land.
#
# Risk signals (any one trips quarantine):
#   1. Shrink   — the proposed new body is less than 50% the size (byte count,
#                 frontmatter excluded) of the current target's body.
#   2. Dropped provenance — the current target has a non-empty `source:` and/or
#                 `created_by:` frontmatter key that the proposed new content lacks.
#   3. --overwrite flag passed explicitly by the caller (the caller knows this is
#                 a full replace, not a merge, and wants the risk check to apply
#                 unconditionally regardless of size).
#
# Usage:
#   review-queue.sh apply <target-path> <new-content-path> [--actor INITIALS] [--reason TEXT] [--overwrite]
#       Applies the edit directly if not risky; quarantines it under _review-queue/
#       if risky. Exit 0 = applied in place. Exit 2 = quarantined (not an error —
#       check the exit code, not just stderr).
#
#   review-queue.sh approve <queue-id> [--actor INITIALS]
#       Moves a quarantined edit into its recorded target path. Marks APPROVED.
#
#   review-queue.sh reject <queue-id> [--actor INITIALS] --reason TEXT
#       Discards a quarantined edit (target is left untouched). Marks REJECTED.
#
#   review-queue.sh list
#       Prints all PENDING entries from the manifest.
#
# Manifest: _review-queue/QUEUE.md, one row per action, append-only. The
# quarantined content itself is saved at _review-queue/<queue-id>--<basename>.
#
# All paths are resolved relative to the current working directory — run this
# from the repo (or fixture-copy) root you want the queue anchored to.
set -euo pipefail

QUEUE_DIR="_review-queue"
MANIFEST="${QUEUE_DIR}/QUEUE.md"
SHRINK_RATIO="0.50"

ensure_manifest() {
  mkdir -p "${QUEUE_DIR}"
  if [[ ! -f "${MANIFEST}" ]]; then
    cat > "${MANIFEST}" <<'EOF'
# Wiki Review Queue

Risk-based quarantine for LLM-written wiki edits (shrink / overwrite / dropped-provenance).
Append-only manifest. Do not edit existing rows — approve/reject appends a new row instead.

| Date | Status | Queue ID | Target | Reason | Actor |
|------|--------|----------|--------|--------|-------|
EOF
  fi
}

body_only() {
  # Strip a leading YAML frontmatter block (--- ... ---), print the rest.
  awk '
    NR==1 && $0=="---" { infm=1; next }
    infm && $0=="---" { infm=0; next }
    infm { next }
    { print }
  ' "$1"
}

frontmatter_value() {
  # frontmatter_value <file> <key> — prints the raw value of a top-level frontmatter key, or "".
  awk -v key="$2" '
    NR==1 && $0=="---" { infm=1; next }
    infm && $0=="---" { exit }
    infm && $0 ~ "^"key":" { sub("^"key":[ ]*", ""); print; exit }
  ' "$1"
}

cmd_apply() {
  local target="$1" newfile="$2"
  shift 2
  local actor="unknown" reason="" force_overwrite=0
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --actor) actor="$2"; shift 2 ;;
      --reason) reason="$2"; shift 2 ;;
      --overwrite) force_overwrite=1; shift ;;
      *) echo "ERROR: unknown flag: $1" >&2; exit 2 ;;
    esac
  done

  if [[ ! -f "${newfile}" ]]; then
    echo "ERROR: new-content file not found: ${newfile}" >&2
    exit 2
  fi

  local risky=0
  local risk_reasons=()

  if [[ -f "${target}" ]]; then
    local old_body_size new_body_size
    old_body_size=$(body_only "${target}" | wc -c | tr -d ' ')
    new_body_size=$(body_only "${newfile}" | wc -c | tr -d ' ')

    if [[ "${old_body_size}" -gt 0 ]]; then
      # Integer-safe: new*2 < old  <=>  new < old*0.5
      if (( new_body_size * 2 < old_body_size )); then
        risky=1
        risk_reasons+=("shrink: ${old_body_size}B -> ${new_body_size}B (>${SHRINK_RATIO} reduction)")
      fi
    fi

    local old_source old_created_by new_source new_created_by
    old_source="$(frontmatter_value "${target}" "source")"
    old_created_by="$(frontmatter_value "${target}" "created_by")"
    new_source="$(frontmatter_value "${newfile}" "source")"
    new_created_by="$(frontmatter_value "${newfile}" "created_by")"

    if [[ -n "${old_source}" && -z "${new_source}" ]]; then
      risky=1
      risk_reasons+=("dropped-provenance: source: present in target, absent in new content")
    fi
    if [[ -n "${old_created_by}" && -z "${new_created_by}" ]]; then
      risky=1
      risk_reasons+=("dropped-provenance: created_by: present in target, absent in new content")
    fi
  fi

  if [[ "${force_overwrite}" -eq 1 ]]; then
    risky=1
    risk_reasons+=("explicit --overwrite flag")
  fi

  if [[ "${risky}" -eq 0 ]]; then
    mkdir -p "$(dirname "${target}")"
    cp "${newfile}" "${target}"
    echo "Applied in place: ${target}"
    exit 0
  fi

  ensure_manifest
  local qid dest
  # Timestamp plus pid+random suffix: two quarantines within the same second
  # (same-second CI batches, scripted demos) must not collide on queue id.
  qid="$(date -u +%Y%m%dT%H%M%SZ)-$$-${RANDOM}"
  dest="${QUEUE_DIR}/${qid}--$(basename "${target}")"
  cp "${newfile}" "${dest}"

  local combined_reason
  combined_reason="${reason:+${reason}; }$(IFS='; '; echo "${risk_reasons[*]}")"

  printf '| %s | PENDING | %s | %s | %s | %s |\n' \
    "$(date -u +%Y-%m-%d)" "${qid}" "${target}" "${combined_reason}" "${actor}" >> "${MANIFEST}"

  echo "QUARANTINED: ${dest}"
  echo "Reason: ${combined_reason}"
  echo "Target left untouched: ${target}"
  echo "Manifest: ${MANIFEST} (queue id: ${qid})"
  exit 2
}

find_manifest_row() {
  local qid="$1"
  grep -F "| ${qid} |" "${MANIFEST}" 2>/dev/null | tail -1
}

cmd_approve() {
  local qid="$1"; shift
  local actor="unknown"
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --actor) actor="$2"; shift 2 ;;
      *) echo "ERROR: unknown flag: $1" >&2; exit 2 ;;
    esac
  done

  local row target queued_file
  row="$(find_manifest_row "${qid}")"
  if [[ -z "${row}" ]]; then
    echo "ERROR: no manifest row found for queue id ${qid}" >&2
    exit 2
  fi
  target="$(echo "${row}" | awk -F' \\| ' '{print $4}')"
  queued_file=$(ls "${QUEUE_DIR}/${qid}--"* 2>/dev/null | head -1 || true)

  if [[ -z "${queued_file}" || ! -f "${queued_file}" ]]; then
    echo "ERROR: quarantined content not found for queue id ${qid}" >&2
    exit 2
  fi

  mkdir -p "$(dirname "${target}")"
  cp "${queued_file}" "${target}"
  printf '| %s | APPROVED | %s | %s | approved by %s | %s |\n' \
    "$(date -u +%Y-%m-%d)" "${qid}" "${target}" "${actor}" "${actor}" >> "${MANIFEST}"
  echo "Approved and applied: ${target} (from ${queued_file})"
}

cmd_reject() {
  local qid="$1"; shift
  local actor="unknown" reason="no reason given"
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --actor) actor="$2"; shift 2 ;;
      --reason) reason="$2"; shift 2 ;;
      *) echo "ERROR: unknown flag: $1" >&2; exit 2 ;;
    esac
  done

  local row target
  row="$(find_manifest_row "${qid}")"
  if [[ -z "${row}" ]]; then
    echo "ERROR: no manifest row found for queue id ${qid}" >&2
    exit 2
  fi
  target="$(echo "${row}" | awk -F' \\| ' '{print $4}')"

  printf '| %s | REJECTED | %s | %s | %s | %s |\n' \
    "$(date -u +%Y-%m-%d)" "${qid}" "${target}" "${reason}" "${actor}" >> "${MANIFEST}"
  echo "Rejected: queue id ${qid} — target ${target} left untouched."
}

cmd_list() {
  if [[ ! -f "${MANIFEST}" ]]; then
    echo "No review queue manifest at ${MANIFEST} — nothing quarantined yet."
    exit 0
  fi
  grep '| PENDING |' "${MANIFEST}" || echo "No PENDING entries."
}

if [[ $# -lt 1 ]]; then
  echo "Usage: review-queue.sh {apply|approve|reject|list} ..." >&2
  exit 2
fi

SUBCMD="$1"; shift
case "${SUBCMD}" in
  apply)   cmd_apply "$@" ;;
  approve) cmd_approve "$@" ;;
  reject)  cmd_reject "$@" ;;
  list)    cmd_list "$@" ;;
  *) echo "ERROR: unknown subcommand: ${SUBCMD}" >&2; exit 2 ;;
esac
