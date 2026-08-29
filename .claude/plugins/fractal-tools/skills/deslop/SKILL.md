---
name: deslop
description: "Identify and remove AI slop from code while preserving security posture and intended behavior"
disable-model-invocation: true
allowed-tools:
  - Bash(git diff *)
  - Read
  - Grep
  - Glob
  - Edit
---

# Deslop — Slop Cleanup Command

## Purpose
Identify and remove "AI slop" introduced since the last commit **without** changing intended behavior, product logic, or security posture.

This command is for **code quality cleanup**. It is **not** a refactor, redesign, or feature change tool.

## Safety Rules (Non-Negotiable)
- **No sensitive data leakage:** Never print, log, or paste **credentials**, **tokens**, **API keys**, **connection strings**, or **user document contents** into output. Redact with placeholders (e.g., `***REDACTED***`).
- **Do not weaken controls:** Do not reduce authentication, authorization, input validation, encryption, or audit logging.
- **Config remains externalized:** Do not introduce hardcoded secrets or environment-specific configuration.
- **Preserve observability:** Do not remove transaction/request IDs, structured logging, metrics, or health checks unless they are clearly redundant and inconsistent with established patterns.

## What Counts as "Slop" (Remove/Correct)
### 1) Commentary & Noise
- Excessive comments a human wouldn't write (tutorial-like, redundant, narrating obvious code).
- Comments that conflict with existing file tone/conventions.
- Generated boilerplate text (e.g., "This function does X" when the name already says it).

### 2) Unnecessary Defensive Code
- Extra `try/catch` blocks where the codebase convention relies on centralized error handling.
- Redundant null/undefined checks when callers are trusted/validated by design.
- Over-verbose guard clauses added "just in case" that don't match surrounding patterns.

### 3) Type/Correctness Workarounds
- `any` casts or unsafe assertions used to silence type errors instead of fixing types properly.
- Over-broad types (e.g., `Record<string, any>`) introduced without necessity.

### 4) Style / Consistency Violations
- Formatting or naming inconsistent with the file/module conventions.
- Duplicate helpers, repeated patterns that already exist elsewhere (prefer existing utilities).
- Language-specific style issues:
  - **Python:** inline imports moved to file top with other imports (unless intentionally lazy-loaded for perf).
  - **TypeScript:** avoid dynamic requires; keep imports consistent with project conventions.

### 5) Suspicious Changes (Flag, Don't "Fix" Blindly)
- Changes that alter auth, RBAC, billing, entitlements, logging redaction, or provenance behavior.
- Changes that affect database migrations, schema, or queries.
- Changes that add/remove telemetry, transaction IDs, or audit logging.
If found: **stop** and report as a potential risk rather than making speculative edits.

## Process
1. **Compute diff**
   - `git diff main...HEAD`
2. **Review each changed file**
   - Scan for the slop patterns above.
   - Keep legitimate changes intact; only remove noise/inconsistencies.
3. **Make minimal edits**
   - Small, targeted changes only.
   - Do not reformat entire files unless necessary for a slop fix.
4. **Validate**
   - Run the standard checks relevant to the repo (e.g., `lint`, `test`, `typecheck`) if available.
   - Ensure build still passes and behavior remains consistent.
5. **Report**
   - Provide a 1-3 sentence summary of what changed.
   - List files touched.
   - If risks were detected, list them separately as "Flags" (no secrets, no sensitive data).

## Output Format (required)
- **Summary (1-3 sentences)**
- **Files Changed**
- **Flags / Risks (if any)**

## Notes
- This command is intentionally narrower than a full refactor pass. Use it when the primary goal is to remove AI-generated clutter and restore codebase consistency without touching security-sensitive behavior.
