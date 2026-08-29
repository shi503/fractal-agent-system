---
name: fractal-setup
description: "Detect the contributor's current setup phase in this FRACTAL repo and walk them through the remaining onboarding steps: prerequisites, marketplace add, plugin install, and a router smoke run against the bundled fixture. Invoked via /fractal-setup."
argument-hint: "[optional: rerun]"
disable-model-invocation: true
---

# FRACTAL Setup — Onboarding Companion

You are bootstrapping a contributor onto this FRACTAL repo. The repo graduates through four
setup phases. Detect the current phase, then walk the contributor through their remaining
steps. Do not skip detection — the same user can be in different phases on different machines.

## Phases

- **Phase A** — Prerequisites unverified (Python 3 + PyYAML for `ROUTING_LOGIC/router.py`)
- **Phase B** — Prerequisites OK, marketplace not yet added / plugins not yet installed
- **Phase C** — Plugins installed, deterministic gates not yet run clean
- **Phase D** — Fully set up — `tools/validate-plugins.sh` and `tools/router-smoke.sh` both pass

## Steps

### 1. Detect current phase

Run these checks in sequence and print the results to the user:

```bash
# Prerequisite check
python3 --version 2>/dev/null && echo "PYTHON_OK" || echo "PYTHON_MISSING"
python3 -c "import yaml" 2>/dev/null && echo "PYYAML_OK" || echo "PYYAML_MISSING"

# Marketplace + plugin manifests present on disk (repo-side; does not confirm
# the plugins are installed in *this* Claude Code session — see Step 2)
test -f .claude-plugin/marketplace.json && echo "MARKETPLACE_MANIFEST_OK" || echo "MARKETPLACE_MANIFEST_MISSING"
for p in fractal-core fractal-planning fractal-tools fractal-wiki fractal-runner fractal-pr-review; do
  test -f ".claude/plugins/${p}/.claude-plugin/plugin.json" && echo "PLUGIN_MANIFEST_OK: ${p}" || echo "PLUGIN_MANIFEST_MISSING: ${p}"
done

# Deterministic gates
test -x tools/validate-plugins.sh && echo "VALIDATE_SCRIPT_OK" || echo "VALIDATE_SCRIPT_MISSING"
test -x tools/router-smoke.sh && echo "SMOKE_SCRIPT_OK" || echo "SMOKE_SCRIPT_MISSING"
test -d fixtures/taskflow && echo "FIXTURE_OK" || echo "FIXTURE_MISSING"
```

Report each result to the user in one line each. If `PYTHON_MISSING` or `PYYAML_MISSING` →
Phase A. If prerequisites are OK but plugin install has not been confirmed (Step 2 below) →
Phase B. Otherwise proceed to Step 3 (Phase C/D).

### 2. Confirm plugin install state

Whether the marketplace has been added and the plugins installed is Claude Code session
state, not something a repo-relative file check can see. Ask the user directly (use
`AskUserQuestion` if available):

> "Have you run `/plugin marketplace add` for this repo and installed the plugins you need
> (at minimum `fractal-core`; `fractal-tools` for general dev helpers, `fractal-planning` for
> Architect/Strategist work, `fractal-wiki` if this repo has a `wiki/` substrate,
> `fractal-runner` for the scheduled runner, `fractal-pr-review` for the PR-review helpers)?"

If no or unsure, walk them through it:

```
/plugin marketplace add .
/plugin install fractal-core
/plugin install fractal-tools
/plugin install fractal-planning
/plugin install fractal-wiki
/plugin install fractal-runner
/plugin install fractal-pr-review
```

Run `/plugin marketplace add .` from this repo's root in Claude Code (the marketplace manifest
lives at `.claude-plugin/marketplace.json` — see `README.md` for the full install walkthrough
and `SETUP-CLAUDE-CODE.md` for the from-scratch manual path). Install only the plugins the
contributor's role needs; `fractal-core` is required for everyone running FRACTAL workstreams.

After they confirm, re-run Step 1's manifest checks to sanity-check the repo side, then move
to Step 3.

### 3. Run the deterministic gates

```bash
bash tools/validate-plugins.sh
bash tools/router-smoke.sh
```

- `validate-plugins.sh` checks the marketplace manifest, every `plugin.json`, and every
  `SKILL.md` frontmatter (name matches directory, no forbidden keys).
- `router-smoke.sh` exercises `ROUTING_LOGIC/router.py` end-to-end against the bundled
  `fixtures/taskflow/` blueprints in a throwaway temp directory — it never touches this repo's
  own `.claude/fractal/.state.json`.

Report each script's pass/fail verbatim. Do not claim a gate passed unless its exit code was 0
in this session.

**Both green → Phase D, fully set up.** One or both failing → stay in Phase C and report the
failing step's output to the user; do not guess a fix, quote the script's own error text.

### 4. Report summary

Finish with a one-screen summary:

```
Phase detected:     [A | B | C | D]
Prerequisites:      [python3: ok/missing, pyyaml: ok/missing]
Plugins installed:  [confirmed | not confirmed]
validate-plugins:   [PASS | FAIL | not run]
router-smoke:       [PASS | FAIL | not run]
Suggested action:   [the single next thing to do]
```

Do not claim a step is complete unless the user confirmed it or a check passed. Silence on a
step = not done.

## Notes for Maintainers

- Re-verify the plugin list in Step 2 against `.claude-plugin/marketplace.json` — if a plugin
  is added, removed, or renamed there, update this skill's install list to match.
- If a role isn't covered by any of the six plugins, say so explicitly rather than filling
  with filler steps.
- Skill output should be terse and actionable — defer to `README.md` and
  `SETUP-CLAUDE-CODE.md` for rationale.
