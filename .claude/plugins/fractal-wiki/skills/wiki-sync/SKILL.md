---
name: wiki-sync
description: "Bi-directional sync of a file between a user's local space (often a sibling repo) and the wiki substrate. Push-primary: a dev points it at a locally generated/edited .md and it lands in the right wiki home with provenance. Always uses AskUserQuestion to confirm direction + reconciliation strategy before writing, and fires follow-up actions (re-index, re-synthesis, mark-dirty) after. Use when the user asks to sync this up to the wiki, sync this guide with the wiki, push a local doc into the wiki, or update the wiki with the latest version."
user-invocable: true
---

# wiki-sync — bidirectional sync

You sync a file between a user's local/sibling-repo space and the canonical wiki substrate.
**Canonical lands in the wiki** (git-tracked, provenance-stamped). The common case is a dev
in a sibling repo who generated or hand-edited a doc (a guide, a meeting summary, a plan) and
wants it reflected in the wiki — or pulled back to latest.

## ALWAYS clarify first (AskUserQuestion — do not guess)

Before any write, ask:
1. **Direction** — Push (local → wiki, default/primary) · Pull (wiki → local) · Reconcile
   (two-way, files diverged).
2. **Reconciliation strategy** (when both sides exist + differ) — Overwrite destination ·
   Merge (you reconcile, show diff) · Latest-wins (mtime/explicit) · Keep-both (suffix).
3. **Destination tier** (push) — `wiki/sources/` (knowledge/guide), `wiki/raw/` (raw
   capture), or a project-specific meetings/summaries home if this repo has one. If the
   content is a **decision**, STOP and route to `promote-to-ledger` (never sync into the
   decision log directly).

Use `wiki-explore` first if you don't know whether a wiki counterpart already exists.

## Sync

1. Locate both sides (local path; wiki counterpart via `wiki-explore` / the BM25 search).
   Show a short diff if both exist.
2. Apply the chosen direction + strategy. Normalize filename + stamp/update provenance
   frontmatter (`source:` = the sibling-repo path + commit if available, `synced_by:`,
   `synced:` date, `status:`). Read-only on the sibling repo unless the user explicitly
   chose Pull.
3. **Confirm the write back to the user** (what landed where).

## Follow-up actions (the "and then" — always run after a successful sync)

A sync rarely ends at the copy. Determine and execute/queue:
- **Re-index:** if the file landed in the indexed `wiki/` tree, rebuild or refresh the BM25
  index (`tools/wiki-index/refresh-bm25-index.sh`) so it is searchable.
- **Re-synthesis:** if the synced content changes a topic that has a `wiki/synthesis/` page,
  flag that page as needing a re-run (don't silently let synthesis drift).
- **Downstream planning:** if it touches a decision or a plan, flag the affected doc(s) to
  update — or route to `promote-to-ledger`.
- **Mark dirty:** if you can't complete a follow-up now (e.g. a full reindex is slow), stamp
  `status: DIRTY` / append to a dirty-list so a later sweep or cron picks it up. Never leave
  a sync half-reconciled silently.

## Hard rules

- Decisions → `promote-to-ledger`, never a direct decision-log write (locked, change-managed
  tier).
- Push-primary; pulls and reconciles require explicit user choice.
- Sibling repos: read-only unless Pull was chosen; never `git checkout`/write a sibling
  working tree without explicit instruction.

Cross-refs: `wiki-explore` (find the counterpart), `wiki-add` (one-shot capture, no
reconciliation), `wiki-ingest` (process raw → source), `promote-to-ledger` (decisions).
