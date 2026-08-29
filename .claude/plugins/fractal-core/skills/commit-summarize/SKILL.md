---
name: commit-summarize
description: "Commit work in progress with a concise, scannable summary, gated by a review step before the commit lands. Use when the user asks to commit changes, wrap up a work session, or summarize a diff into a commit."
disable-model-invocation: true
---

User has made incremental progress and is at a sensible stopping point. Commit all the relevant work that's been done and provide a concise and fast summary so they can keep working and the log stays easy to understand.

> **Review policy:** Every commit passes a **review gate** before `git commit` runs. No exceptions — not for "obvious" diffs, not for "fast" commits. Show the summary and ask for approval via `AskUserQuestion` every time. Rationale: preserves provenance and keeps an auditable record of intent for AI-assisted commits.

## Your Goal

### 1. Verify Current Implementation
**CRITICAL**: DO NOT trust existing documentation. Read the actual code.
- Review what's actually changing (verify with diff and look at actual code, not assumptions)

### 2. Document and create a solid commit with:
- Clear title, concise Description (80 chars max)
- Update CHANGELOG.md if needed
- TL;DR of what was done, include headline stats (eg. # files changed/added, minor vs major change, etc..)
- Proper references to features, PRDs, or fixes
- Bullet point details, keep it scannable
- Show your message at the end and commit.

## How to Get There

**1. Review the changes**
```bash
git status
git diff
```
- Understand what files changed and why
- If it's obvious (typo fix, small tweak), move fast
- If it's substantial, verify the actual changes match user's intent

**2. Update CHANGELOG.md** (if needed)
- Skip for: typos, minor refactors, internal tweaks, WIP commits
- Update for: new features, bug fixes, breaking changes, user-facing updates
- Capture decision-making: new documentation, pivots, decisions-made, planning
- Add under "Unreleased" with proper category (Added/Changed/Fixed/Removed)

**3. Generate commit message**

Format:
```
type: concise description (50 chars max)

- bullet point details if needed (what/why)
- keep it scannable
- 72 chars max width
```

Types: `feat`, `fix`, `docs`, `refactor`, `chore`, `test`

**4. Review gate — always ask before committing**

Every commit goes through this step, regardless of size, obviousness, or whether the user stated intent upfront.

Present the user with:
1. The list of files to be staged (from `git status`), grouped by change type if helpful (modified / added / deleted / renamed).
2. The proposed commit message in full (title + body).
3. A one-line note on scope (e.g., "3 files, ~40 lines, docs-only" or "1 migration + 2 model edits, schema change").
4. If the CHANGELOG is being updated, show the proposed new entry.

Then invoke `AskUserQuestion` asking the user to review the files and summary before committing.

Options:

| Label | Description |
|---|---|
| **Approve and commit** | Proceed with the staged files and proposed message as shown. |
| **Edit the message** | User provides a corrected title / body in the free-text response. Re-show and re-ask. |
| **Unstage some files** | User lists paths to remove from this commit. Re-stage, re-show, re-ask. |
| **Cancel** | Do not commit. Leave working tree as-is. |

Do NOT proceed to `git commit` on anything other than explicit **Approve and commit**. If the user selects **Edit the message** or **Unstage some files** (or writes any free-text correction via the "Other" option):

1. Apply the requested change.
2. **Re-display the updated state before asking again** — show the new file list and the **full new proposed commit message in a fenced code block**. Do not ask the user to trust that the change was applied; prove it by re-showing.
3. Re-invoke the review gate. The approval must cover the exact final state.

Exception: if the user's correction message explicitly includes "commit now" / "you're good to commit" / equivalent, treat that as approval of the new state and skip the second `AskUserQuestion` — but still re-display the final message + file list in the turn that runs the commit, so the approval and the committed state are both on record in the transcript.

**5. Commit (only after explicit approval)**
```bash
git add <specific files from approval>
git commit -m "approved message"
```
Prefer staging specific files over `git add -A` so the approval reflects the exact scope.

**6. Ask & Follow-up**
- After the commit lands, prompt a follow-up to ask what to do next:
- 1. Amend: ask if they want to make any changes to the commit
- 2. Push: begin push changes
- 3. Something else: ask if they want to do something else.

## Behavior Rules

- **Review gate first, fast second** — every commit passes the Step 4 review gate. "Fast" means generate the message and summary quickly, not skip the approval.
- **CHANGELOG only when it matters** — don't document every semicolon.
- **Verify before committing** — read the actual diff, don't guess. Present what you verified as part of the Step 4 review.
- **Approval covers exact state** — if the user edits the message or unstages files, re-run the review gate on the new state. Prior approval does not carry over changes.
- **Never `git add -A` blind** — stage the files the user approved, not everything in the working tree. Avoid sweeping in unrelated untracked items.

## Model Efficiency

💡 **Consider using cheaper model** (Sonnet/Haiku) for:
- Reading `git diff` output
- Generating commit message
- Updating CHANGELOG

⚠️ **Stick with current model** if:
- Changes are complex/ambiguous
- User wants discussion about what to commit
- Multiple files with unclear relationships

**Ask questions** to fill gaps - be concise, respect the user's time. They're mid-flow and want to capture this quickly. Usually need:
- What's the issue/feature
- Current behavior vs desired behavior
- Type (bug/feature/improvement) and priority if not obvious

Keep questions brief. One message with 2-3 targeted questions beats multiple back-and-forths.

**Search for context** only when helpful:
- Web search for best practices if it's a complex feature
- Grep codebase to find relevant files
- Note any risks or dependencies you spot

**Skip what's obvious** - If it's a straightforward bug, don't search web. If type/priority is clear from description, don't ask.

**Keep it fast** - Total exchange under 2min. Be conversational but brief. Get what you need, create ticket, done.

## Behavior Rules

- Be conversational - ask what makes sense, not a checklist
- Default priority: normal, effort: medium (ask only if unclear)
- Bullet points over paragraphs

## Gotchas

- The review gate is mandatory even for one-line changes — do not special-case "obvious" diffs out of it.
- `git add -A` is explicitly disallowed as a default — always stage the specific approved files to keep the commit scope matching what the user reviewed.
