# PRD: {workstream-id}

**Blueprint:** `{EPIC-ID}`
**Workstream id:** `{workstream-id}`
**Depends on:** `{id}` (evidence accepted) · or `none`

> Status is not stored on this PRD. Readiness comes from accepted evidence
> on `depends_on` workstreams. Do not add a Status field as source of truth.

---

## Feature overview

One paragraph: what this workstream produces and why it exists in the epic.
Reference surrounding systems by path. Do not paste large guide files inline.

**Guides (path only):**
- `{project-guides}/relevant-guide.md`

---

## Acceptance criteria

Binary, verifiable. Must cover (and may refine) the BLUEPRINT `acceptance` bullets.

- [ ] Specific outcome 1
- [ ] Specific outcome 2
- [ ] CI gate passes (see below)

---

## File manifest

Exhaustive. If a file is not listed, it is out of scope.

### Read

- `path/to/existing-file.ts` — why it must be read first

### Write

- `path/to/existing-file.ts` — what may change

### Create

- `path/to/new-file.ts` — what this workstream adds

---

## CI gate

Commands that must pass before evidence can be submitted. Adapt to the project toolchain. At minimum, the primary build command must PASS.

```text
{build} && {typecheck} && {lint} && {test}
```

Paste the full command output into the workstream evidence Layer 1 table. Self-assessment is not evidence.

---

## Out of scope

- Explicit exclusion 1 (and why)
- Files or features owned by another workstream id

---

## Blockers

Issues that prevent progress. `None` if unblocked.

- None
