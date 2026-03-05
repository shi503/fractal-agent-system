# PULSE.md - Structured Heartbeat Log

This document is a structured log of the Feature Lead's progress. It is appended to by the Feature Lead at regular intervals (e.g., every 30 minutes) to provide a lightweight, machine-readable status update to the Architect.

---

```json
{
  "timestamp": "2026-02-27 21:00:00 UTC",
  "status": "IN_PROGRESS",
  "tasks_completed": "1/5",
  "blockers": "none",
  "escalation_needed": false
}
```

```json
{
  "timestamp": "2026-02-27 21:30:00 UTC",
  "status": "IN_PROGRESS",
  "tasks_completed": "2/5",
  "blockers": "none",
  "escalation_needed": false
}
```

```json
{
  "timestamp": "2026-02-27 22:00:00 UTC",
  "status": "BLOCKED",
  "tasks_completed": "2/5",
  "blockers": "Database connection timeout",
  "escalation_needed": true
}
```
