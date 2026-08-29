# Meeting-summary rubric (feature/architecture sessions)

Score each dimension 0–3 (0 absent · 1 minimal · 2 solid · 3 excellent).

| # | Dimension | What "3" looks like |
|---|-----------|---------------------|
| D1 | **Capture fidelity** | Every decision, action, open question, and attendee recorded accurately. |
| D2 | **Disambiguation** | Systematic mistranscription/codename table (applied from the shared glossary) plus a roster check for referenced-not-present names. |
| D3 | **Grounding** ⭐ | Each meeting assumption checked against deployed code/stack; contradictions and already-handled primitives flagged with **citations** (synthesis §, file, function). |
| D4 | **Decision register** | ✅ Decided / 🟡 Deferred / ❓ Open split, each row attributed. |
| D5 | **Traceability** | Mapped to real tracker tickets, ADR candidates, and per-owner actions; downstream-ready. |
| D6 | **Architecture clarity** | A diagram or model that orients the reader before the detail starts. |
| D7 | **Risk/migration flags** | Surfaces tensions with the current posture (⚠️ "this reverses X"). |
| D8 | **Navigability** | Structure, cross-links, sources block, findable by the repo's search index. |
| D9 | **Safety** | Scrubbed of secrets, credentials, and personal data; safe to share. |

## The bar for a grounded summary

- **Total ≥ 24/27.**
- **D3 (grounding) ≥ 2**, with a **non-empty set of 🔎 callouts, every one cited** (synthesis §,
  `file:line`, or function). D3 is the differentiator — it drives D5, D6, and D7 as well.
- D9 = 3 always. The safety scrub is non-negotiable.

## Reference scores

| | Automatic wiki-ingest (librarian tier) | Manual grounded (gold standard) |
|---|:---:|:---:|
| Total | **13 / 27** | **27 / 27** |
| D3 Grounding | 0 | 3 |

The two are **different tiers, not better and worse versions of the same thing.** The librarian
capture propagates unverified room assumptions; the grounded artifact cross-references deployed
reality so readers act on it instead of re-deriving primitives. This skill produces the grounded
tier.
