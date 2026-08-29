---
name: fractal-runner
description: >
  Install and operate the FRACTAL Scheduled Runner. Drives the full setup — runs every
  deterministic step itself, and PAUSES at each permission gate (FRACTAL_REPOS_ROOT,
  gh auth scopes, systemd --user / launchd availability, schedule install) with an explanation
  and a copy-able command for the user to run in a second terminal. Covers three paths: local
  computer (systemd --user or launchd), VM (systemd --user + Persistent=true), and manual
  (on-demand run.sh, no scheduler). Use when the user asks to install or set up the
  fractal runner, install the scheduled runner, or run the fractal runner.
disable-model-invocation: true
---

# /fractal-runner — Scheduled FRACTAL Runner install + operate

You are driving a teammate through setup and operation of the FRACTAL Scheduled Runner. The
runner lives at `tools/scheduled-fractal-runner/` in this repo. This plugin is installer-only:
no runner code is duplicated here; the plugin provides this guided setup skill only.

Reference docs (load these if needed):
- `${CLAUDE_PLUGIN_ROOT}/skills/fractal-runner/references/install-guide.md` — the three-path install guide
- `tools/scheduled-fractal-runner/README.md` — the runner's own reference (files, safety model, running it)

## Operating rules

1. **Run everything you can; gate everything you must.** Deterministic steps (state detection,
   dry-run verification) you execute yourself. The four gates below you NEVER run or work around —
   present the why + a copy-able command, then pause with AskUserQuestion.
2. **One gate at a time, JIT.** Don't dump all gates up front. Reach a gate, present it, wait,
   then verify with the listed probe before moving on.
3. **Verify, never trust.** A gate is done when its probe passes, not when the user says so.
4. **Log new friction.** Any failure not covered here should be reported to the user as a
   possible gap in this skill or the runner's docs.

## Step 1 — Detect environment (you run these, report as a table)

```bash
uname -sm                                            # Darwin arm64 = macOS; Linux = VM or server
command -v claude gh git jq systemctl launchctl || true
echo "FRACTAL_REPOS_ROOT=${FRACTAL_REPOS_ROOT:-<unset>}"
gh auth status 2>&1 | head -5 || true
```

Report as a compact table:

| Check | Result |
|-------|--------|
| Platform | ... |
| claude / gh / git / jq | present / missing |
| FRACTAL_REPOS_ROOT | set / unset |
| gh auth | authenticated / NOT |

Platform routing:
- **macOS (Darwin):** launchd path; `launchctl` present; see Gate 3 (macOS note).
- **Linux with systemd:** systemd `--user` path; `systemctl` present.
- **Linux without systemd (rare):** manual-only path; note it clearly.

## Step 2 — Dry-run (you run this)

Navigate to the runner and run plan mode. This requires no model calls, no GitHub writes:

```bash
cd tools/scheduled-fractal-runner
# FRACTAL_REPOS_ROOT should point at the directory containing this repo's sibling checkouts
# (registry targets are resolved as ${FRACTAL_REPOS_ROOT}/${target.repo_dir}). If you only
# review this repo itself, set it to the parent of this checkout.
export FRACTAL_REPOS_ROOT="${FRACTAL_REPOS_ROOT:-..}"
bash run.sh --mode plan
```

Expected output lines include `WOULD-REVIEW`, `SKIP` (draft/unchanged), and a `DONE ... failed=0` tail.
If you see `repos root ... not found` → Gate 1 is needed immediately.

## Step 3 — Gates (JIT, one at a time)

For each gate: explain in ≤3 sentences **why it is the user's to run**, show the command in a
copy-able fenced block, then `AskUserQuestion` (options: "Done — verify it" / "Defer").

| # | Gate | Why it's human-only | Command | Verify probe |
|---|------|--------------------|----|------|
| 1 | `FRACTAL_REPOS_ROOT` | The variable tells the runner where your sibling repo checkouts live. It must match *your* machine's layout — only you know that. | `export FRACTAL_REPOS_ROOT="$HOME/dev"` (macOS) or `export FRACTAL_REPOS_ROOT="/home/you/src"` (Linux); persist: `echo 'export FRACTAL_REPOS_ROOT=...' >> ~/.zshrc` (or `~/.bashrc`) | `ls "${FRACTAL_REPOS_ROOT}/fractal-agent-system"` lists files |
| 2 | `gh` auth + scopes | The runner calls GitHub APIs with *your* identity; only you can authorize that. | `gh auth status` — if scopes missing: `gh auth refresh -s repo,read:org` | `gh auth status` shows `repo` in Token scopes |
| 3 | Schedule install | Registering a scheduler unit (systemd or launchd) modifies your user environment — a trust decision only you can make. | **Linux:** `cd tools/scheduled-fractal-runner && FRACTAL_REPOS_ROOT="$FRACTAL_REPOS_ROOT" ./install-schedule.sh install --mode review --job pr-review` (adds systemd --user timer) **macOS:** same command — installs launchd LaunchAgent | **Linux:** `systemctl --user list-timers fractal-runner.timer` shows next fire **macOS:** `launchctl list | grep com.fractal-agent-system.fractal-runner` shows PID/status |
| 4 | Arm live (optional, post sign-off) | `live` mode posts inline GitHub comments with your token — a deliberate, human-authorised action after you've read sample reviews. | `cd tools/scheduled-fractal-runner && FRACTAL_REPOS_ROOT="$FRACTAL_REPOS_ROOT" ./install-schedule.sh install --mode live --job pr-review` | `./install-schedule.sh status` shows mode=live in unit definition |

Gate 4 is intentionally deferred. Present it only when the user asks to arm posting.

## Step 4 — On-demand / manual run (no scheduler)

If the user wants to run on-demand only (no scheduler), skip Gate 3 entirely:

```bash
cd tools/scheduled-fractal-runner

# Dry-run: prove discovery, no model/post
./run.sh --mode plan

# One real review (never posts; writes runs/<date>/<slug>-pr<n>.md)
./run.sh --mode review --only fractal-agent-system --pr <N>

# All open PRs, review mode
./run.sh --mode review
```

## Step 5 — Security posture (state verbatim, never elide)

Present this before any `review` or `live` run so the user understands the constraints:

> **`review` is the safe default.** It runs the never-posts triage skill, writes artifacts locally,
> and posts nothing to GitHub. Every permission the headless agent gets is explicitly listed in
> `registry.json` `claude_allowed_tools_review`; the deny list takes precedence and blocks
> code mutation, `git push`, exfiltration (`curl`/`ssh`/`gh gist`), and language interpreters.
>
> **`live` requires explicit operator sign-off and is registry-only.** It posts inline PR comments
> — never commits, merges, or approves. Run it only on registered targets. Auto-fix is disabled
> in every mode.
>
> **The untrusted `--review-requested` sweep stays disabled** (`sweep.enabled=false` in
> `registry.json`) pending a `--permission-prompt-tool` classifier or a no-egress sandbox
> (`bwrap`, read-only worktree, network limited to `api.github.com`). See `registry.json`'s
> `_tools_note` for the full threat-model rationale.
>
> This is hardening, not a sandbox. The residual risk is that `gh`-read reaches what your token
> can, and `live`'s `gh api` can mutate. That is why `live` needs explicit sign-off.

## Step 6 — Closing summary

```
Platform:         [Darwin arm64 / Linux systemd / manual-only]
Repos root:       $FRACTAL_REPOS_ROOT
Dry-run:          DONE ... failed=0  [check]
gh auth:          repo scope [check]
Schedule:         [review / live / manual] installed / deferred
Pilot mode:       review (never posts)
Next action:      [./run.sh --mode review --only fractal-agent-system --pr N  OR  wait for first scheduled fire]
```

Never report a gate done without its probe having passed in this session.

## Gotchas

- **This skill is user-only** (`disable-model-invocation: true`) — it installs schedulers
  (systemd `--user` / launchd) and touches `gh auth`, so it must never self-fire; only an
  explicit `/fractal-runner` invocation starts it.
- **`live` mode posts real GitHub PR comments.** It requires explicit operator sign-off (Step 5)
  — never arm Gate 4 on your own judgment.
- **macOS/launchd does not catch up on missed runs** (sleep) — a VM with systemd is the
  reliable-coverage path; note this to the user rather than silently under-reporting misses.
- **`FRACTAL_REPOS_ROOT` mismatches silently break discovery** — always verify with the Gate 1
  probe (`ls "${FRACTAL_REPOS_ROOT}/fractal-agent-system"`) rather than trusting a prior
  session's export.

## Common failures

| Symptom | Fix |
|---------|-----|
| `repos root ... not found` | Set/export `FRACTAL_REPOS_ROOT` (Gate 1) |
| `gh token missing 'repo' scope` | `gh auth refresh -s repo,read:org` (Gate 2) |
| `Skill not found / empty review` | `.claude/plugins/` was deleted or moved in this checkout; restore from git |
| `claude: command not found` in scheduler logs | Your tools moved; re-run `install-schedule.sh install` to regenerate the PATH-baked unit |
| Nothing happened overnight (macOS) | Mac slept through the interval; launchd does not catch up. Keep the Mac awake, or accept gaps. Use a VM for reliable coverage. |
| Slow or overlapping runs | `flock` single-flight lock prevents overlap. Slow = many changed PRs reviewed sequentially. Adjust `--only <slug>` to scope. |
