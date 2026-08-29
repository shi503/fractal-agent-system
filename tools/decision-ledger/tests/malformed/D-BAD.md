---
id: D-BAD
type: discovery
title: "Deliberately malformed fixture — validator must reject this"
owner: unknown-person
status: not_a_real_status
raci:
  responsible: []
created: not-a-timestamp
updated: 2026-08-20T09:15:00Z
created_by: zz
updated_by: AR
---

## Context

This entry exists only to exercise the validator's rejection path. It has
several independent defects on purpose:

- `status` is not in `allowed_statuses`
- `created` is not a valid ISO-8601 datetime
- `raci.responsible` is empty (must be non-empty)
- `created_by` (`zz`, lowercase) is not valid initials
- `owner` (`unknown-person`) does not resolve against `people.yaml`

## Answer

_N/A — this file must never validate._
