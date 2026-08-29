#!/usr/bin/env bash
# router-smoke.sh — end-to-end smoke test for ROUTING_LOGIC/router.py.
#
# Exercises init/next/update/status/pulse against the fixture blueprints
# and the target's own demo blueprint, and asserts the dependency-edge
# behavior: a workstream's dependents must not appear from `next` until
# the workstream they depend on is marked COMPLETE.
#
# Runs against a throwaway copy of router.py in a temp directory, so its
# .state.json never touches the real .claude/fractal/.state.json.
#
# Usage: bash tools/router-smoke.sh
# Run from the repo root (paths below are repo-relative).
set -euo pipefail
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

ROUTER_SRC="$REPO_ROOT/ROUTING_LOGIC/router.py"
P1_FLAT="$REPO_ROOT/fixtures/taskflow/blueprints/BLUEPRINT-NOVA-P1-NotificationCore.yaml"
P3_PHASED="$REPO_ROOT/fixtures/taskflow/blueprints/BLUEPRINT-NOVA-P3-Hardening.yaml"
DEMO_PHASED="$REPO_ROOT/.claude/fractal/BLUEPRINT-Example.yaml"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

cp "$ROUTER_SRC" "$WORK/router.py"

run() {
  # run <blueprint-path> <router-args...>
  local bp="$1"; shift
  python3 "$WORK/router.py" --blueprint "$bp" "$@"
}

echo "== 1/7: init against the P1 fixture (flat shape) =="
run "$P1_FLAT" init

echo ""
echo "== 2/7: next BEFORE WS-1 is COMPLETE — dependents must not surface =="
BEFORE="$(run "$P1_FLAT" next)"
echo "$BEFORE"
if echo "$BEFORE" | grep -qE 'FeatureLead-EventFanout|FeatureLead-PreferenceCenter'; then
  echo "FAIL: WS-2/WS-3 surfaced before WS-1 (NotificationSchema) is COMPLETE" >&2
  exit 1
fi
if ! echo "$BEFORE" | grep -q 'FeatureLead-NotificationSchema'; then
  echo "FAIL: WS-1 (NotificationSchema, no deps) did not surface as ready" >&2
  exit 1
fi
echo "OK: dependents correctly withheld pre-update."

echo ""
echo "== 3/7: update WS-1 -> COMPLETE =="
run "$P1_FLAT" update FeatureLead-NotificationSchema COMPLETE

echo ""
echo "== 4/7: next AFTER WS-1 is COMPLETE — dependents must surface =="
AFTER="$(run "$P1_FLAT" next)"
echo "$AFTER"
if ! echo "$AFTER" | grep -q 'FeatureLead-EventFanout'; then
  echo "FAIL: EventFanout (WS-2) did not surface after WS-1 COMPLETE" >&2
  exit 1
fi
if ! echo "$AFTER" | grep -q 'FeatureLead-PreferenceCenter'; then
  echo "FAIL: PreferenceCenter (WS-3) did not surface after WS-1 COMPLETE" >&2
  exit 1
fi
echo "OK: dependency edge respected — both dependents now ready."

echo ""
echo "== 5/7: status =="
run "$P1_FLAT" status

echo ""
echo "== 6/7: pulse against a synthetic PULSE.md =="
cat > "$WORK/PULSE.md" <<'EOF'
```json
{"timestamp": "2026-01-01T00:00:00Z", "status": "IN_PROGRESS", "tasks_completed": "1/3", "blockers": "none", "escalation_needed": false}
```
EOF
python3 "$WORK/router.py" pulse "$WORK/PULSE.md"

echo ""
echo "== 7/7: both blueprint shapes init cleanly =="
echo "-- phased fixture (BLUEPRINT-NOVA-P3-Hardening.yaml) --"
run "$P3_PHASED" init
echo "-- target demo blueprint (.claude/fractal/BLUEPRINT-Example.yaml, phased shape) --"
run "$DEMO_PHASED" init

echo ""
echo "ALL SMOKE CHECKS PASSED"
