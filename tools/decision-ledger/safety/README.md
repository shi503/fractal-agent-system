# Decision Ledger v2 — Multi-User Safety Layer

This directory implements the **pessimistic multi-user safety layer** for the
decision-log. It closes FM-7 (the "multi-user theatre" failure mode) by ensuring
that no concurrent edit can silently overwrite another actor's work.

## Architecture

```
tools/decision-ledger/safety/
├── pre_commit_hook.py      — git pre-commit gate (intercepts both scripted and direct-editor paths)
├── conflict_resolver.py    — preserves both versions, flips status to conflicted
├── active_locks_view.py    — generates views/active-locks.md on every lock event
├── test_multi_user_safety.py — four smoke tests + supporting tests
├── install.sh              — idempotent hook installer
└── README.md               — this file
```

## The two write paths — both protected

```
Scripted path (dl CLI / write_adapter.py):
  dl lock <ID> --actor <A>
  → dl write <ID> ...            (store.write → _check_lock → permit/PermissionError)
  → dl unlock <ID> --actor <A>

Direct editor save (e.g. an Obsidian vault synced via obsidian-git):
  user edits decision-log/D-9001.md directly
  → the editor's git integration stages the file
  → git commit triggers .git/hooks/pre-commit
  → pre_commit_hook.py checks lock table
  → permit (with warning if no lock) or REJECT
```

Both paths share the **same SQLite lock table** (`.index.sqlite` in the store root).
The lock table is the single source of truth for "who is editing what".

## Installation

```bash
# Install the pre-commit hook (idempotent)
bash tools/decision-ledger/safety/install.sh

# Configure your actor initials (used by the hook when DL_ACTOR is not set)
git config user.initials AR
```

To uninstall:
```bash
bash tools/decision-ledger/safety/install.sh --uninstall
```

## Lock TTL renewal

The default lock TTL is **5 minutes**. Long editing sessions must renew before
the TTL elapses:

```bash
# Renew the lock for another 5 minutes
python3 tools/decision-ledger/storage/cli.py \
  --store <decision-log-dir> \
  lock-renew D-9001 --actor AR

# Or renew for 10 minutes explicitly
python3 tools/decision-ledger/storage/cli.py \
  --store <decision-log-dir> \
  lock-renew D-9001 --actor AR --ttl 600
```

A long-running scripted caller should renew every 4 minutes or so.

## Conflict resolution

When a race is detected, `conflict_resolver.resolve_conflict()` is called:

1. The canonical `D-9001.md` is **preserved** with status flipped to `conflicted`.
2. The competing version is written to `D-9001.conflict-<actor>-<timestamp>.md`.
3. An audit row `(operation='conflict')` is written naming both actors.

A RACI R/A holder resolves the conflict manually:
```bash
# After manual resolution, reset status and commit
python3 tools/decision-ledger/storage/cli.py \
  --store <decision-log-dir> \
  write D-9001 --actor AR --set "status=answered"
git add <decision-log-dir>/
git commit -m "chore(ledger): D-9001 conflict resolved — AR-R"
```

## Active-locks view

`views/active-locks.md` is regenerated on every pre-commit hook run. It shows:
- Entry ID, actor, acquisition time, expiry, TTL remaining
- Stale/expired locks waiting to be swept

View it with any markdown reader or `cat views/active-locks.md`.

## Audit log

Every event is recorded in `.index.sqlite` / `audit_log`:

| Operation    | When recorded |
|-------------|--------------|
| `lock`       | Lock acquired |
| `lock_renew` | Lock TTL extended |
| `unlock`     | Lock released |
| `write`      | Entry written (scripted or hook) |
| `conflict`   | Race detected; both versions preserved |
| `rebuild`    | Index rebuilt from markdown |
| `delete`     | Entry removed |

Query:
```bash
python3 tools/decision-ledger/storage/cli.py \
  --store <decision-log-dir> \
  audit --id D-9001
```

---

## Regression checklist

The four smoke-test scenarios below. Run after any change to the storage or
safety layer.

### Smoke Test 1 — Skill–Skill (concurrent `dl write`)

**Scenario:** AR and RV both attempt to write D-9001 via the `dl` CLI simultaneously.

**Expected:**
- [ ] AR acquires the lock first (`dl lock D-9001 --actor AR` returns `Lock acquired`)
- [ ] RV's lock attempt returns `LOCKED: D-9001 is held by AR until <expiry>` (exit 2)
- [ ] RV's `dl write D-9001 --actor RV` raises `PermissionError` and exits non-zero
- [ ] AR's write succeeds; D-9001.md is updated
- [ ] Audit log contains: `lock` (AR), `write` (AR); no write row for RV

**Automated test:** `TestSmokeSkillSkill` in `test_multi_user_safety.py`

---

### Smoke Test 2 — Editor–editor (two direct-file saves)

**Scenario:** AR and RV both save `decision-log/D-9001.md` directly (e.g. through an
editor's own git integration). AR commits first and holds the lock; RV's commit
arrives while AR's lock is active.

**Expected:**
- [ ] AR's commit passes the pre-commit hook (lock held by AR, actor = AR → authorised)
- [ ] RV's commit is **rejected** by the hook: exit 1 with `[LOCK CONFLICT] D-9001`
- [ ] D-9001.md on disk contains only AR's version
- [ ] No silent overwrite occurred

**How to run manually:**
```bash
# Simulate AR committing (hook allows):
DL_ACTOR=AR git commit --allow-empty -m "test: AR commit"

# Simulate RV committing while AR holds the lock:
DL_ACTOR=RV git commit --allow-empty -m "test: RV commit — should be rejected"
# Expected: pre-commit hook exits 1, commit aborted
```

**Automated test:** `TestSmokeEditorEditor` in `test_multi_user_safety.py`

---

### Smoke Test 3 — Skill–editor (mixed path)

**Scenario:** AR uses the `dl` CLI to write D-9001 (acquires lock, writes). Then RV
saves D-9001.md directly with a competing version.

**Expected:**
- [ ] AR's scripted write succeeds; lock is active
- [ ] RV's competing direct save triggers `resolve_conflict()`
- [ ] `D-9001.md` status = `conflicted`; both versions preserved
- [ ] Sidecar `D-9001.conflict-RV-<timestamp>.md` exists with RV's content
- [ ] Audit log contains: `lock` (AR), `write` (AR), `conflict` (AR+RV)

**Automated test:** `TestSmokeSkillEditor.test_skill_then_editor_conflict`

---

### Smoke Test 4 — Lock-expire race (the guard's most subtle case)

**Scenario:** AR acquires a lock and writes. The lock expires (TTL elapsed). RV
writes a competing version via any path. Both writes succeed but the second one
preserves both versions and flips status to `conflicted` — no silent overwrite.

**Expected:**
- [ ] AR's write (with short TTL) succeeds
- [ ] After TTL expires, RV's write succeeds but triggers `resolve_conflict()`
- [ ] `D-9001.md` status = `conflicted`
- [ ] Sidecar `D-9001.conflict-RV-<timestamp>.md` contains RV's content
- [ ] Audit log contains: `conflict` operation
- [ ] A solo write after lock expiry (same actor, no competitor) does NOT conflict

**How to force-expire for manual testing:**
```bash
# Acquire a 1-second lock
python3 tools/decision-ledger/storage/cli.py \
  --store <decision-log-dir> \
  lock D-9001 --actor AR
sleep 6  # wait for 5-min TTL... or use the test which patches TTL to 1s

# Write as AR first
python3 tools/decision-ledger/storage/cli.py \
  --store <decision-log-dir> \
  write D-9001 --actor AR --body "AR answer after expire"
```

**Automated test:** `TestSmokeLockExpireRace` in `test_multi_user_safety.py`

---

## Running the tests

```bash
python3 tools/decision-ledger/safety/test_multi_user_safety.py
# or:
python3 -m pytest tools/decision-ledger/safety/test_multi_user_safety.py -v
```

All four smoke tests plus the supporting tests must pass.

---

## Known edge cases and limitations

1. **Shared-mount users**: if two users mount the same store path via a network
   filesystem and commit independently without push/pull, the pre-commit hook only
   sees the local lock table. Recommendation: use a local clone per user and sync
   through git, not a shared live mount.

2. **Force-push / `git commit --no-verify`**: bypasses the hook. This is a git-level
   escape hatch that bypasses all pre-commit hooks; enforce via branch protection on
   the default branch (`required_status_checks` or `push` restriction).

3. **Conflict sidecar cleanup**: sidecar files (`.conflict-*.md`) accumulate until a
   RACI R/A holder resolves the conflict and deletes the sidecar. No auto-cleanup.
   The validate CLI ignores sidecar filenames (they don't match the entry ID pattern).

4. **Lock table in SQLite**: the `.index.sqlite` file must be on the same filesystem
   for POSIX atomic rename to work. Remote filesystems (NFS, some network-share
   configs) may not honour `rename(2)` atomicity — mitigated by working from a local
   clone.

5. **macOS temp-dir symlinks**: on macOS, paths under `/tmp` and `/var` often resolve
   through a `/private/...` symlink. `pre_commit_hook.run_hook()` resolves both the
   store root and the repo root before computing a relative path, specifically to stay
   correct when one side of that comparison has been resolved and the other hasn't.
