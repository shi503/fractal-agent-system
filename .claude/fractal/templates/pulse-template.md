# PULSE — {WorkstreamName}

Append-only heartbeat log. One JSON block per entry. Write at ~30-minute intervals or at task boundaries (whichever comes first).

**Rules:**
- Never mutate prior entries. Append only.
- `status` must be one of: `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `IN_REVIEW`, `COMPLETE`.
- `tasks_completed` is `done/total` against the PRD acceptance criteria.
- Set `escalation_needed: true` only when `status: BLOCKED` and the blocker is architectural (not a transient build error you can fix yourself).
- This file is gitignored — it lives in the working tree only. The HANDOFF is the permanent record.

---

```json
{
  "timestamp": "YYYY-MM-DDTHH:MM:SSZ",
  "status": "NOT_STARTED",
  "tasks_completed": "0/N",
  "blockers": "none",
  "escalation_needed": false,
  "notes": "kicked off; reading PRD + source files"
}
```

```json
{
  "timestamp": "YYYY-MM-DDTHH:MM:SSZ",
  "status": "IN_PROGRESS",
  "tasks_completed": "2/N",
  "blockers": "none",
  "escalation_needed": false,
  "notes": "AC 1-2 green; starting AC 3"
}
```

```json
{
  "timestamp": "YYYY-MM-DDTHH:MM:SSZ",
  "status": "BLOCKED",
  "tasks_completed": "3/N",
  "blockers": "Agent API auth contract unclear on key-rotation header — need design review before wiring the route",
  "escalation_needed": true,
  "notes": "stopping; surfacing to Architect"
}
```

```json
{
  "timestamp": "YYYY-MM-DDTHH:MM:SSZ",
  "status": "COMPLETE",
  "tasks_completed": "N/N",
  "blockers": "none",
  "escalation_needed": false,
  "notes": "CI gate PASS; writing HANDOFF.md"
}
```
