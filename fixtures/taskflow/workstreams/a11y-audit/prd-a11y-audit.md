# PRD — A11yAudit

**Blueprint:** `blueprints/BLUEPRINT-NOVA-P3-Hardening.yaml`
**Workstream ID:** `WS-8`
**Model tier:** `haiku`
**Owner:** Feature Lead (SP)
**Depends on:** `[WS-7]`
**Status:** `NOT_STARTED`

> **FIXTURE.** Synthetic PRD for the TaskFlow NOVA fixture corpus. Nothing here describes real work.

---

## 1. Feature Overview

Audit the three surfaces NOVA added — the toast stack, the preference center, and the merge review queue — against WCAG 2.2 AA, and file each finding with a reproduction path and an owning workstream. It runs after the load harness so the audit sees the surfaces at realistic data volume rather than with three seeded rows.

**Source documents:**
- `wiki/synthesis/notification-fatigue-principles.md`
- `wiki/raw/2026/08/2026-08-08-SP-preference-center-sketch.md`

**Locked decisions:**
- `D-0002`: the digest surface is the primary reading path, so it is the primary audit target.

## 2. Acceptance Criteria

- [ ] Every NOVA surface has a recorded axe run with zero critical violations.
- [ ] A screen-reader pass is documented for the merge review queue.
- [ ] Each finding lists a reproduction path and an owning workstream.

## 3. Read / Write File Manifest

**Read only:** `components/notifications/`, `components/vault/`, `app/(dashboard)/settings/notifications/`
**Write / modify:** none
**Create:** `docs/a11y/nova-audit.md`, `docs/a11y/findings.json`

## 4. CI Gate

```bash
npm run build && npm run test:e2e
```

Reduced gate: this workstream ships documentation and a findings file; no application source changes, so lint and unit tests are unaffected.

## 5. Session Protocol

Heartbeat to `PULSE.md` every ~30 min or at task boundaries. On completion generate `HANDOFF.md`. On block set `escalation_needed: true` and stop.

## 6. Out of Scope

- Fixing the findings — each becomes its own follow-up workstream.
- Auditing pre-NOVA surfaces.

## 7. Blockers

**Blockers:** None
