paths: ["**/*.md"]
---

# Markdown Authoring — no hard-wrapped prose

**Rationale:** agent-authored markdown routinely gets copy-pasted into chat tools, wikis, and
issue trackers outside this repo. A hard newline inserted mid-paragraph is a literal
character — it survives the paste and renders as a broken mid-sentence line break, forcing a
human to manually re-join lines. `.prettierrc` at the repo root sets no `proseWrap` (default
`preserve`, which does not reflow existing text), so wrapping markdown prose is purely an
authoring choice here, not something a formatter fixes for you. The choice: **don't
hard-wrap.**

## Rules

1. **Prose = one logical line per paragraph.** Do NOT insert newlines to keep paragraphs
   under ~80–100 columns. Let the line run long; the reader's editor soft-wraps it. A
   paragraph is one unbroken line of source text.
2. **A blank line still separates paragraphs.** "No hard-wrap" means no newline *within* a
   paragraph — paragraph breaks (one blank line) are unchanged.
3. **These constructs keep their normal line structure** (they are not prose): tables, fenced
   code blocks, list items (one line per item), headings, link-reference definitions,
   frontmatter.
4. **Bullets:** each bullet is its own line. Do not wrap a single bullet's text across
   multiple source lines — let the bullet run long.
5. **No trailing whitespace** (a stray double-space at line end is a markdown hard break —
   the exact artifact this rule avoids).

## Why not just soft-wrap in the editor?

Soft-wrap is a *display* setting; it does not change the bytes on disk. The problem is the
bytes — the literal `\n` mid-sentence. Only authoring long lines fixes what gets pasted
downstream.

## Scope note

This governs `.md` **prose** in this repo. It says nothing about code formatting in
`app/`, `components/`, or `lib/` — those follow `.prettierrc` and `eslint.config.mjs`.

<!-- referenced-paths
.prettierrc
-->
