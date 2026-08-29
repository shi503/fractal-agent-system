#!/usr/bin/env python3
"""Hashed contamination scanner (target-side).

Ships in this public repo so OSS CI can keep enforcing hygiene after the
port without ever learning the underlying denylist terms in cleartext — see
README.md in this directory for the full design rationale.

This scanner and hashes.json are DERIVED from a private, cleartext denylist
maintained in a separate (non-public) planning repo. hashes.json is
regenerated there and copied in verbatim; it is never hand-edited here.

Usage:
    python3 contamination_scan.py <path> [--changed-only]

Exit code: 0 = clean, non-zero = at least one hit. Output: one line per hit,
``file:line:<first-8-hex-of-digest>``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

MIN_TOKEN_LEN = 3
DIGEST_SUPPRESS_MAX_LEN = 4  # candidates this short or shorter get the digest-run check
EXCLUDE_DIRS = {".git", "node_modules", ".herenow", ".obsidian", "docs/fractal-harness-fork"}
TOKEN_RE = re.compile(r"[a-z0-9]+")
ALLOW_RE = re.compile(r"oss-scan-allow:\s*(\S+)")

# --- digest-run matcher rule (mirrors scripts/oss-contamination-scan.sh) ---
# A short candidate token/join can coincidentally hash-match purely because
# it sits inside a high-entropy digest (npm sha512 integrity strings,
# base64/base64url/hex blobs) — the tokenizer already splits on `+`, `/`,
# `=`, so a short alnum run bounded by those is a normal token to this
# scanner, digest or not. Suppressed per-occurrence, not by filename.
DIGEST_RUN_RE = re.compile(r"[A-Za-z0-9+/=_-]{24,}")


def is_digest_run(run_text: str) -> bool:
    # Real digests mix case and digits within any 24+ char stretch; kebab-/
    # snake-case prose identifiers are overwhelmingly lowercase-only.
    has_upper = any(c.isupper() for c in run_text)
    has_lower = any(c.islower() for c in run_text)
    has_digit = any(c.isdigit() for c in run_text)
    return has_upper and has_lower and has_digit


def digest_runs(text: str) -> list[tuple[int, int]]:
    return [
        (m.start(), m.end())
        for m in DIGEST_RUN_RE.finditer(text)
        if is_digest_run(m.group(0))
    ]


def in_digest_run(start: int, end: int, runs: list[tuple[int, int]]) -> bool:
    return any(run_start <= start and end <= run_end for run_start, run_end in runs)


def load_hashes(hashes_path: Path) -> set[str]:
    with hashes_path.open() as f:
        payload = json.load(f)
    return set(payload.get("hashes", []))


def tokenize(text: str) -> list[tuple[str, int, int]]:
    """Lowercased tokens with their (start, end) span in `text` (unchanged
    by lowercasing — ASCII case folding doesn't shift character offsets).
    """
    return [(m.group(0), m.start(), m.end()) for m in TOKEN_RE.finditer(text.lower())]


def is_binary(path: Path) -> bool:
    try:
        chunk = path.open("rb").read(8192)
    except OSError:
        return True
    return b"\x00" in chunk


def git_root(path: Path) -> Path | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(path if path.is_dir() else path.parent), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        )
        return Path(out.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def git_files(root: Path, rel_scope: str, changed_only: bool) -> list[str]:
    if changed_only:
        base_ref = None
        for candidate in ("main", "origin/main"):
            check = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "--verify", candidate],
                capture_output=True,
            )
            if check.returncode == 0:
                base_ref = candidate
                break
        if base_ref is None:
            print(f"error: --changed-only requires a 'main' or 'origin/main' ref in {root}", file=sys.stderr)
            sys.exit(2)
        cur_ref = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        args = ["git", "-C", str(root), "diff", "--name-only", "--diff-filter=ACMR", f"{base_ref}...{cur_ref}"]
        if rel_scope != ".":
            args += ["--", rel_scope]
        out = subprocess.run(args, capture_output=True, text=True, check=True)
        return [line for line in out.stdout.splitlines() if line.strip()]

    files: set[str] = set()
    for extra in (["ls-files"], ["ls-files", "--others", "--exclude-standard"]):
        args = ["git", "-C", str(root)] + extra
        if rel_scope != ".":
            args += ["--", rel_scope]
        out = subprocess.run(args, capture_output=True, text=True, check=True)
        files.update(line for line in out.stdout.splitlines() if line.strip())
    return sorted(files)


def walk_files(root: Path) -> list[str]:
    return sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file())


def is_excluded(rel_path: str, scan_scope: str) -> bool:
    for ex in EXCLUDE_DIRS:
        if scan_scope == ex or scan_scope.startswith(ex + "/"):
            continue  # explicitly requested as the scan path — don't exclude it
        if rel_path == ex or rel_path.startswith(ex + "/"):
            return True
    return False


def _candidates(tokens: list[tuple[str, int, int]]) -> list[tuple[str, int, int]]:
    """Every hashable token and adjacent-2-token join, each with its span."""
    out = [(t, s, e) for t, s, e in tokens if len(t) >= MIN_TOKEN_LEN]
    for i in range(len(tokens) - 1):
        (t1, s1, _e1), (t2, _s2, e2) = tokens[i], tokens[i + 1]
        join = t1 + t2
        if len(join) >= MIN_TOKEN_LEN:
            out.append((join, s1, e2))
    return out


def scan(
    root: Path, rel_paths: list[str], scan_scope: str, hashes: set[str]
) -> tuple[list[str], list[str], list[str]]:
    hits: list[str] = []
    allowlist_uses: list[str] = []
    digest_suppressed: list[str] = []

    for rel_path in rel_paths:
        if is_excluded(rel_path, scan_scope):
            continue
        abs_path = root / rel_path

        # Path-itself check (full-digest match).
        path_runs = digest_runs(rel_path)
        for cand, start, end in _candidates(tokenize(rel_path)):
            full = hashlib.sha256(cand.encode("utf-8")).hexdigest()
            if full not in hashes:
                continue
            if len(cand) <= DIGEST_SUPPRESS_MAX_LEN and in_digest_run(start, end, path_runs):
                digest_suppressed.append(f"{rel_path}:0:{full[:8]}")
            else:
                hits.append(f"{rel_path}:0:{full[:8]}")

        if not abs_path.is_file() or is_binary(abs_path):
            continue
        try:
            lines = abs_path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue

        for lineno, text in enumerate(lines, start=1):
            allow_match = ALLOW_RE.search(text)
            runs = digest_runs(text)
            for cand, start, end in _candidates(tokenize(text)):
                full = hashlib.sha256(cand.encode("utf-8")).hexdigest()
                if full not in hashes:
                    continue
                if len(cand) <= DIGEST_SUPPRESS_MAX_LEN and in_digest_run(start, end, runs):
                    digest_suppressed.append(f"{rel_path}:{lineno}:{full[:8]}")
                elif allow_match is not None and allow_match.group(1) in ("*", cand):
                    allowlist_uses.append(f"{rel_path}:{lineno}:{full[:8]}")
                else:
                    hits.append(f"{rel_path}:{lineno}:{full[:8]}")

    return hits, allowlist_uses, digest_suppressed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--changed-only", action="store_true")
    args = parser.parse_args()

    target = Path(args.path)
    if not target.exists():
        print(f"error: path not found: {target}", file=sys.stderr)
        return 2

    target_abs = target.resolve()
    hashes_path = Path(__file__).resolve().parent / "hashes.json"
    if not hashes_path.is_file():
        print(f"error: hashes.json not found: {hashes_path}", file=sys.stderr)
        return 2
    hashes = load_hashes(hashes_path)

    root = git_root(target_abs)
    if root is not None:
        rel_scope = str(target_abs.relative_to(root)) if target_abs != root else "."
        rel_paths = git_files(root, rel_scope, args.changed_only)
        scan_root = root
        scan_scope = rel_scope
    else:
        if args.changed_only:
            print(f"error: --changed-only requires <path> to be inside a git repo (got a non-git path: {target_abs})", file=sys.stderr)
            return 2
        if target_abs.is_dir():
            rel_paths = [str(p) for p in walk_files(target_abs)]
            scan_root = target_abs
        else:
            rel_paths = [target_abs.name]
            scan_root = target_abs.parent
        scan_scope = "."

    hits, allowlist_uses, digest_suppressed = scan(scan_root, rel_paths, scan_scope, hashes)

    for a in allowlist_uses:
        print(f"ALLOWLISTED: {a}")
    for d in digest_suppressed:
        print(f"DIGEST-SUPPRESSED: {d} (short token inside a high-entropy run)")
    for h in hits:
        print(h)
    if digest_suppressed:
        print(f"DIGEST SUPPRESSION SUMMARY: {len(digest_suppressed)} suppression(s)")

    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
