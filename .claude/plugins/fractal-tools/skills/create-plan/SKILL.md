---
name: create-plan
description: Create a structured markdown implementation plan and file it into the repo's plans convention — never loose root files
disable-model-invocation: true
---

# Plan Creation Stage

Based on our full exchange, produce a markdown plan document and file it in the correct location.

## Filing destinations

Determine the target path before writing:

1. **Project-scoped plan** — if the repo organizes work under a `projects/<project>/` (or
   equivalent) convention, target is `projects/<project>/plan-<slug>.md` (append with YAML
   frontmatter if the file exists, create with frontmatter if new):
   ```yaml
   ---
   title: "<plan title>"
   project: <project>
   created: "<YYYY-MM-DD>"
   status: ACTIVE
   tags: [plan]
   ---
   ```
   Backlog items appended to `projects/<project>/backlog.md`.

2. **Non-project plan** (cross-cutting, research, spike) — if the repo has a `wiki/` substrate,
   file into `wiki/raw/<slug>.md` with the same frontmatter pattern (`tags: [plan, raw]`).
   Otherwise, use whatever docs/plans convention the repo already has established.

3. **Never** write a loose file at the repo root or a random directory. If the correct
   destination is unclear, ask the user one targeted question before writing.

## Plan requirements

- Include clear, minimal, concise steps.
- Track the status of each step using these status markers:
  - DONE
  - IN_PROGRESS
  - TO_DO
- Include dynamic tracking of overall progress percentage (at top).
- Do NOT add extra scope or unnecessary complexity beyond explicitly clarified details.
- Steps should be modular, elegant, minimal, and integrate seamlessly within the existing codebase.

## Markdown template

```markdown
---
title: "<Feature Name> Implementation Plan"
project: <project>
created: "<YYYY-MM-DD>"
status: ACTIVE
tags: [plan]
---

# <Feature Name> Implementation Plan

**Overall Progress:** `0%`

## TLDR
Short summary of what we're building and why.

## Critical Decisions
Key architectural/implementation choices made during exploration:
- Decision 1: [choice] — [brief rationale]
- Decision 2: [choice] — [brief rationale]

## Tasks

- [ ] TO_DO **Step 1: [Name]**
  - [ ] TO_DO Subtask 1
  - [ ] TO_DO Subtask 2

- [ ] TO_DO **Step 2: [Name]**
  - [ ] TO_DO Subtask 1
  - [ ] TO_DO Subtask 2
```

After writing the file, output its absolute path so the user can open it directly.

It's still not time to build. Write the plan document only. No extra complexity or extra scope.
