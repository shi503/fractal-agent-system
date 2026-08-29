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
EXCLUDE_DIRS = {".git", "node_modules", ".herenow", ".obsidian", "docs/fractal-harness-fork"}
TOKEN_RE = re.compile(r"[a-z0-9]+")
ALLOW_RE = re.compile(r"oss-scan-allow:\s*(\S+)")


def load_hashes(hashes_path: Path) -> set[str]:
    with hashes_path.open() as f:
        payload = json.load(f)
    return set(payload.get("hashes", []))


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


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


def scan(root: Path, rel_paths: list[str], scan_scope: str, hashes: set[str]) -> tuple[list[str], list[str]]:
    hits: list[str] = []
    allowlist_uses: list[str] = []

    for rel_path in rel_paths:
        if is_excluded(rel_path, scan_scope):
            continue
        abs_path = root / rel_path

        # Path-itself check (full-digest match).
        path_tokens = tokenize(rel_path)
        path_candidates = [t for t in path_tokens if len(t) >= MIN_TOKEN_LEN]
        path_candidates += [
            path_tokens[i] + path_tokens[i + 1]
            for i in range(len(path_tokens) - 1)
            if len(path_tokens[i] + path_tokens[i + 1]) >= MIN_TOKEN_LEN
        ]
        for cand in path_candidates:
            full = hashlib.sha256(cand.encode("utf-8")).hexdigest()
            if full in hashes:
                hits.append(f"{rel_path}:0:{full[:8]}")

        if not abs_path.is_file() or is_binary(abs_path):
            continue
        try:
            lines = abs_path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue

        for lineno, text in enumerate(lines, start=1):
            allow_match = ALLOW_RE.search(text)
            tokens = tokenize(text)
            candidates = [t for t in tokens if len(t) >= MIN_TOKEN_LEN]
            candidates += [
                tokens[i] + tokens[i + 1]
                for i in range(len(tokens) - 1)
                if len(tokens[i] + tokens[i + 1]) >= MIN_TOKEN_LEN
            ]
            for cand in candidates:
                full = hashlib.sha256(cand.encode("utf-8")).hexdigest()
                if full not in hashes:
                    continue
                if allow_match is not None and allow_match.group(1) in ("*", cand):
                    allowlist_uses.append(f"{rel_path}:{lineno}:{full[:8]}")
                else:
                    hits.append(f"{rel_path}:{lineno}:{full[:8]}")

    return hits, allowlist_uses


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

    hits, allowlist_uses = scan(scan_root, rel_paths, scan_scope, hashes)

    for a in allowlist_uses:
        print(f"ALLOWLISTED: {a}")
    for h in hits:
        print(h)

    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
