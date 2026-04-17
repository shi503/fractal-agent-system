# Claude Code Permissions Guide — Graduated Safety Tiers

**For:** FRACTAL team members onboarding to Claude Code
**Why this matters:** Without configuring permissions, you'll hit "Allow" / "Don't Allow" on **every** file edit and Bash command. That's 50+ interruptions per session. This guide lets you choose your comfort level and copy-paste a config that matches it.

---

## How it works (30-second version)

Claude Code checks every tool call against your permission rules:

```
deny  →  ask  →  allow
(first match wins; deny always beats allow)
```

Rules live in JSON files. You have two that matter:

| File | Git? | Who it affects |
|---|---|---|
| `.claude/settings.json` | ✅ Committed | Whole team — shared baseline |
| `.claude/settings.local.json` | ❌ Gitignored | You only — your comfort level |

**The team file sets the floor.** Your local file can add more permissions on top. If you need to deny something the team allows, local deny rules win.

---

## Rule syntax cheat sheet

```jsonc
{
  "permissions": {
    "allow": [
      "Bash(npm run *)",              // Wildcard — any npm run command
      "Bash(git commit *)",           // Any git commit variant
      "Bash(npx tsc --noEmit)",       // Exact command
      "Read(./.env.example)",         // Specific file (gitignore glob syntax)
      "Edit(src/**/*.ts)",            // All .ts files under src/
      "WebFetch(domain:github.com)",  // Specific domain
      "WebSearch",                    // All web searches (no specifier)
      "mcp__puppeteer__*"             // All tools from an MCP server
    ],
    "deny": [
      "Bash(rm -rf *)",              // Block dangerous deletes
      "Read(./.env)"                 // Block reading secrets
    ]
  }
}
```

**Key gotcha:** `Bash(npm run *)` (with space before `*`) only matches commands starting with `npm run `. Without the space, `Bash(npm*)` also matches `npmx`, `npm-cli`, etc.

---

## The Tiers

Pick the tier that matches your comfort level. Each tier includes everything from the tier below it.

---

### Tier 0 — Read-Only (built-in, no config needed)

These are **always auto-approved** regardless of your settings:

- `Read` — all file reads
- `Glob` — file pattern searches
- `Grep` — content searches
- Read-only Bash: `ls`, `cat`, `head`, `tail`, `grep`, `find`, `wc`, `diff`, `stat`, `du`
- Read-only git: `git status`, `git log`, `git diff`, `git branch`

**You get this for free.** No settings file needed. Claude can explore your codebase without interruption.

**Who this is for:** First day on the project. You want to ask Claude questions about the codebase but not let it change anything.

---

### Tier 1 — Safe Dev Loop

**Philosophy:** Let Claude run your CI gate without asking. These commands are read-only or produce only local build artifacts. Nothing leaves your machine.

```jsonc
// .claude/settings.local.json
{
  "permissions": {
    "allow": [
      // TypeScript & build
      "Bash(npx tsc *)",
      "Bash(npm run build)",
      "Bash(npm run build:*)",

      // Lint & format (read-only checks)
      "Bash(npm run lint)",
      "Bash(npm run format:check)",
      "Bash(npx eslint *)",
      "Bash(npx prettier --check *)",

      // Tests (local execution only)
      "Bash(npm test *)",
      "Bash(npm run test *)",
      "Bash(npm run test:run)",
      "Bash(npx vitest *)",
      "Bash(npx playwright test *)"
    ],
    "deny": [
      // Explicit safety net
      "Bash(rm -rf *)",
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./.env.local)"
    ]
  }
}
```

**What this unlocks:** Claude can verify its own work (build, lint, test) without interrupting you. This is the **single highest-leverage tier** — the official Anthropic best practices say *"give Claude a way to verify its work"* as the #1 recommendation.

**What still prompts:** File edits, `npm install`, git commits, web access, database commands.

**Who this is for:** You want Claude to check its own work but you want to approve every code change.

---

### Tier 2 — Active Development

**Philosophy:** Claude can edit code, install packages, manage the database, and commit — the normal development loop. You still approve anything that leaves your machine (push, publish, deploy).

```jsonc
// .claude/settings.local.json
{
  "permissions": {
    "allow": [
      // === Everything from Tier 1 ===
      "Bash(npx tsc *)",
      "Bash(npm run build)",
      "Bash(npm run build:*)",
      "Bash(npm run lint)",
      "Bash(npm run lint:fix)",
      "Bash(npm run format)",
      "Bash(npm run format:check)",
      "Bash(npx eslint *)",
      "Bash(npx prettier *)",
      "Bash(npm test *)",
      "Bash(npm run test *)",
      "Bash(npm run test:run)",
      "Bash(npx vitest *)",
      "Bash(npx playwright test *)",

      // === Tier 2 additions ===

      // Package management
      "Bash(npm install *)",
      "Bash(npm install)",
      "Bash(npm ls *)",
      "Bash(npm view *)",
      "Bash(npm outdated)",
      "Bash(npx shadcn@latest *)",

      // Database (local dev only)
      "Bash(npx prisma generate)",
      "Bash(npx prisma db push)",
      "Bash(npx prisma migrate dev *)",
      "Bash(npx prisma studio)",
      "Bash(npx prisma db seed)",
      "Bash(npx prisma format)",

      // Git (local operations only)
      "Bash(git add *)",
      "Bash(git commit *)",
      "Bash(git checkout *)",
      "Bash(git branch *)",
      "Bash(git stash *)",
      "Bash(git merge *)",
      "Bash(git rebase *)",

      // File operations
      "Bash(mkdir *)",
      "Bash(touch *)",
      "Bash(cp *)",
      "Bash(mv *)",

      // FRACTAL router
      "Bash(python3 *router.py *)"
    ],
    "deny": [
      // Nothing leaves your machine without approval
      "Bash(git push *)",
      "Bash(git push)",
      "Bash(npm publish *)",
      "Bash(npx prisma migrate reset)",
      "Bash(rm -rf *)",
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./.env.local)"
    ]
  }
}
```

**What this unlocks:** Full local development loop. Claude can write code, install deps, run migrations, commit changes, and verify everything — without interruption.

**What still prompts:** `git push`, `npm publish`, destructive database ops, reading secrets, web requests.

**Who this is for:** You trust Claude's edits and want a smooth coding flow, but you manually approve anything that ships or leaves your machine.

---

### Tier 3 — Extended Autonomy

**Philosophy:** Add web access, `gh` CLI for PRs/issues, and broader git ops. Claude can research, implement, and open PRs in one uninterrupted flow. You review the PR, not each individual action.

```jsonc
// .claude/settings.local.json
{
  "permissions": {
    "defaultMode": "acceptEdits",
    "allow": [
      // === Everything from Tier 2 ===
      "Bash(npx tsc *)",
      "Bash(npm run *)",
      "Bash(npm test *)",
      "Bash(npm install *)",
      "Bash(npm install)",
      "Bash(npm ls *)",
      "Bash(npm view *)",
      "Bash(npm outdated)",
      "Bash(npx shadcn@latest *)",
      "Bash(npx eslint *)",
      "Bash(npx prettier *)",
      "Bash(npx vitest *)",
      "Bash(npx playwright test *)",
      "Bash(npx prisma *)",
      "Bash(git add *)",
      "Bash(git commit *)",
      "Bash(git checkout *)",
      "Bash(git branch *)",
      "Bash(git stash *)",
      "Bash(git merge *)",
      "Bash(git rebase *)",
      "Bash(mkdir *)",
      "Bash(touch *)",
      "Bash(cp *)",
      "Bash(mv *)",
      "Bash(python3 *router.py *)",

      // === Tier 3 additions ===

      // Git remote (push to feature branches only)
      "Bash(git push origin feat/*)",
      "Bash(git push origin fix/*)",
      "Bash(git push origin chore/*)",
      "Bash(git push -u origin *)",
      "Bash(git pull *)",
      "Bash(git fetch *)",

      // GitHub CLI
      "Bash(gh pr *)",
      "Bash(gh issue *)",
      "Bash(gh api *)",
      "Bash(gh auth status)",
      "Bash(gh repo view *)",

      // Web research
      "WebSearch",
      "WebFetch(domain:github.com)",
      "WebFetch(domain:*.github.com)",
      "WebFetch(domain:registry.npmjs.org)",
      "WebFetch(domain:*.npmjs.org)",
      "WebFetch(domain:nextjs.org)",
      "WebFetch(domain:react.dev)",
      "WebFetch(domain:tailwindcss.com)",
      "WebFetch(domain:www.prisma.io)",
      "WebFetch(domain:supabase.com)",
      "WebFetch(domain:*.supabase.com)",
      "WebFetch(domain:developer.mozilla.org)",
      "WebFetch(domain:stackoverflow.com)"
    ],
    "deny": [
      // Hard boundaries
      "Bash(git push * main)",
      "Bash(git push * master)",
      "Bash(git push --force *)",
      "Bash(git push -f *)",
      "Bash(npm publish *)",
      "Bash(npx prisma migrate reset)",
      "Bash(rm -rf *)",
      "Bash(curl *)",
      "Bash(wget *)",
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./.env.local)"
    ]
  }
}
```

**Key change:** `"defaultMode": "acceptEdits"` — file edits no longer prompt. Claude writes code freely; you review via git diff / PR.

**What this unlocks:** Full autonomous feature development: research docs → plan → implement → test → commit → push branch → open PR. The PR is your review checkpoint.

**What still prompts:** Pushing to main, force-push, npm publish, destructive ops, reading secrets, `curl`/`wget`.

**Who this is for:** You're comfortable reviewing PRs rather than individual edits. Claude is your pair programmer, not a junior you're watching type.

---

### Tier 4 — Auto Mode

**Philosophy:** Let Claude's background safety classifier handle approvals. You intervene only when the classifier flags something risky. Best for long-running tasks where prompt fatigue defeats the purpose of having permissions.

```jsonc
// .claude/settings.local.json
{
  "permissions": {
    "defaultMode": "auto",
    "allow": [
      // Tier 3 allow list (same as above)
      // ...
    ],
    "deny": [
      // Hard boundaries (same as Tier 3 — classifier respects deny rules)
      "Bash(git push * main)",
      "Bash(git push * master)",
      "Bash(git push --force *)",
      "Bash(npm publish *)",
      "Bash(npx prisma migrate reset)",
      "Bash(rm -rf *)",
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./.env.local)"
    ]
  },
  "autoMode": {
    "environment": [
      "Organization: FRACTAL Agent System",
      "Source control: github.com/shi503/fractal-agent-system",
      "Stack: Next.js 15, TypeScript, Prisma, Supabase",
      "Safe to run: npm scripts, prisma commands, vitest, playwright"
    ],
    "soft_deny": [
      "Never run database migrations outside Prisma CLI",
      "Never force-push to main or master",
      "Never modify .claude/settings.json directly — use settings.local.json",
      "Never delete migration files"
    ]
  }
}
```

**How the classifier works:** A background model (Sonnet 4.6) reviews each action against your stated intent, your `soft_deny` rules, and built-in safety heuristics. It blocks: download-and-execute patterns (`curl | bash`), sending data to unknown endpoints, production deploys, mass cloud deletion.

**Fallback:** If the classifier blocks 3x in a row or 20x total, auto mode pauses and prompts you. Check `/permissions` → "Recently denied" to review.

**What still prompts:** Anything matching your explicit `deny` rules. Anything the classifier flags as risky (scope escalation, unknown infra, hostile-content-driven actions).

**Who this is for:** Long feature implementations, batch operations, or migration tasks where you'd otherwise click "Allow" 100+ times.

---

### Tier 5 — YOLO (Containers / VMs Only)

**Philosophy:** Everything is auto-approved. Only use this inside a disposable container, VM, or CI environment where nothing persists and nothing sensitive is accessible.

```jsonc
// .claude/settings.local.json
{
  "permissions": {
    "defaultMode": "bypassPermissions"
  }
}
```

**What this does:** Approves everything except writes to protected paths (`.git/`, `.claude/settings*`, `.vscode/`, `.husky/`). No classifier, no prompts.

**⚠️ Do NOT use this on your dev machine.** This is for:
- Ephemeral CI runners
- Docker containers with mounted workspaces
- VM-based cloud dev environments (Codespaces, Gitpod)
- Sandboxed testing environments

**To add OS-level sandboxing** (recommended even at lower tiers):

```bash
# macOS — uses Apple Seatbelt for filesystem/network restrictions
claude --sandbox

# Or configure in settings:
{
  "permissions": {
    "enableSandbox": true
  }
}
```

---

## Team-shared baseline (`.claude/settings.json`)

This goes in the committed file. It's the floor that applies to everyone:

```jsonc
// .claude/settings.json — committed to git
{
  "permissions": {
    "deny": [
      // Team-wide hard blocks — nobody can override these
      "Bash(npm publish *)",
      "Bash(git push --force *)",
      "Bash(git push -f *)",
      "Bash(rm -rf /)",
      "Read(./.env)",
      "Read(./.env.local)",
      "Read(./.env.production)"
    ],
    "allow": [
      // Safe reads everyone should have
      "Read(./.env.example)",

      // FRACTAL router (team-shared tooling)
      "Bash(python3 *router.py *)"
    ]
  }
}
```

**Why minimal:** The team file should deny dangerous things and allow shared tooling. Everything else is personal preference — that's what `settings.local.json` is for. Don't force Tier 3 on someone who wants Tier 1.

---

## Quick setup for new team members

```bash
# 1. Clone the repo (gets .claude/settings.json automatically)
git clone <repo-url> && cd <repo>

# 2. Pick your tier and copy the config
# Option A: Copy a template
cp docs/permission-templates/tier-2.json .claude/settings.local.json

# Option B: Start empty and build organically
echo '{"permissions":{"allow":[]}}' > .claude/settings.local.json
# Then click "Yes, don't ask again" as you work — rules accumulate

# 3. Verify .gitignore has the local file excluded
grep -q "settings.local.json" .gitignore || echo ".claude/settings.local.json" >> .gitignore
```

---

## Precedence rules (when things conflict)

```
Managed (IT-deployed)     ← Highest: cannot be overridden
  ↓
.claude/settings.local.json  ← Your personal overrides
  ↓
.claude/settings.json        ← Team-shared baseline
  ↓
~/.claude/settings.json      ← Your global defaults (lowest)
```

**Key rules:**
- **Deny always wins.** If the team file denies `npm publish`, your local file cannot allow it.
- **Arrays concatenate.** Your local `allow` list merges with (doesn't replace) the team's.
- **Symlink deny is strict.** A deny rule matches if *either* the symlink path *or* the target matches.

---

## Debugging permissions

```bash
# See all active rules and where they came from
/permissions

# In auto mode — see what the classifier blocked
/permissions → "Recently denied" tab

# Check if a specific command would be allowed
# (just try it — Claude will tell you if it's blocked)
```

---

## Common mistakes

| Mistake | Fix |
|---|---|
| 36 one-off rules from clicking "always allow" | Replace with tier-based wildcards (`Bash(npm run *)` instead of 12 specific commands) |
| No deny rules | Always deny: `.env` reads, `rm -rf`, force-push, `npm publish` |
| Using `Bash(*)` in allow | This allows *any* shell command — equivalent to YOLO mode. Use specific patterns. |
| Same rule in allow AND deny | Deny wins. Remove the allow rule to avoid confusion. |
| Putting personal prefs in `settings.json` | Use `settings.local.json` — don't force your comfort level on the team |
| Forgetting `settings.local.json` in `.gitignore` | Add it. It's auto-ignored in newer Claude Code versions but check. |

---

## Permission modes at a glance

| Mode | Shortcut | Auto-approves | Best for |
|---|---|---|---|
| `default` | — | Reads only | First day, sensitive work |
| `acceptEdits` | `Shift+Tab` | Reads + file edits + mkdir/touch/cp/mv | Active coding (Tier 3) |
| `plan` | `Shift+Tab` | Reads only (exploration) | Architecture review |
| `auto` | `Shift+Tab` | Everything (classifier-gated) | Long tasks (Tier 4) |
| `bypassPermissions` | CLI flag | Everything (no classifier) | Containers only (Tier 5) |

Switch modes mid-session with `Shift+Tab`. No restart needed.

---

## Reference: protected paths (always prompt, all modes)

These paths **always** require manual approval regardless of your tier:

- `.git/` — repository internals
- `.claude/settings*` — permission config itself
- `.vscode/`, `.idea/` — IDE config
- `.husky/` — git hooks
- `.gitconfig`, `.gitmodules`
- `.bashrc`, `.bash_profile`, `.zshrc`, `.zprofile` — shell config
