---
name: wiki-explore
description: "Discovery pass over the wiki substrate — given a topic, file, or pasted output, find the documents/decisions it relates to (BM25-first search, search-before-load, cite file:line) and return a ranked relevance map. The parsing/triage step that precedes wiki-add / wiki-sync / promote-to-ledger / a decision fold. Use when the user asks what the wiki has on a topic, to find related docs, where something would fit in the wiki, or to wiki-explore before adding or syncing."
user-invocable: true
---

# wiki-explore — the discovery / triage loop

You are the **librarian doing reconnaissance**. Before anything is added, synced, revised, or
folded, you locate what already exists and where the new material belongs. This is the
**read-only** front half of the capture loop — you find and map; `wiki-add` / `wiki-sync` /
`promote-to-ledger` act.

## Input

A topic string, a file path, or pasted output. If given a file/paste, first extract its key
entities (decision IDs, doc names, people, systems) — those become your sub-queries.

## Loop

1. **Search-before-load.** Run the committed BM25 index first — no model load, sub-second
   (see `tools/wiki-index/README.md`):
   ```bash
   WRAP="${CLAUDE_PLUGIN_ROOT}/skills/wiki-query/scripts/qmd-search.sh"
   bash "$WRAP" search "<topic keywords>"
   ```
   Escalate to a vector/rerank pass only on a capable local host and only when BM25 misses
   the meaning (see `wiki-query` for the full ladder). Do NOT read whole files
   speculatively.
2. **Map, don't dump.** For each hit, record `path:line`, a one-line "what it is", and the
   relationship (duplicate / supersedes / superseded-by / related / canonical home).
3. **Classify the target.** Decide where the input material belongs: `wiki/raw/` (new raw),
   `wiki/sources/` (summary), the decision log (a decision → route to `promote-to-ledger`,
   never a raw file write), or "already covered" (point at the existing canonical entry).
4. **Surface follow-ups.** Flag anything the input would make stale: a synthesis page
   needing re-run, a downstream plan to update, a decision whose status would change.

## Output (return, don't file)

```
## Relevance map: <topic>
- CANONICAL: <path:line> — <what> — <relationship>
- RELATED:   <path:line> — <what>
- DUPLICATE/STALE: <path:line> — <what> — <action>
## Recommended action: <wiki-add | wiki-sync | promote-to-ledger | revise <path> | already-covered>
## Follow-ups if acted on: <re-synthesis page(s) | downstream plan(s) | mark-dirty targets>
```

Cite `file:line` for every claim. This is the **wiki (librarian) tier** — read-only here;
never write to the decision log (that is the change-managed tier — hand decisions to
`promote-to-ledger`).
