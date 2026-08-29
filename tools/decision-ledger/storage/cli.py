#!/usr/bin/env python3
"""
Decision Ledger v2 — CLI (`dl`)

Usage:
    dl read <ID>                     Print frontmatter + body for an entry
    dl write <ID> --body <text>      Write/update an entry body (keeps frontmatter)
    dl list [--status <s>] [--type <t>] [--layer <l>]   List entries
    dl rebuild-index                 Rebuild .index.sqlite from markdown
    dl verify                        Check index ↔ markdown consistency (FM-1)
    dl lock <ID> --actor <A>         Acquire a 5-minute lock
    dl unlock <ID> --actor <A>       Release a lock
    dl audit [--id <ID>]             Show audit log (all or for a single entry)

Global option:
    --store <path>   Store root directory
                     (default: decision-log/, relative to the
                      tools/decision-ledger/ parent)

Exit codes: 0 = success, 1 = validation/usage error, 2 = not found / locked.

Language: Python 3.12 stdlib only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


# Locate the decision-ledger root (two levels up from this file)
_DL_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_STORE = _DL_ROOT.parent / "decision-log"

sys.path.insert(0, str(Path(__file__).parent))
from store import DecisionStore  # noqa: E402
from frontmatter import render_entry  # noqa: E402


# ---------------------------------------------------------------------------
# Command implementations
# ---------------------------------------------------------------------------

def cmd_read(args: argparse.Namespace, store: DecisionStore) -> int:
    try:
        fm, body = store.read(args.id)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(render_entry(fm, body))
    return 0


def cmd_write(args: argparse.Namespace, store: DecisionStore) -> int:
    entry_id = args.id
    actor = args.actor

    # Load existing frontmatter if the file exists
    try:
        fm, existing_body = store.read(entry_id)
    except FileNotFoundError:
        fm = {"id": entry_id}
        existing_body = ""

    body = args.body if args.body is not None else existing_body

    # Apply any frontmatter patches from --set key=value pairs
    for kv in (args.set or []):
        if "=" not in kv:
            print(f"ERROR: --set requires key=value format, got: {kv!r}", file=sys.stderr)
            return 1
        k, _, v = kv.partition("=")
        fm[k.strip()] = v.strip()

    try:
        after_hash = store.write(entry_id, fm, body, actor)
    except PermissionError as exc:
        print(f"LOCKED: {exc}", file=sys.stderr)
        return 2
    print(f"Written {entry_id} (hash={after_hash[:12]}…)")
    return 0


def cmd_list(args: argparse.Namespace, store: DecisionStore) -> int:
    filters: dict[str, str] = {}
    if args.status:
        filters["status"] = args.status
    if args.type:
        filters["type"] = args.type
    if args.layer:
        filters["layer"] = args.layer
    if args.owner:
        filters["owner"] = args.owner

    entries = store.list_entries(filters or None)
    if not entries:
        print("(no entries)")
        return 0

    col_w = 10
    header = f"{'ID':<12} {'TYPE':<18} {'STATUS':<16} {'OWNER':<6} {'TITLE'}"
    print(header)
    print("-" * min(len(header) + 40, 100))
    for fm in entries:
        title = fm.get("title", "")
        if len(title) > 50:
            title = title[:47] + "..."
        print(
            f"{fm.get('id',''):<12} {fm.get('type',''):<18} {fm.get('status',''):<16} "
            f"{fm.get('owner',''):<6} {title}"
        )
    print(f"\n{len(entries)} entries.")
    return 0


def cmd_rebuild(args: argparse.Namespace, store: DecisionStore) -> int:
    stats = store.rebuild_index(actor=args.actor)
    print(
        f"Rebuild complete: "
        f"{stats['parsed']} parsed, "
        f"{stats['upserted']} upserted, "
        f"{stats['skipped']} skipped, "
        f"{stats['deleted']} deleted."
    )
    return 0


def cmd_verify(args: argparse.Namespace, store: DecisionStore) -> int:
    drift = store.verify_consistency()
    if not drift:
        print("FM-1 OK — index and markdown are consistent.")
        return 0
    print(f"FM-1 DRIFT DETECTED — {len(drift)} issue(s):")
    for msg in drift:
        print(f"  {msg}")
    return 1


def cmd_lock(args: argparse.Namespace, store: DecisionStore) -> int:
    acquired = store.lock(args.id, args.actor)
    if acquired:
        print(f"Lock acquired: {args.id} by {args.actor} (TTL 5 min)")
        return 0
    lock = store.get_lock(args.id)
    print(
        f"LOCKED: {args.id} is held by {lock['actor']} until {lock['expires_at']}",
        file=sys.stderr,
    )
    return 2


def cmd_unlock(args: argparse.Namespace, store: DecisionStore) -> int:
    released = store.unlock(args.id, args.actor)
    if released:
        print(f"Lock released: {args.id}")
        return 0
    lock = store.get_lock(args.id)
    if lock:
        print(
            f"ERROR: {args.id} is held by {lock['actor']}, not {args.actor}",
            file=sys.stderr,
        )
    else:
        print(f"No lock held on {args.id}")
    return 2


def cmd_lock_renew(args: argparse.Namespace, store: DecisionStore) -> int:
    ttl = getattr(args, "ttl", 300)
    renewed = store.renew_lock(args.id, args.actor, ttl_seconds=ttl)
    if renewed:
        lock = store.get_lock(args.id)
        print(f"Lock renewed: {args.id} by {args.actor} (new expiry: {lock['expires_at']})")
        return 0
    lock = store.get_lock(args.id)
    if lock:
        print(
            f"ERROR: lock on {args.id} is held by {lock['actor']}, not {args.actor}",
            file=sys.stderr,
        )
    else:
        print(f"No lock held on {args.id} — cannot renew", file=sys.stderr)
    return 2


def cmd_audit(args: argparse.Namespace, store: DecisionStore) -> int:
    sql = "SELECT rowid, entry_id, actor, operation, before_hash, after_hash, timestamp FROM audit_log"
    params: tuple = ()
    if args.id:
        sql += " WHERE entry_id = ?"
        params = (args.id,)
    sql += " ORDER BY rowid DESC LIMIT 50"
    rows = store.query(sql, params)
    if not rows:
        print("(no audit records)")
        return 0
    print(f"{'#':<5} {'ENTRY':<12} {'ACTOR':<6} {'OP':<10} {'TIMESTAMP':<22} BEFORE→AFTER")
    print("-" * 80)
    for row in rows:
        bh = row.get("before_hash", "")[:8] or "new"
        ah = row.get("after_hash", "")[:8] or "del"
        print(
            f"{row['rowid']:<5} {row['entry_id']:<12} {row['actor']:<6} "
            f"{row['operation']:<10} {row['timestamp']:<22} {bh}→{ah}"
        )
    return 0


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="dl",
        description="Decision Ledger v2 CLI",
    )
    p.add_argument(
        "--store",
        type=Path,
        default=None,
        help=f"Store root directory (default: {_DEFAULT_STORE})",
    )

    sub = p.add_subparsers(dest="command", required=True)

    # read
    pr = sub.add_parser("read", help="Read an entry")
    pr.add_argument("id")

    # write
    pw = sub.add_parser("write", help="Write or update an entry")
    pw.add_argument("id")
    pw.add_argument("--actor", default="CLI", help="Initials of the author")
    pw.add_argument("--body", default=None, help="Markdown body text")
    pw.add_argument("--set", action="append", metavar="KEY=VALUE", help="Set a frontmatter field")

    # list
    pl = sub.add_parser("list", help="List entries")
    pl.add_argument("--status", default=None)
    pl.add_argument("--type", default=None)
    pl.add_argument("--layer", default=None)
    pl.add_argument("--owner", default=None)

    # rebuild-index
    prb = sub.add_parser("rebuild-index", help="Rebuild index from markdown")
    prb.add_argument("--actor", default="CLI")

    # verify
    sub.add_parser("verify", help="FM-1 consistency check")

    # lock
    plk = sub.add_parser("lock", help="Acquire a lock on an entry")
    plk.add_argument("id")
    plk.add_argument("--actor", required=True)

    # unlock
    pul = sub.add_parser("unlock", help="Release a lock on an entry")
    pul.add_argument("id")
    pul.add_argument("--actor", required=True)

    # lock-renew
    plr = sub.add_parser("lock-renew", help="Renew (extend) an existing lock's TTL")
    plr.add_argument("id")
    plr.add_argument("--actor", required=True)
    plr.add_argument("--ttl", type=int, default=300, help="New TTL in seconds (default: 300)")

    # audit
    pau = sub.add_parser("audit", help="Show audit log")
    pau.add_argument("--id", default=None, help="Filter by entry ID")

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    store_root = args.store or _DEFAULT_STORE
    store = DecisionStore(Path(store_root))
    try:
        dispatch = {
            "read": cmd_read,
            "write": cmd_write,
            "list": cmd_list,
            "rebuild-index": cmd_rebuild,
            "verify": cmd_verify,
            "lock": cmd_lock,
            "unlock": cmd_unlock,
            "lock-renew": cmd_lock_renew,
            "audit": cmd_audit,
        }
        handler = dispatch.get(args.command)
        if handler is None:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            return 1
        return handler(args, store)
    finally:
        store.close()


if __name__ == "__main__":
    sys.exit(main())
