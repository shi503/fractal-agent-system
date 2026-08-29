# wiki-index — the lex-first search floor for the wiki substrate

The `fractal-wiki` plugin's skills (`wiki-query`, `wiki-explore`, `wiki-ingest`, `wiki-lint`)
search the wiki through a local hybrid search engine (`@tobilu/qmd`), vendored here with a
committed lockfile so the tool is reproducible on any box with no external install step
beyond `bun install`.

**The sanctioned discovery floor is a committed, lexical-only (BM25) index** — no vector or
rerank models, no always-on server. Vector/rerank search is a genuine opt-in extra with its
own memory profile — see below — not something any skill invokes by default.

## What is committed here

- `package.json` + `bun.lock` — the vendored dependency, pinned. Run `bun install &&
  bun pm trust --all` once to materialize `node_modules/` (gitignored — reproducible from
  the lockfile, not committed).
- `taskflow.sqlite` — a BM25 index of `fixtures/taskflow/wiki/` (17 documents), built with
  the vector-embed step never invoked. It contains only full-text (FTS5/BM25) tables and
  document metadata — no vector or rerank data, by construction (the tool only creates
  vector tables when its `embed` command runs, and this pipeline never calls it). **328 KB**,
  well under the 2 MB ceiling.
- `refresh-bm25-index.sh` — rebuilds `taskflow.sqlite` from the live corpus. Deterministic
  and safe to re-run: it builds into an isolated, throwaway config dir and never touches a
  caller's personal search-tool config or cache.
- `qmd-search.sh` — the canonical resolver: finds the vendored binary and the committed
  index relative to its own location, so any caller (a skill, a script, a person) can invoke
  it from any cwd without knowing install paths.
- `query-smoke.sh` — the deterministic gate: runs three canned queries against the committed
  index and checks each returns a hit and that the three top hits are three distinct
  documents.

## How to query it

```bash
tools/wiki-index/qmd-search.sh search "<keywords>"      # BM25 only — fast, no model (DEFAULT)
tools/wiki-index/qmd-search.sh query  "<question>" --no-rerank   # semantic, no rerank model
tools/wiki-index/qmd-search.sh query  "<question>"       # DEEP: full rerank+expand (capable host only)
tools/wiki-index/qmd-search.sh get    "<result-ref>"     # fetch surrounding lines of a doc
tools/wiki-index/qmd-search.sh status                    # index + collection health
```

`INDEX_PATH` defaults to `tools/wiki-index/taskflow.sqlite` (the fixture's committed index);
override it to point at a different index (e.g. a real deployment's `wiki.sqlite`). Every
hit includes a `qmd://<path>:<line>` reference — cite as `<path>:<line>`.

Measured on this box: `search` against the committed index returns well under a second, no
model load.

## Refreshing the index

```bash
tools/wiki-index/refresh-bm25-index.sh
```

Safe to re-run any time the corpus changes. Rebuilds `taskflow.sqlite` from
`fixtures/taskflow/wiki/` (override with `WIKI_SRC=wiki` and `INDEX_DB=wiki.sqlite` for a
real, non-fixture wiki) into an isolated config, checkpoints the SQLite WAL so the committed
file is complete (not a common integration bug: deleting `-wal`/`-shm` side files *before* a
checkpoint silently drops the most recent writes), and reports the resulting size. Review
the diff and commit `taskflow.sqlite` through the normal PR flow — the script does not
commit on your behalf.

## The vector/rerank path — opt-in extra, not the default

A full hybrid `query` (query expansion + embedding + reranking) loads several local models —
an embedder, a reranker, and often a query-expansion model — with resident memory in the low
single-digit gigabytes. On a small VM, CI runner, or a laptop already under memory pressure,
this thrashes swap; a `search` (BM25) call needs no model and returns in well under a second
regardless of box size.

**Default ladder (fastest → heaviest), matching `wiki-query`'s doctrine:**
1. `search` (BM25) — no model, always fast. Start here; the only path to use on a
   memory-constrained box.
2. `query --no-rerank` — semantic via reciprocal-rank fusion, skips the reranker model. Use
   on a local machine when keywords miss the meaning.
3. `query` (full rerank + expansion) — DEEP mode, opt-in, capable local host only
   (several GB free RAM). Never invoked by default by any skill in this plugin.

To build vector data at all, run `node tools/wiki-index/node_modules/.bin/qmd embed` against
a working `QMD_CONFIG_DIR` — this is a separate, explicit step from
`refresh-bm25-index.sh`, which deliberately never calls it. Building and committing a vector
index is out of scope here; the BM25 floor stands on its own.

## Scope

This index covers `fixtures/taskflow/wiki/` only, matching this plugin's fixture corpus. A
repo adopting `fractal-wiki` against its own `wiki/` tree should run
`WIKI_SRC=wiki INDEX_DB=wiki.sqlite tools/wiki-index/refresh-bm25-index.sh` and update
`qmd-search.sh`'s `INDEX_PATH` default (or set `INDEX_PATH` in the environment) accordingly.
