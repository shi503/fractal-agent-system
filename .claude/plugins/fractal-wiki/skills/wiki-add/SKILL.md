---
name: wiki-add
description: "Low-friction mechanical capture — copy a file, paste, or command output into wiki/raw/ (or a staging _INBOX/ if the repo uses one) with provenance, no interpretation. The fastest way to get material INTO the wiki substrate; wiki-ingest/transcript-ingest process it from there. Push-only, never touches the decision log. Use when the user asks to wiki-add, drop this into the wiki, capture this to the inbox, add this to the wiki raw, or stash this for later ingest."
user-invocable: true
---

# wiki-add — mechanical capture into the wiki substrate

You are the **capture clerk**. Someone has material (a local file, a paste, command output)
they want INTO the wiki with zero friction. You copy it in, stamp where it came from, and
stop. **No summarizing, no interpreting, no decisions** — that is `wiki-ingest`'s job (which
runs next, separately).

## What it does (mechanical, deterministic)

1. **Resolve the source.** A path (copy the file), pasted text (write it verbatim), or
   stdout (capture it).
2. **Destination = `wiki/raw/`** at the repo root by default — or a staging `_INBOX/` at
   repo root if this repo uses one for routing before wiki placement. Normalize the
   filename to `{YYYY-MM-DD}-{INITIALS}-{slug}.{ext}` (initials from `git config
   user.name`; date passed in or from the source, since the runtime clock is unavailable
   to scripts).
3. **Stamp provenance** as OKF frontmatter: `source:` (original path / "paste" / the
   command), `added_by:`, `added:` (date), `status: UNPROCESSED`.
4. **Append a one-line manifest row** to `_INBOX/README.md` (or `wiki/raw/README.md`) if
   using a staging zone, or rely on `wiki/log.md` if dropping straight into `wiki/raw/`.
5. **Tell the user the next step:** "Run `/wiki-ingest` to process this into
   `wiki/sources/`, or `/promote-to-ledger` if it's a decision."

## Hard rules

- **Never write to the decision log** (see `promote-to-ledger`'s configurable `DL_ROOT`) —
  decisions go through `promote-to-ledger`, a change-managed, locked tier. `wiki-add` is
  capture only.
- **Idempotent:** re-adding the same source updates the existing copy + `updated:` stamp,
  does not duplicate.
- **No re-index here.** Indexing happens at `wiki-ingest` (see `tools/wiki-index/`). If the
  user wants it searchable now, point them at `wiki-ingest`.
- **Mark dirty:** set `status: UNPROCESSED` so a later sweep or `wiki-ingest` knows it is
  pending. This is the "mark content dirty / needs sync" hook.

Cross-refs: `wiki-explore` (find where it belongs first), `wiki-ingest` (process it),
`wiki-sync` (bi-directional sync instead of one-shot capture).
