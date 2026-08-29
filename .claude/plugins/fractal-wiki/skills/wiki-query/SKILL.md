---
name: wiki-query
description: "Answer a question over the wiki substrate using a local hybrid search engine (BM25 + optional vector + rerank), citing file:line for every claim, then optionally file the valuable answer back into wiki/synthesis/. The librarian query loop. Use when the user asks to search the wiki, query the wiki, ask the wiki a question, or find something in the knowledge base."
user-invocable: true
---

# wiki-query — the librarian query loop

You answer questions over the **indexed markdown library** using a local hybrid search
engine (BM25 + vector + rerank). Every claim in your answer cites a `file:line`. If the
answer is durable and valuable, you file it back into `wiki/synthesis/` so the library
compounds.

## The search CLI

The tool is vendored under `tools/wiki-index/` (see that directory's `README.md` for setup
and the committed index). Use the wrapper, which resolves the binary and the committed index
from any cwd:

```bash
WRAP="${CLAUDE_PLUGIN_ROOT}/skills/wiki-query/scripts/qmd-search.sh"

bash "$WRAP" search "<exact keywords>"        # BM25 only — fast, no model load (DEFAULT)
bash "$WRAP" query  "<question>" --no-rerank  # semantic, RRF-only — no rerank model
bash "$WRAP" query  "<question>"              # DEEP: full rerank+expand (capable host only)
bash "$WRAP" get    "<result-ref>"            # fetch surrounding lines of a doc
bash "$WRAP" status                           # index + collection health
```

If this repo scopes multiple document collections, pass `-c <collection>`; a repo with a
single `wiki/` tree can omit it.

> **Latency is host placement, not the tool.** A full hybrid `query` (rerank + query
> expansion) loads several local models (an embedder plus a reranker, and often a
> query-expansion model) — resident memory in the low single-digit GB. On a small VM or CI
> box this thrashes swap; BM25 (`search`) needs no model and returns in well under a second
> regardless of box size. The semantic/rerank path is a **local-workstation** tool
> (several GB of free RAM), not something to run by default on a constrained box.
>
> **Default ladder (fastest → heaviest):**
> 1. `search` (BM25) — no model, always fast. **Start here**, and the only path to use on a
>    memory-constrained VM or CI runner.
> 2. `query --no-rerank` — semantic via reciprocal-rank fusion, skips the reranker model.
>    Use on a local machine when keywords aren't enough.
> 3. `query` (full rerank + expansion) — **DEEP mode**, opt-in, capable host only. Don't
>    invoke by default.
>
> Force CPU-only inference where the tool supports it on constrained boxes, and cap rerank
> candidates for speed. If any semantic path is slow or unavailable, fall back to `search`.

## Steps

1. **Pick scope.** If this repo has multiple collections and the user named a domain, pass
   `-c <collection>`. Otherwise query the default collection.

2. **Run the search, cheapest path first.** Start with `search` (BM25) — it answers most
   lookups in under a second with no model load. Escalate to `query --no-rerank` only when
   keyword search misses the meaning, and to full `query` (DEEP) only on a capable local
   host when ranking quality matters. Capture the citation references and scores.

3. **Read the hits.** Use `get` to pull enough surrounding context to answer faithfully. Do
   not answer from snippet alone if the claim is load-bearing.

4. **Answer with citations.** Every factual claim cites `file:line` (translate a result
   reference like `wiki/foo.md:34` accordingly). If the corpus is silent or contradictory,
   say so — do not invent.

5. **File the answer back (optional, when durable).** If the synthesized answer is reusable,
   write it to `wiki/synthesis/<slug>.md` (A+ clean markdown, with the citing links), update
   `wiki/index.md` if a new category appeared, and append a `query` row to `wiki/log.md`:
   `| <date> | query | wiki/synthesis/<slug>.md | <one-line> |`. Then refresh the index
   (`tools/wiki-index/refresh-bm25-index.sh`) so it is searchable. Skip filing for one-off
   lookups.

## Acceptance (self-check)

- [ ] Answer cites real `file:line` references that exist in the corpus.
- [ ] Scope was chosen deliberately (collection or default).
- [ ] If filed: `wiki/synthesis/<slug>.md` exists, log row appended, index refreshed.

## Constraints

- Never fabricate a citation. If the search returns nothing, report the gap.
- Sensitive-data discipline: never echo regulated personal data (e.g. patient identifiers,
  identifying personal findings) into synthesis or logs if this repo handles such data — reference by
  resource type + UUID only.
- Do not write to a change-managed decision log — that tier is reached only via
  `promote-to-ledger`, never filed here directly.
