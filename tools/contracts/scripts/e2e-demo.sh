#!/usr/bin/env bash
# e2e-demo.sh — replay one fixture workstream lifecycle end to end
# (init -> IN_PROGRESS -> COMPLETE) through the router CLI, emitting a
# schema-valid event per transition plus one evidence bundle, and gate
# every artifact against its schema.
#
# Router safety: this script NEVER touches the real router state file
# (.claude/fractal/.state.json). It copies the unmodified ROUTING_LOGIC/
# router.py into a throwaway temp directory and runs that copy — router.py
# derives its state-file path from its own script directory, so the copy
# reads/writes a temp .state.json instead. See fractal-protocol.md's
# router.py init foot-gun note: this is exactly the workaround it calls for.
#
# All demo output (temp router state, events log, evidence bundle) is
# written under a mktemp -d directory and removed on exit. Nothing under
# fixtures/taskflow/ is modified — it is only read.
#
# Usage: bash tools/contracts/scripts/e2e-demo.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTRACTS_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${CONTRACTS_DIR}/../.." && pwd)"

ROUTER_SRC="${REPO_ROOT}/ROUTING_LOGIC/router.py"
BLUEPRINT="${REPO_ROOT}/fixtures/taskflow/blueprints/BLUEPRINT-NOVA-P1-NotificationCore.yaml"
VALIDATOR="${SCRIPT_DIR}/validate-contracts.cjs"
EMIT_EVENT="${SCRIPT_DIR}/emit-event.cjs"
BUILD_EVIDENCE="${SCRIPT_DIR}/build-evidence.cjs"
REAL_STATE="${REPO_ROOT}/.claude/fractal/.state.json"

WORKSTREAM_ID="workstream:notification-schema"
FEATURE_LEAD="FeatureLead-NotificationSchema"

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/fractal-e2e-demo.XXXXXX")"
trap 'rm -rf "${TMP_DIR}"' EXIT

echo "== e2e-demo: temp workspace ${TMP_DIR} =="

# --- 0. Snapshot the real router state file (byte-for-byte, before) -------
if [[ -f "${REAL_STATE}" ]]; then
  REAL_STATE_HASH_BEFORE="$(shasum -a 256 "${REAL_STATE}" | awk '{print $1}')"
else
  REAL_STATE_HASH_BEFORE="ABSENT"
fi
echo "== real router state before: ${REAL_STATE_HASH_BEFORE} (${REAL_STATE}) =="

# --- 1. Sandbox the router: unmodified copy in a throwaway directory ------
TMP_ROUTER="${TMP_DIR}/router.py"
cp "${ROUTER_SRC}" "${TMP_ROUTER}"
TMP_STATE="${TMP_DIR}/.state.json"

router() {
  python3 "${TMP_ROUTER}" --blueprint "${BLUEPRINT}" "$@"
}

EVENTS_LOG="${TMP_DIR}/events.jsonl"

echo "-- router init (temp state: ${TMP_STATE}) --"
router init

echo "-- router next (confirms ${FEATURE_LEAD} is ready) --"
router next | tee "${TMP_DIR}/next.txt"
grep -q "${FEATURE_LEAD}" "${TMP_DIR}/next.txt"

echo "-- emit accepted event (NOT_STARTED) --"
node "${EMIT_EVENT}" \
  --workstream-id "${WORKSTREAM_ID}" \
  --router-status NOT_STARTED \
  --log "${EVENTS_LOG}"

echo "-- router update -> IN_PROGRESS --"
router update "${FEATURE_LEAD}" IN_PROGRESS
node "${EMIT_EVENT}" \
  --workstream-id "${WORKSTREAM_ID}" \
  --router-status IN_PROGRESS \
  --message "NotificationSchema migration + idempotency-key contract underway" \
  --log "${EVENTS_LOG}"

echo "-- router update -> COMPLETE --"
router update "${FEATURE_LEAD}" COMPLETE
node "${EMIT_EVENT}" \
  --workstream-id "${WORKSTREAM_ID}" \
  --router-status COMPLETE \
  --message "Migration applied; idempotency-key format documented and unit-tested" \
  --log "${EVENTS_LOG}"

EVENT_COUNT="$(wc -l < "${EVENTS_LOG}" | tr -d ' ')"
echo "== ${EVENT_COUNT} events written to ${EVENTS_LOG} =="

# --- 2. Build one evidence bundle for the completed workstream ------------
TEST_OUTPUT="${TMP_DIR}/pytest-output.txt"
LINT_OUTPUT="${TMP_DIR}/ruff-output.txt"
printf '3 passed, 0 failed in 0.42s\n' > "${TEST_OUTPUT}"
printf 'All checks passed!\n' > "${LINT_OUTPUT}"

EVIDENCE_DIR="${TMP_DIR}/evidence"
node "${BUILD_EVIDENCE}" \
  --workstream-id "${WORKSTREAM_ID}" \
  --out "${EVIDENCE_DIR}" \
  --item "kind=test,subject=notification schema unit tests,uri=${TEST_OUTPUT},result=pass" \
  --item "kind=lint,subject=ruff check,uri=${LINT_OUTPUT},result=pass"

EVIDENCE_COUNT="$(find "${EVIDENCE_DIR}" -name '*.json' | wc -l | tr -d ' ')"
echo "== ${EVIDENCE_COUNT} evidence items written to ${EVIDENCE_DIR} =="

# --- 3. Gate: every event line validates against event.schema.json --------
EVENTS_VALIDATE_DIR="${TMP_DIR}/events-as-files"
node -e '
  const fs = require("fs");
  const path = require("path");
  const [logPath, outDir] = process.argv.slice(1);
  fs.mkdirSync(outDir, { recursive: true });
  const lines = fs.readFileSync(logPath, "utf8").split("\n").filter(Boolean);
  lines.forEach((line, i) => {
    const obj = JSON.parse(line);
    obj.$schemaRef = "event";
    const name = String(i).padStart(3, "0") + ".json";
    fs.writeFileSync(path.join(outDir, name), JSON.stringify(obj, null, 2));
  });
  console.log(lines.length);
' "${EVENTS_LOG}" "${EVENTS_VALIDATE_DIR}"

echo "-- validating events against event.schema.json --"
node "${VALIDATOR}" "${EVENTS_VALIDATE_DIR}"

echo "-- validating evidence bundle against evidence.schema.json --"
node "${VALIDATOR}" "${EVIDENCE_DIR}"

# --- 4. Prove the real router state file was never touched ----------------
if [[ -f "${REAL_STATE}" ]]; then
  REAL_STATE_HASH_AFTER="$(shasum -a 256 "${REAL_STATE}" | awk '{print $1}')"
else
  REAL_STATE_HASH_AFTER="ABSENT"
fi
echo "== real router state after:  ${REAL_STATE_HASH_AFTER} (${REAL_STATE}) =="

if [[ "${REAL_STATE_HASH_BEFORE}" != "${REAL_STATE_HASH_AFTER}" ]]; then
  echo "FAIL: real router state file changed during the demo." >&2
  exit 1
fi

echo "== e2e-demo: PASS — ${EVENT_COUNT} events, ${EVIDENCE_COUNT} evidence items, all valid; real router state unchanged =="
