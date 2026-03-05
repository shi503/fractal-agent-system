---
name: commit-summarize
description: Commit work in progress with a concise, scannable summary
disable-model-invocation: true
---

User has made incremental progress and is at a sensible stopping point. Commit all the relevant work that's been done and provide a concise and fast summary so they can keep working and our logs are easy to understand. 

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

**Ask for message approval** if:
- Commit is substantial (multi-file, complex changes)
- You're unsure about the "why" behind changes

**Just do it** if:
- Message is obvious from the diff
- User already indicated what they were doing

**4. Commit**
```bash
git add -A
git commit -m "your message"
```

**5. Ask & Follow-up**
- After you made the commit, prompt a follow-up to ask what to do next: 
- 1. Amend: ask if they want to make any changes to the commit
- 2. Push: begin push changes
- 3. Something else: ask if they want to do something else. 

## Behavior Rules

- **Fast by default** - Most commits don't need discussion
- **CHANGELOG only when it matters** - Don't document every semicolon
- **Verify before committing** - Read the actual diff, don't guess
- **One message** - If you need to ask about the commit message, ask once with your best attempt for them to approve/edit

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