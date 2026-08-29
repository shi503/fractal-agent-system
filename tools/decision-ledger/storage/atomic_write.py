"""
Decision Ledger v2 — Atomic Write

Writes files via temp-file + atomic rename (POSIX rename(2) guarantee).
If the write fails mid-flight, the original file is untouched.

Language: Python 3.12 stdlib only — no external dependencies.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path


def atomic_write(dest: Path, content: str, encoding: str = "utf-8") -> str:
    """
    Write *content* to *dest* atomically.

    Steps:
      1. Write to a temporary file in the same directory as *dest*
         (ensures same filesystem, so rename is atomic on POSIX).
      2. fsync the temp file to flush OS buffers.
      3. os.replace() (atomic rename) to move temp → dest.

    Returns the SHA-256 hex digest of the written content (used by audit log).

    Raises OSError on any failure; the original *dest* is never partially written.
    """
    dest = dest.resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)

    encoded = content.encode(encoding)
    digest = hashlib.sha256(encoded).hexdigest()

    fd, tmp_path = tempfile.mkstemp(
        dir=dest.parent,
        prefix=".tmp-",
        suffix=".md",
    )
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(encoded)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, dest)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise

    return digest


def file_hash(path: Path, encoding: str = "utf-8") -> str:
    """Return the SHA-256 hex digest of a file's content, or '' if it doesn't exist."""
    try:
        raw = path.read_bytes()
        return hashlib.sha256(raw).hexdigest()
    except FileNotFoundError:
        return ""
