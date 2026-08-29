# Contamination scan (hashed, target-side)

This is the public half of a two-scanner contamination gate.
The private half — a cleartext denylist and scanner — lives in a separate,
non-public planning repo and never ships here. That repo carries the actual
company/people/infra terms this gate exists to catch; a public repo cannot
carry that denylist in cleartext without itself becoming the leak.

`hashes.json` is the bridge: each denylisted term is broken into lowercase
tokens (and adjacent 2-token joins), and each token is SHA-256'd. The hash
set is one-way — nobody reading this directory can recover the original
company name, product name, or person's name it was derived from — but a
future contributor's accidental paste of that same term will still hash to
a value already in the set, and get caught.

`hashes.json` is **generated, not authored**. Do not hand-edit it. It is
regenerated from the private denylist by the planning repo's
`scripts/regen-oss-hashes.sh` and copied in here verbatim (including its
`generated:` date — that date is the day the source denylist was last
translated into this file, not the day this directory was last touched).

## Usage

```bash
python3 tools/repo-hygiene/contamination_scan.py <path> [--changed-only]
```

`<path>` may be this repo's root, any subdirectory of it, or an arbitrary
directory outside it (falls back to a plain file walk if it isn't a git
repo). `--changed-only` scans only files that differ from `main` (or
`origin/main`) on the current branch, and requires `<path>` to be inside a
git repo.

Exit code `0` = clean. Non-zero = at least one hit, printed as
`file:line:<first-8-hex-of-sha256>` (line `0` means the *path itself*
matched, not its content). A hit's 8-hex prefix is enough to confirm a
report references the same underlying term across two runs; it is not
reversible back to the term.

## Allowlisting a line

Add a trailing comment to the offending line: `# oss-scan-allow: <token>`
(or `# oss-scan-allow: *` to allow every hit on that line). The scan still
reports it — as `ALLOWLISTED: file:line:hash` — it just doesn't fail the
build. Allowlist use is never silent.

This scanner does **not** read a path-scoped allowlist file the way the
private cleartext scanner does (a policy file kept in the private planning
repo, not published here). That mechanism depends on comparing a file
against the private repo's `main` branch and is private-repo-side policy,
not something a standalone public CI tool should need to run clean. Only the
inline marker above is honoured here.

## Why the hashed and cleartext scanners can disagree on individual hits

They're intentionally not identical detectors — only their **pass/fail
verdict** on the planted-contamination-fixture and clean-tree tests is
required to agree (WS-02 acceptance criterion). Two known, documented
asymmetries:

- The cleartext denylist has a handful of raw-regex entries (e.g. a ticket-ID
  pattern like `PROJ-<digits>`). A regex isn't a literal string, so it can't
  be tokenized and hashed — this scanner simply doesn't enforce those
  specific entries. `hashes.json`'s `skipped_regex_term_count` field says how
  many there are (their text is not reproduced here — see the "why" below).
- This scanner lowercases every token before hashing (per the algorithm this
  gate is specified against); the cleartext scanner can additionally use
  case-sensitive matching for a few short, collision-prone tokens (2-letter
  initials that are also common lowercase English words). Those
  case-sensitive-only cleartext terms have no hashed counterpart here.

Tokens and 2-token joins shorter than 3 characters are never hashed or
looked up on either side of the generation/scan boundary — below that
length a hash carries essentially no discriminating signal and produces
constant false positives (this repo's own calibration testing found exactly
that: see the source denylist's inline notes for the concrete collisions
this threshold was built to avoid).

## Scope note (WS-02)

This scanner and `hashes.json` are built and verified as part of the OSS
port's WS-02 workstream. Wiring it into this repo's CI as a required check
is a recommendation for a follow-up workstream (WS-19 HANDOFF), not done
here. Branch-history scanning (a term introduced then removed still lives in
`git log -p`) is also out of scope for this scanner — see WS-19.
