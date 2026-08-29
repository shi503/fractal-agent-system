# Scheduled FRACTAL Runner

A single deterministic engine that, on a schedule, does two things across a registry
of repos:

1. **PR review** — discovers open PRs, skips drafts and unchanged heads, syncs each
   PR to an isolated git worktree, and runs a headless `claude -p` review inside a
   locked-down permission/allowlist sandbox (read-only in `review` mode; posts inline
   comments only, auto-fix disabled, in `live` mode).
2. **HANDOFF evidence** — for a registered target with an `IN_PROGRESS` FRACTAL
   workstream, runs that target's gate command and writes a machine-verified
   pass/fail evidence artifact.

This tool is structurally complete and its tests pass out of the box, but it is
**not wired up as a plugin skill yet** — the `fractal-runner` plugin skill that will
operate this tool end-to-end has not been filled in.

## Files

| File | Purpose |
|------|---------|
| `run.sh` | The engine. `--mode plan\|review\|live`, `--job pr-review\|handoff-evidence\|all`. |
| `lib.sh` | Deterministic helpers: logging, single-flight locking, JSON state read/write. |
| `install-schedule.sh` | Generates a systemd `--user` timer (Linux) or launchd agent (macOS). **Not run automatically** — placing this script here does not install anything on any machine. |
| `registry.json` | Target repo registry + tool-allowlist config. Synthetic: ships with exactly one target, this repo itself. |
| `state.json` | Per-PR "last reviewed SHA" ledger. Ships empty (`{}`) — no review history. |
| `tests/test-allowlist-safety.sh` | Static guard: fails the build if an exec-capable token (find, sed, gh api in review mode, …) re-enters the Claude tool allowlists. |
| `tests/eval-dryrun.sh` | Read-only AC1-7 scoring harness. On a fresh checkout (no `run.log`) it SKIPs the log-dependent checks (AC2-5) rather than failing — that's the expected state until someone actually runs the engine. |
| `.gitignore` | Excludes `run.log`, `.run.lock`, `_worktrees/`, `runs/` — `state.json` stays tracked by design. |

## Configuration

Set one environment variable before running:

```bash
export FRACTAL_REPOS_ROOT=/path/to/the/directory/containing/your/sibling/repo/checkouts
```

`repo_path` for a target is derived as `${FRACTAL_REPOS_ROOT}/${target.repo_dir}` — no
absolute path is ever baked into `registry.json`. To register more repos, add entries
to `registry.json`'s `targets[]` array; each needs `repo_slug`, `owner`, `repo_dir`,
`branch`, `gate_cmd`, `gate_subdir`, `enabled`, `jobs`.

## Safety

- **Concurrency is hard-capped at 1** — `lib.sh:acquire_lock` single-flights runs
  (`flock` on Linux, an atomic `mkdir` lock with stale-PID reclaim on macOS).
- **`--mode plan`** (the default) makes no model calls, posts nothing, and runs no
  gate commands — it only discovers and prints what *would* happen.
- **Review-mode allowlists are read-only.** PR code under review is untrusted;
  `tests/test-allowlist-safety.sh` statically guards that no exec-capable Bash token
  (`find`, `sed`, `awk`, `xargs`, `gh api`, language interpreters, …) is ever granted.
- **The `--review-requested=@me` sweep is disabled by default** (`sweep.enabled: false`)
  pending a permission-prompt classifier or no-egress sandbox — it is the path that
  touches genuinely arbitrary, unregistered external repos.
- **`install-schedule.sh install` has never been invoked.** No launchd agent or
  systemd timer exists on any machine as a result of this directory being present.

## Running it

```bash
cd tools/scheduled-fractal-runner
bash tests/test-allowlist-safety.sh
bash tests/eval-dryrun.sh
FRACTAL_REPOS_ROOT=.. ./run.sh --mode plan   # discovery only, no side effects
```
