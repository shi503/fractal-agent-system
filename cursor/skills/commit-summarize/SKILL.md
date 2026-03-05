---
name: commit-summarize
description: "Commit work in progress with a concise, scannable summary"
---

User has made incremental progress at a sensible stopping point. Commit the relevant work and provide a concise summary so logs stay clear.

## Goal

1. **Verify** — Read the actual diff; do not trust documentation alone.
2. **Document** — Clear title (80 chars max), bullet details, update CHANGELOG.md if needed (features, fixes, breaking changes).
3. **Commit** — Show the message and commit.

## Steps

1. `git status` and `git diff` — understand what changed and why.
2. Update CHANGELOG.md only for: new features, bug fixes, breaking changes, user-facing updates. Skip for typos, minor refactors, WIP.
3. Commit message format:
   ```
   type: concise description (50 chars max)
   - bullet details (what/why), 72 chars max width
   ```
   Types: `feat`, `fix`, `docs`, `refactor`, `chore`, `test`
4. Ask for approval only if the commit is substantial or the "why" is unclear; otherwise commit.
5. After commit, ask: Amend, Push, or something else?

## Rules

- Fast by default. Verify before committing. One message — ask once with your best attempt for approval if needed.
- Keep it fast; be conversational but brief.
