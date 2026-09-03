# Evidence: {workstream-id}

**Blueprint:** `{EPIC-ID}`
**Workstream id:** `{workstream-id}`
**Accepted:** no

> Dependents become ready only when **Accepted** is yes (Architect or
> installer equivalent signed off). This file is the record — not a PRD
> Status field, not a self-assessment.

---

## Work completed

- Specific outcome: path, symbol, or behavior
- Specific outcome: path, symbol, or behavior

---

## Work not completed

- In-scope item left undone, and why
- Or: None

---

## Technical debt

- Shortcut, TODO, or follow-up
- Or: None

---

## Key decisions / deviations

| Decision | Rationale | Deviation from PRD |
|----------|-----------|--------------------|
| Chose X instead of Y | Why | yes / no |

---

## Layer 1 — command table

Paste real stdout/stderr. A row with Result=PASS and empty Output is invalid.

| Gate | Command | Result | Output (paste) |
|------|---------|--------|----------------|
| lint | `{lint}` | PASS / FAIL / N/A | |
| build | `{build}` | PASS / FAIL | |
| typecheck | `{typecheck}` | PASS / FAIL / N/A | |
| test | `{test}` | PASS / FAIL / N/A | |

If output is long, keep the table row as PASS/FAIL and paste the tail below:

### lint

```text
(paste)
```

### build

```text
(paste)
```

### typecheck

```text
(paste)
```

### test

```text
(paste)
```
