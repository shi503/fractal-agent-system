paths: ["fixtures/taskflow/wiki/**", ".claude/plugins/fractal-wiki/**", "tools/wiki-index/**"]
---

# Wiki Agent Access — Retrieval Conventions

**Rationale:** give an agent the context it needs without bulk-loading the whole substrate.
Pattern: a small always-on overview plus on-demand retrieval via the committed search index,
not speculative full-file reads.

## The floor: committed BM25 index

The sanctioned discovery mechanism is the **committed lexical (BM25) index** at
`tools/wiki-index/taskflow.sqlite` (328 KB, full-text tables only — no vector or rerank data
by construction), queried through `tools/wiki-index/qmd-search.sh`. This is not a slow-path
fallback — it is the default: no model load, sub-second, works on any box with the vendored
dependency installed. `tools/wiki-index/query-smoke.sh` is the deterministic gate: three
canned queries must each rank a distinct document first.

## Search-before-load rule

**Do NOT** `Read` whole wiki files speculatively. Instead:

```bash
tools/wiki-index/qmd-search.sh search "<exact keywords>"   # BM25 — DEFAULT, no model load
```

`INDEX_PATH` defaults to `tools/wiki-index/taskflow.sqlite` (the fixture's committed index);
a repo running `fractal-wiki` against its own `wiki/` tree overrides it after running
`WIKI_SRC=wiki INDEX_DB=wiki.sqlite tools/wiki-index/refresh-bm25-index.sh` (see
`tools/wiki-index/README.md`).

## Cite `file:line` for every retrieval-derived claim

Every hit carries a `qmd://<path>:<line>` reference. Cite it as `<path>:<line>`. No claim
from retrieval without attribution.

## Query placement + latency doctrine

**Latency is host placement, not the tool.** A full hybrid query (rerank + expansion) loads
several local models (embedder, reranker, often a query-expansion model) — resident memory in
the low single-digit GB. On a small VM or CI runner this thrashes swap; BM25 needs no model
and returns in well under a second regardless of box size.

Default ladder — cheapest path first:

1. **`search` (BM25)** — no model, sub-second. **Start here.** On a memory-constrained box
   this is the only path to use.
2. **`query --no-rerank`** — semantic recall via reciprocal-rank fusion, no reranker model.
   Use on a local machine when keywords miss the meaning.
3. **`query` (full rerank + expansion)** — DEEP mode, opt-in, capable local host only (several
   GB free RAM). No skill in `fractal-wiki` invokes this by default.

If any semantic path is slow or unavailable, fall back to `search`.

## Substrate shape and deeper conventions

`docs/wiki-conventions.md` is the full reference: the four-tier layout (`raw/` → `sources/` →
`synthesis/` → `entities/`), the OKF v0.2 frontmatter contract, the three-way
See-also/Backlinks/Related-semantic link split, and the risk-based review-queue gate that
quarantines a risky LLM edit to an existing page (`wiki-ingest`'s
`scripts/review-queue.sh`). Read it before writing to an existing wiki page, not just before
querying one.

## Summary

- Query `tools/wiki-index/taskflow.sqlite` via `qmd-search.sh` first — no MCP, no model load.
- Search first, read whole files only as a last resort.
- Cite every claim: `file:line`.
- Cheapest path first: BM25 (`search`) → `query --no-rerank` → full `query` (DEEP, capable
  host only).

<!-- referenced-paths
tools/wiki-index/qmd-search.sh
tools/wiki-index/taskflow.sqlite
tools/wiki-index/query-smoke.sh
tools/wiki-index/README.md
docs/wiki-conventions.md
.claude/plugins/fractal-wiki
.claude/plugins/fractal-wiki/skills/wiki-ingest/scripts/review-queue.sh
-->
