# Scheduled FRACTAL Runner — Install Guide

**Runner:** `tools/scheduled-fractal-runner/` in this repo checkout
**Pilot status:** default mode is `review` (never posts) until an operator explicitly arms `live`

---

## Prerequisites (all paths)

Check each. The runner asserts most of these and aborts loudly if anything is missing.

| Need | Check | Fix |
|------|-------|-----|
| This repo checked out | you are running from inside it | `git clone` this repo |
| Any additional registry targets checked out | `ls $FRACTAL_REPOS_ROOT/<repo_dir>` for each `targets[]` entry in `registry.json` | `git clone` them under one parent directory |
| `gh` CLI authenticated | `gh auth status` shows your login + `repo, read:org` scopes | `gh auth login` then `gh auth refresh -s repo,read:org` |
| `claude` CLI logged in | `claude -p "say ok"` returns text | `claude` (interactive) once to log in |
| `jq`, `git` | `jq --version`, `git --version` | `brew install jq` / `apt-get install jq` |
| For gate-evidence job only — the build/test tooling each registered target's `gate_cmd` needs | run the target's `gate_cmd` manually once | install separately; optional for PR-review-only setup |

The PR-review skills the runner invokes are plugins inside this checkout — injected via
`--plugin-dir`. Do not install them globally; do not delete `.claude/plugins/` from your clone.

## Path A — Local computer (macOS / Linux desktop)

**When to use:** your personal development laptop or desktop machine. You want the runner to fire hourly and review changed PRs automatically.

### macOS (launchd LaunchAgent)

```bash
cd tools/scheduled-fractal-runner

# 1. Set your repos root (the directory that CONTAINS this repo, and any other registry targets)
export FRACTAL_REPOS_ROOT="$HOME/dev"
echo 'export FRACTAL_REPOS_ROOT="$HOME/dev"' >> ~/.zshrc   # persist

# 2. Dry-run — prove discovery works, no model/post
./run.sh --mode plan

# 3. Install the hourly launchd agent (review mode — never posts)
./install-schedule.sh install --mode review --job pr-review

# 4. Confirm
./install-schedule.sh run-now      # fire immediately
./install-schedule.sh status       # verify loaded
tail -f run.log                    # watch output
```

**macOS limitation:** launchd does NOT catch up fires the Mac sleeps through. It runs at the next interval after wake. Keep the Mac awake (AC power, "Prevent sleep" on) if you want reliable hourly coverage. A VM is the more reliable choice for an always-on schedule.

**macOS log paths:** `tools/scheduled-fractal-runner/launchd.out.log` and `launchd.err.log`

### Linux desktop (systemd --user)

Same as VM path (Path B). `--user` timers require an active login session unless you also run `loginctl enable-linger $USER` (see Path B).

---

## Path B — VM (systemd --user + Persistent=true)

**When to use:** a Linux VM or server. `systemd --user` with `Persistent=true` catches up any fires that were missed while the machine was asleep or the user was logged out (if linger is enabled).

```bash
cd tools/scheduled-fractal-runner

# 1. Set your repos root
export FRACTAL_REPOS_ROOT="$HOME/src"       # adjust to your checkout location
echo 'export FRACTAL_REPOS_ROOT="$HOME/src"' >> ~/.bashrc   # persist

# 2. Dry-run
./run.sh --mode plan

# 3. Install the hourly systemd --user timer (review mode — never posts)
./install-schedule.sh install --mode review --job pr-review
# The installer attempts 'loginctl enable-linger $USER' automatically.
# If you see a sudo note, run:
#   sudo loginctl enable-linger $USER
# Without it, the timer only fires while you are logged in.

# 4. Confirm
./install-schedule.sh run-now
./install-schedule.sh status
journalctl --user -u fractal-runner.service -f   # live log
```

**Concurrency = 1 (hard constraint).** The runner uses `flock` to prevent two scheduled fires from overlapping. Targets and PRs are reviewed strictly sequentially — there is no parallel path. A parallel headless-`claude` fan-out risks OOM on a small VM; do not attempt to parallelise.

**Persistent=true behaviour:** if the system was off when the scheduled time passed, systemd will catch up the missed fire on next boot/login. This is the key advantage of the VM path over macOS launchd.

---

## Path C — Manual / on-demand (no scheduler)

**When to use:** you want to run reviews on-demand, or you are evaluating the runner before committing to an hourly schedule. This path has zero prerequisites beyond the ones listed above.

```bash
cd tools/scheduled-fractal-runner
export FRACTAL_REPOS_ROOT="..."   # set once

# Dry-run (safe, no model, no post)
./run.sh --mode plan
./run.sh --mode plan --job pr-review       # just discovery

# One real review — never posts; writes runs/<date>/<slug>-pr<n>.md
./run.sh --mode review --only fractal-agent-system --pr <N>

# All open PRs across all registry targets (review mode)
./run.sh --mode review

# Read the review artifact
less runs/$(date -u +%Y-%m-%d)/fractal-agent-system-pr<N>.md
```

No install step needed. No daemon. Re-run whenever you want a fresh review.

---

## Security posture (do not elide)

**`review` is the safe default.** The headless session runs the never-posts triage skill, writes review artifacts to `runs/<date>/`, and posts nothing to GitHub. The Bash allowlist is read-only: `gh pr view/diff/checks/list`, `git log/show`, `cat/ls/head/tail/wc/jq`. No `find`, `rg`, `sed`, `awk`, `gh api`. Claude's native `Read`/`Grep`/`Glob` tools handle code inspection (no shell escape). The deny list takes precedence and blocks code mutation, `git push`, exfiltration (`curl`/`ssh`/`gh gist`), and language interpreters (`perl`/`python`/`node`/`sh`).

**`live` requires explicit operator sign-off and is registry-only.** It posts inline PR comments using the posting skill. Never commits, merges, or approves. Auto-fix disabled in every mode. Arm posting after you have read and approved several sample `review`-mode artifacts.

**The `--review-requested` sweep stays disabled** (`sweep.enabled=false` in `registry.json`) pending a `--permission-prompt-tool` classifier or a no-egress sandbox (`bwrap`, read-only worktree, network limited to `api.github.com`). Re-enabling the sweep on untrusted repos without this is a real security risk (prompt injection) — see `registry.json`'s `_tools_note` for the full rationale.

**This is hardening, not a sandbox.** Residual: `gh`-read reaches what your token can; `live`'s `gh api` can mutate. That is why `live` needs explicit sign-off.

---

## Arming live (deliberate, post sign-off)

After reviewing several `review`-mode artifacts and confirming quality:

```bash
./install-schedule.sh install --mode live --job pr-review
```

Three things to know before arming:

1. **Comment-only, always.** `live` posts inline PR comments and never commits, pushes, merges, or approves — enforced at the permission layer (deny list: `Edit`, `Write`, `git push/commit`). Auto-fix is disabled.
2. **Don't have two operators post on the same registry PRs.** If more than one person runs `live` on the same targets, each PR gets duplicate bot comments. Coordinate: one person runs `live` on the registry targets; others stay `--mode review`.
3. **Keep the sweep off `live`.** Reviewing untrusted external PRs with a posting agent requires the classifier/sandbox that is still a follow-up. Registry targets only for now.

---

## Day-2 operations

| Task | How |
|------|-----|
| Add a repo to the rotation | Edit `registry.json` → `targets[]` (`repo_slug`, `owner`, `repo_dir`, `branch`, `gate_cmd`, `gate_subdir`, `enabled`, `jobs`). No code change. |
| Include gate evidence | Install with `--job all`. Heavier: runs each target's `gate_cmd` on IN_PROGRESS workstreams each hour. |
| Change cadence | **Linux:** edit `OnCalendar` in `~/.config/systemd/user/fractal-runner.timer`; or re-run the installer. **macOS:** edit `StartInterval` in `~/Library/LaunchAgents/com.fractal-agent-system.fractal-runner.plist`; or re-run the installer. |
| Pause / remove scheduler | `./install-schedule.sh uninstall` |
| Update after `git pull` | Re-run `./install-schedule.sh install` — regenerates units from the new script path with fresh PATH baking. |
| Check run history | `tail -200 tools/scheduled-fractal-runner/run.log` |
| Review a specific PR manually | `./run.sh --mode review --only <repo_slug> --pr <N>` |

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `repos root ... not found` | Set/export `FRACTAL_REPOS_ROOT` to the directory that contains this repo (and any other registry targets). |
| `gh token missing 'repo' scope` | `gh auth refresh -s repo,read:org` |
| `Skill not found / empty review` | `.claude/plugins/` was deleted or moved in your checkout. Restore: `git checkout -- .claude/plugins/`. The runner injects plugins via `--plugin-dir`; nothing to install globally. |
| `claude: command not found` in scheduler logs | Your `claude` binary moved. Re-run `./install-schedule.sh install` — it re-resolves `PATH` and bakes it into the scheduler unit. |
| Nothing happened overnight (macOS) | Mac slept through the launchd interval. launchd does not catch up. Keep the Mac awake or use a VM. |
| Runs overlap / scheduler skips | Normal: `flock` prevents overlap; the second fire exits 0 immediately ("single-flight"). Review runs are sequential by design. |
| `run.sh --mode plan` shows no targets | Registered target repos not checked out under `FRACTAL_REPOS_ROOT`. |
| `gh auth status failed` | `gh auth login` (interactive), or use a token-based path on a headless VM per `gh`'s own docs. |
