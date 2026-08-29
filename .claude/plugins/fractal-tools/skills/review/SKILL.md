---
name: review
description: Comprehensive code review checking logging, errors, types, security, performance, and component-framework patterns
disable-model-invocation: true
---

# Code Review Task

Perform comprehensive code review. Be thorough but concise.

## Pre-Review: Deterministic Checks (Run First)

Before any subjective review, run these grep assertions against the diff or changed files. These are binary and never produce false negatives. A single match is a **CRITICAL** finding — stop and report it before continuing to subjective review.

```bash
# Component-framework forbidden patterns — must return 0 matches in new/changed files
grep -n "\*ngIf\|\*ngFor\|\*ngSwitch" <changed-files>
grep -n "standalone:\s*true" <changed-files>
grep -n "@Input()\|@Output()" <changed-files>
grep -n "\[ngClass\]\|\[ngStyle\]" <changed-files>

# Hardcoded colors — must return 0 matches in new/changed files
grep -n "#[0-9a-fA-F]\{3,6\}" <changed-files>
grep -Pn "rgb\(|rgba\(|hsl\(" <changed-files>

# Console logs — must return 0 matches in new/changed files
grep -n "console\.log\|console\.warn\|console\.error" <changed-files>

# Raw fetch() in framework app files — must return 0 matches
grep -rn "fetch(" src/app/services/ src/app/components/ src/app/stores/ 2>/dev/null
```

Report any match as:
**CRITICAL [Pattern]** `file:line` — `<matched text>` — [correct alternative per the project's forbidden-patterns convention]

Only proceed to subjective review after all deterministic checks pass.

## Check For:

**Logging** - No console.log statements, uses proper logger with context
**Error Handling** - Try-catch for async, centralized handlers, helpful messages
**TypeScript** - No `any` types, proper interfaces, no @ts-ignore
**Production Readiness** - No debug statements, no TODOs, no hardcoded secrets
**Framework/Signals** - `effect()` has cleanup via `onCleanup`, signal reactivity correct, `OnPush` on all components, `takeUntilDestroyed` for observables, dependencies complete, no infinite loops
**Performance** - No unnecessary signal reads in templates, expensive derivations use `computed()`, No unnecessary re-renders, expensive calcs memoized
**Security** - Auth checked, inputs validated, RLS policies in place
**Architecture** - Follows existing patterns, code in correct directory

## Output Format

### Looks Good
- [Item 1]
- [Item 2]

### Issues Found
- **[Severity]** [File:line] - [Issue description]
  - Fix: [Suggested fix]

### Summary
- Files reviewed: X
- Critical issues: X
- Warnings: X

## Severity Levels
- **CRITICAL** - Security, data loss, crashes
- **HIGH** - Bugs, performance issues, bad UX
- **MEDIUM** - Code quality, maintainability
- **LOW** - Style, minor improvements
