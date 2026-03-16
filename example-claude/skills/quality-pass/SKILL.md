---
name: quality-pass
description: "Review recent changes for AI slop and code quality issues. Run after implementation, before handoff."
argument-hint: "[optional: file or directory scope]"
disable-model-invocation: true
allowed-tools:
  - Bash(git diff *)
  - Read
  - Grep
  - Glob
  - Edit
---

# Quality Pass — Code Quality Cleanup

## Purpose

Identify and remove "AI slop" introduced since the last commit **without** changing intended behavior, product logic, or security posture.

This command is for **code quality cleanup**. It is **not** a refactor, redesign, or feature change tool. Run it after implementing a workstream and before `/handoff`.

## Safety Rules (Non-Negotiable)

- **No sensitive data leakage:** Never print, log, or paste credentials, tokens, API keys, connection strings, or PII into output. Redact with placeholders (e.g. `[REDACTED]`).
- **Do not weaken controls:** Do not reduce authentication, authorization, input validation, encryption, or audit logging.
- **Config remains externalized:** Do not introduce hardcoded secrets or environment-specific configuration.
- **Preserve observability:** Do not remove transaction/request IDs, structured logging, metrics, or health checks unless they are clearly redundant.

## What Counts as "Slop" (Remove/Correct)

### 1) Commentary and Noise

- Excessive comments a human wouldn't write (tutorial-like, redundant, narrating obvious code)
- Comments that conflict with existing file tone/conventions
- Generated boilerplate text (e.g. "This function does X" when the name already says it)

### 2) Unnecessary Defensive Code

- Extra `try/catch` blocks where the codebase convention relies on centralized error handling
- Redundant null/undefined checks when callers are trusted/validated by design
- Over-verbose guard clauses added "just in case" that don't match surrounding patterns

### 3) Type/Correctness Workarounds

- `any` casts or unsafe assertions used to silence type errors instead of fixing types properly
- Over-broad types (e.g. `Record<string, any>`) introduced without necessity

### 4) Style / Consistency Violations

- Formatting or naming inconsistent with the file/module conventions
- Duplicate helpers or repeated patterns that already exist elsewhere (prefer existing utilities)
- Language-specific issues:
  - **TypeScript:** Avoid dynamic requires; keep imports consistent with project conventions
  - **Python:** Inline imports moved to file top with other imports (unless intentionally lazy-loaded)

### 5) Suspicious Changes (Flag, Don't Fix Blindly)

- Changes that alter auth, RBAC, billing, entitlements, logging redaction, or provenance behavior
- Changes that affect database migrations, schema, or queries
- Changes that add/remove telemetry, transaction IDs, or audit logging

If found: **stop** and report as a potential risk rather than making speculative edits.

## Process

1. **Compute diff** — `git diff main...HEAD` (or `git diff HEAD` for uncommitted changes)
2. **Review each changed file** — Scan for the slop patterns above. Keep legitimate changes intact; only remove noise/inconsistencies.
3. **Make minimal edits** — Small, targeted changes only. Do not reformat entire files unless necessary for a slop fix.
4. **Validate** — Run the project's standard checks (lint, build, typecheck) if available. Ensure build still passes.
5. **Report** — Provide a brief summary of what changed.

## Output Format (required)

- **Summary** (1–3 sentences)
- **Files Changed** (list)
- **Flags / Risks** (if any suspicious changes were detected)

<!--
## SOC2 / Enterprise Compliance Checks (Optional)

Uncomment this section for projects with SOC2, BAA, or enterprise compliance requirements.
These checks run as part of the quality pass and are reported in the output.

### Additional Safety Rules
- Supply chain: Containers must use approved base images (e.g. Chainguard). No ad-hoc bases.
- Observability: Emit structured logs with request/transaction ID propagation; provide
  deep health checks (downstream reachability) and /metrics endpoints.
- Deployability: Startup must run idempotent DB migrations; fail fast if migrations fail.
  Downgrades must be possible without destroying state.

### Compliance Scan Commands
Run these against the diff and report results:

```bash
# Secrets scan — no credentials in committed code
grep -rn 'password\|secret\|api_key\|token\|credential\|connection_string' \
  --include='*.ts' --include='*.py' --include='*.go' --include='*.rs' \
  $(git diff --name-only main...HEAD) 2>/dev/null | \
  grep -iv 'test\|mock\|example\|\.env\.example\|type\|interface' || echo "PASS: No secrets detected"

# PII/PHI scan — no sensitive identifiers in logs or output
grep -rn 'patient_name\|ssn\|mrn\|date_of_birth\|social_security' \
  --include='*.ts' --include='*.py' --include='*.go' \
  $(git diff --name-only main...HEAD) 2>/dev/null | \
  grep -iv 'test\|mock\|type\|interface\|schema' || echo "PASS: No PII/PHI detected"

# Hardcoded config scan — no environment-specific values
grep -rn 'localhost:\|127\.0\.0\.1\|0\.0\.0\.0' \
  --include='*.ts' --include='*.py' --include='*.go' \
  $(git diff --name-only main...HEAD) 2>/dev/null | \
  grep -iv 'test\|\.env\|config\.example\|README' || echo "PASS: No hardcoded config"
```

### Enterprise Guardrails Checklist
- [ ] No sensitive data (credentials, PHI/PII, document contents) in logs, traces, errors, or metrics
- [ ] All environment-specific config comes from env vars or approved secret managers
- [ ] Structured logs use ISO 8601 timestamps and include: ts, level, service, request_id, msg
- [ ] No hidden/implicit dependencies between services
- [ ] Version tags follow SemVer or date-hash format
- [ ] Startup runs idempotent DB migrations; fails fast on migration failure

Add scan results to the HANDOFF.md Verification Evidence table:
| Compliance scan | [scan commands above] | PASS/FAIL | [details] |
-->
