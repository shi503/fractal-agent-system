#!/usr/bin/env bash
# check-doc-paths.sh — deterministic gate for repo-relative paths cited in the
# top-level onboarding docs.
#
# Scans README.md, SETUP-CLAUDE-CODE.md, the root CLAUDE.md and AGENTS.md, and
# .claude/CLAUDE.md for single-backtick
# inline code spans that look like a repo-relative path (contain a `/`, or are a
# bare filename with a recognized extension) and verifies each one resolves
# against the repo root. Content inside triple-backtick fenced blocks is not
# scanned — those carry shell commands, YAML/JSON snippets, and placeholder
# strings that are not meant to be literal existing paths.
#
# A span is treated as a path claim only if it contains a `/` (a bare filename
# with no directory component is too ambiguous in prose — e.g. a generic
# mention of `router.py` or `CLAUDE.md` — to gate on). A slash-containing span
# is then skipped (not checked) if it:
#   - is a URL (http:// or https://)
#   - contains a placeholder marker: { } < > $ * ? ! ( ) ' "
#   - contains whitespace
#
# A glob-shaped span (contains `*`) is reduced to its longest literal directory
# prefix before the wildcard, and that directory must exist.
#
# Usage: bash tools/check-doc-paths.sh
# Exit code: 0 = every path resolves. 1 = at least one dangling path (printed).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

python3 - "$REPO_ROOT" <<'PYEOF'
import re
import sys
from pathlib import Path

repo_root = Path(sys.argv[1])

DOCS = [
    "README.md",
    "SETUP-CLAUDE-CODE.md",
    "CLAUDE.md",
    "AGENTS.md",
    ".claude/CLAUDE.md",
]

FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
SPAN_RE = re.compile(r"`([^`\n]+)`")
PLACEHOLDER_CHARS = set("{}<>$*?!()'\"")

failures = []
checked = 0

for doc in DOCS:
    path = repo_root / doc
    if not path.is_file():
        failures.append(f"{doc}: doc file itself is missing")
        continue
    text = path.read_text(encoding="utf-8")
    text_no_fences = FENCE_RE.sub("", text)
    for span in SPAN_RE.findall(text_no_fences):
        token = span.strip()
        if not token:
            continue
        if "/" not in token:
            continue
        if token.startswith("http://") or token.startswith("https://"):
            continue
        if any(ch in token for ch in PLACEHOLDER_CHARS):
            continue
        if any(ch.isspace() for ch in token):
            continue

        candidate = token[2:] if token.startswith("./") else token
        candidate = candidate.rstrip("/")
        if not candidate:
            continue

        checked += 1

        if "*" in candidate:
            prefix = candidate.split("*", 1)[0]
            if "/" in prefix:
                prefix = prefix.rsplit("/", 1)[0]
            else:
                prefix = ""
            if not prefix:
                continue
            target = repo_root / prefix
            if not target.is_dir():
                failures.append(f"{doc}: `{token}` — glob prefix `{prefix}` is not a directory")
            continue

        target = repo_root / candidate
        if not target.exists():
            failures.append(f"{doc}: `{token}` — does not resolve to a file or directory")

if failures:
    print(f"check-doc-paths: {len(failures)} dangling path(s) out of {checked} checked:", file=sys.stderr)
    for f in failures:
        print(f"  - {f}", file=sys.stderr)
    sys.exit(1)

print(f"check-doc-paths: OK — {checked} path(s) checked across {len(DOCS)} docs, all resolve.")
PYEOF
