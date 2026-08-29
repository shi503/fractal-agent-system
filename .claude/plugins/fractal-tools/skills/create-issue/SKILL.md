---
name: create-issue
description: Capture a bug, feature, or improvement — files it via gh to GitHub Issues, or drafts to _INBOX/ when offline
argument-hint: "[description of issue]"
disable-model-invocation: true
---

# Create Issue

User is mid-development and thought of a bug, feature, or improvement. Capture it fast so
they can keep working. Default target: GitHub Issues on the current repo, via `gh`.

## Your Goal

Gather enough information to create a clear, plain-language GitHub issue:
- Clear, jargon-free title (no internal shorthand codes the reader wouldn't recognize)
- TL;DR of what the issue is
- Current state vs expected/desired outcome
- Relevant files if applicable
- Type (bug / feature / improvement) and priority (normal unless stated otherwise)

## How to Get There

**Ask one targeted batch** — be concise, respect the user's mid-flow state. Usually need:
- What's the issue/feature
- Current behavior vs desired behavior
- Type and priority if not obvious from context

Keep questions brief. One message with 2-3 targeted questions beats multiple back-and-forths.

**Skip what's obvious** — if type/priority is clear, don't ask.

**Keep it fast** — total exchange under 2 minutes.

## Filing: gh-first

When ready to file, run `gh` to create the issue on the current repo:

```bash
gh issue create \
  --title "<plain-language title>" \
  --body "<TL;DR + current vs desired + relevant files>" \
  --label "<bug|enhancement>"
```

Plain-language rules for the title and description:
- Write as if explaining to a new teammate, not a bot
- Avoid internal shorthand or codes that only make sense with tribal context
- Include the "why" in one sentence if non-obvious

## Offline fallback: _INBOX/

When `gh` is unavailable (no network, auth failure, not a GitHub remote, etc.), file the draft
locally:

```
_INBOX/<YYYY-MM-DD>-<slug>.md
```

Frontmatter:
```yaml
---
title: "<issue title>"
type: bug | feature | improvement
priority: normal | high | low
status: DRAFT
created: "<YYYY-MM-DD>"
routing: GitHub Issues — file when gh available
---
```

Tell the user where the draft landed and remind them to route it when online.
Do not silently swallow failures — if `gh` errors, always fall back to `_INBOX/` and
report the error message.

## Behavior Rules

- Be conversational — ask what makes sense, not a checklist
- Default priority: normal, effort: medium (ask only if unclear)
- Max 3 files in context — most relevant only
- Bullet points over paragraphs
- Never include end-user personal data (names, emails, identifiers) in the ticket body
