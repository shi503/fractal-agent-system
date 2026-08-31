#!/usr/bin/env bash
# docs-freshness-check.sh — staleness/orphan detector for the docs/ corpus.
#
# Retains the two-signal method that found the docs/ corpus's six orphaned
# files by hand during a one-off gap analysis: age alone is not staleness (a
# stable doc that needed no edits is fine), and zero inbound links alone is
# not orphanhood (an intentional entry point has no inbound links either).
# It is the CONJUNCTION — old *and* unreferenced — that flags a doc worth a
# human look. A script that flags every old file gets ignored within a week,
# so this one only trips on the conjunction, not on either signal alone.
#
# For each tracked file under docs/, reports:
#   - last-commit date (git log -1, so a file touched only via a rename or a
#     later unrelated commit still reads correctly)
#   - inbound link count (how many other tracked *.md files anywhere in the
#     repo contain the file's basename as a literal substring — the same
#     cheap, no-parser heuristic the original ad-hoc analysis used; it does
#     not resolve relative paths or markdown link syntax, and it can
#     over-count when two files share a common basename like README.md —
#     documented, accepted limitation, not a bug)
#   - verdict: ORPHAN (old AND zero inbound — actionable), STALE (old but
#     still referenced — informational only, does not fail the gate), or OK
#     (not old, regardless of inbound count)
#
# Usage:
#   bash tools/docs-freshness-check.sh [--rev <tree-ish>] [<repo-root>]
#
#   With no --rev, scans the current working tree (git ls-files + git grep
#   over tracked files) — this is the normal, CI-facing mode.
#
#   --rev <tree-ish> reconstructs the report against a historical tree using
#   only git plumbing (git ls-tree / git log <rev> / git grep <rev>) — it
#   never runs git checkout, git reset, or anything else that moves HEAD or
#   touches the working tree. Use this to regression-test the detector
#   against a tree from before a known triage landed.
#
# Exit code: 0 if zero ORPHAN verdicts. Non-zero (the ORPHAN count) if any
# file is flagged ORPHAN — STALE verdicts alone do not fail the gate.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# ---- Named thresholds ----
#
# STALE_DAYS_THRESHOLD: minimum days since last commit before a doc is even
# considered for the "old" side of the conjunction. This repo's docs/ corpus
# has three sharply separated age bands as of this script's authoring
# (2026-08-30): ~2 days (actively touched this week), ~136 days (an April
# cohort that is still linked-to and clearly live), and ~167 days (the
# untouched-since-initial-scaffold cohort that contains all six known
# orphans). 150 sits in the gap between the 136-day live cohort and the
# 167-day stale cohort: old enough that the April cohort never trips it on
# age alone, young enough that the March cohort always does. It is a
# relative "days since HEAD's last commit", recomputed against wall-clock
# "today" on every run, not an absolute date — it does not need retuning
# just because time passes.
STALE_DAYS_THRESHOLD=150

# INBOUND_ORPHAN_MAX: the inbound-link count at or below which a doc counts
# as "unreferenced" for the orphan verdict. Set to exactly 0, not a fuzzy
# cutoff like 1, because a nonzero count already means some other tracked
# doc found this file worth naming — that is real signal to exclude, not
# noise to threshold away. Verified against this repo's own history:
# `docs/The FRACTAL Evaluation Framework.md` has exactly 1 inbound link and
# was correctly kept (not archived) during the 2026-08-30 triage; a laxer
# threshold (e.g. <=1) would have wrongly swept it in with the true orphans.
INBOUND_ORPHAN_MAX=0

REV=""
ROOT_ARG=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --rev)
      REV="${2:?--rev requires a tree-ish argument}"
      shift 2
      ;;
    -h|--help)
      sed -n '2,33p' "$0"
      exit 0
      ;;
    *)
      if [[ -n "$ROOT_ARG" ]]; then
        echo "error: unexpected extra argument: $1" >&2
        exit 2
      fi
      ROOT_ARG="$1"
      shift
      ;;
  esac
done
ROOT="${ROOT_ARG:-$DEFAULT_ROOT}"

if ! git -C "$ROOT" rev-parse --show-toplevel >/dev/null 2>&1; then
  echo "error: not a git repo: $ROOT" >&2
  exit 2
fi
ROOT="$(git -C "$ROOT" rev-parse --show-toplevel)"

if [[ -n "$REV" ]] && ! git -C "$ROOT" rev-parse --verify --quiet "${REV}^{commit}" >/dev/null; then
  echo "error: --rev '$REV' does not resolve to a commit in $ROOT" >&2
  exit 2
fi

python3 - "$ROOT" "$STALE_DAYS_THRESHOLD" "$INBOUND_ORPHAN_MAX" "$REV" <<'PYEOF'
import datetime
import subprocess
import sys
from pathlib import PurePosixPath

root, stale_days, inbound_max, rev = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]


def git(*args):
    return subprocess.run(
        ["git", "-C", root, *args], capture_output=True, text=True, check=True
    ).stdout


if rev:
    candidates = [
        line for line in git("ls-tree", "-r", "--name-only", rev, "--", "docs").splitlines() if line
    ]
else:
    candidates = [line for line in git("ls-files", "docs/*").splitlines() if line]

today = datetime.date.today()
rows = []

for path in sorted(candidates):
    if rev:
        date_str = git("log", "-1", "--format=%ad", "--date=short", rev, "--", path).strip()
    else:
        date_str = git("log", "-1", "--format=%ad", "--date=short", "--", path).strip()
    if not date_str:
        # No commit touches this path at this rev — should not happen for a
        # path git ls-tree/ls-files just reported as tracked; skip defensively.
        continue
    commit_date = datetime.date.fromisoformat(date_str)
    age_days = (today - commit_date).days

    base = PurePosixPath(path).name
    grep_args = ["grep", "-l", "--fixed-strings", base]
    if rev:
        grep_args.append(rev)
    grep_args += ["--", "*.md"]
    proc = subprocess.run(["git", "-C", root, *grep_args], capture_output=True, text=True)
    hits = [line for line in proc.stdout.splitlines() if line]

    prefix = f"{rev}:" if rev else ""
    inbound = 0
    for hit in hits:
        hit_path = hit[len(prefix):] if prefix and hit.startswith(prefix) else hit
        if hit_path != path:
            inbound += 1

    is_old = age_days >= stale_days
    is_unreferenced = inbound <= inbound_max
    if is_old and is_unreferenced:
        verdict = "ORPHAN"
    elif is_old:
        verdict = "STALE"
    else:
        verdict = "OK"
    rows.append((date_str, age_days, inbound, verdict, path))

label = f"tree {rev}" if rev else "working tree"
print(f"docs/ freshness report — {label}")
header = f"{'DATE':<12}{'AGE_D':>7}  {'INBOUND':>7}  {'VERDICT':<8}  PATH"
print(header)
print("-" * len(header))
for date_str, age_days, inbound, verdict, path in rows:
    print(f"{date_str:<12}{age_days:>7}  {inbound:>7}  {verdict:<8}  {path}")

orphan_paths = [path for *_, verdict, path in rows for verdict in [verdict] if verdict == "ORPHAN"]
stale_count = sum(1 for *_, verdict, _ in rows if verdict == "STALE")
ok_count = sum(1 for *_, verdict, _ in rows if verdict == "OK")

print()
print(
    f"{len(rows)} tracked doc(s) scanned; {len(orphan_paths)} ORPHAN, "
    f"{stale_count} STALE, {ok_count} OK."
)
if orphan_paths:
    print("ORPHAN (stale AND unreferenced — needs a disposition):")
    for path in orphan_paths:
        print(f"  - {path}")

sys.exit(len(orphan_paths))
PYEOF
