"""
Decision Ledger v2 — Active Locks View Generator

Regenerates views/active-locks.md on every lock event.
The view shows: entry ID, actor, acquired time, expiry time, whether expired.

Callable:
  - directly: python3 active_locks_view.py --store <path>
  - as a module: generate_active_locks_view(store_root)

Language: Python stdlib only.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

_SAFETY_DIR = Path(__file__).parent
_STORAGE_DIR = _SAFETY_DIR.parent / "storage"
sys.path.insert(0, str(_STORAGE_DIR))

from store import DecisionStore  # noqa: E402


# ---------------------------------------------------------------------------
# View generator
# ---------------------------------------------------------------------------

def generate_active_locks_view(store_root: Path) -> Path:
    """
    Query the lock table and write views/active-locks.md next to the store root.

    Returns the path of the generated file.
    """
    views_dir = store_root.parent / "views"
    views_dir.mkdir(parents=True, exist_ok=True)
    view_path = views_dir / "active-locks.md"

    store = DecisionStore(store_root)
    try:
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        rows = store.query(
            "SELECT id, actor, acquired, expires_at FROM locks ORDER BY acquired"
        )
    finally:
        store.close()

    lines: list[str] = [
        "# Active Locks — Decision Ledger",
        "",
        f"_Generated: {now_iso}_",
        "",
        "> This file is regenerated automatically on every lock/unlock event.",
        "> Do not edit manually.",
        "",
    ]

    if not rows:
        lines += [
            "## No active locks",
            "",
            "The decision-log is fully unlocked. Anyone may begin editing.",
        ]
    else:
        active = [r for r in rows if r["expires_at"] > now_iso]
        expired = [r for r in rows if r["expires_at"] <= now_iso]

        lines += [
            f"## Active locks ({len(active)})",
            "",
            "| Entry | Actor | Acquired | Expires | TTL remaining |",
            "|-------|-------|----------|---------|---------------|",
        ]
        for r in active:
            # Compute approximate remaining seconds
            try:
                import datetime
                exp_dt = datetime.datetime.strptime(r["expires_at"], "%Y-%m-%dT%H:%M:%SZ")
                exp_dt = exp_dt.replace(tzinfo=datetime.timezone.utc)
                now_dt = datetime.datetime.now(datetime.timezone.utc)
                remaining = max(0, int((exp_dt - now_dt).total_seconds()))
                ttl_str = f"{remaining}s"
            except Exception:
                ttl_str = "?"
            lines.append(
                f"| {r['id']} | {r['actor']} | {r['acquired']} | {r['expires_at']} | {ttl_str} |"
            )

        if expired:
            lines += [
                "",
                f"## Stale locks (expired, {len(expired)})",
                "",
                "These locks expired and can be safely swept. Run `dl lock --renew` or they",
                "will be overwritten on the next lock acquisition for those entries.",
                "",
                "| Entry | Actor | Acquired | Expired at |",
                "|-------|-------|----------|------------|",
            ]
            for r in expired:
                lines.append(
                    f"| {r['id']} | {r['actor']} | {r['acquired']} | {r['expires_at']} |"
                )

    lines.append("")
    view_path.write_text("\n".join(lines), encoding="utf-8")
    return view_path


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(
        prog="active-locks-view",
        description="Regenerate views/active-locks.md from the lock table.",
    )
    p.add_argument("--store", type=Path, required=True, help="Decision-log root directory")
    args = p.parse_args(argv)

    view_path = generate_active_locks_view(args.store.resolve())
    print(f"Written: {view_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
