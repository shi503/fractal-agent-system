paths: [".claude/plugins/**", ".claude-plugin/**"]
---

# Plugin Authoring Protocol

Shared tooling in this repo ships as Claude Code plugins under `.claude/plugins/`, discovered
through the repo-root marketplace manifest. `tools/validate-plugins.sh` is the deterministic
gate — this rule and that script must never disagree; if you change one, check the other.

## Plugin directory layout (canonical format)

```
.claude/plugins/
└── <plugin-name>/
    ├── .claude-plugin/
    │   └── plugin.json           # name, version, description, author — REQUIRED location
    ├── README.md
    ├── agents/                   # agent definitions (fractal-core only)
    └── skills/
        └── <skill-name>/
            ├── SKILL.md          # frontmatter (description drives triggering) + body
            ├── scripts/          # bash helpers using ${CLAUDE_PLUGIN_ROOT}
            └── references/       # deep-loaded guides (only when the skill is invoked)
```

## Marketplace manifest

`.claude-plugin/marketplace.json` (repo root): top-level `name`, `owner` ({`name`}, `email`
optional), `metadata` ({`description`, `version`}), and `plugins[]`, each entry `{name,
source, description, version}` with `source` starting `./`.

## The six plugins

| Plugin | Install target | Contents |
|---|---|---|
| `fractal-core` | Every repo adopting FRACTAL | `fractal-init`, `fractal-maintenance`, `pulse`, `handoff`, `quality-pass`, `gap-analysis`, `claude-md-audit`, `commit-summarize`; the four tier agents (`architect`, `strategist`, `feature-lead`, `sub-agent`) |
| `fractal-planning` | Repos where an Architect/Strategist authors BLUEPRINTs | `stakeholder-brief`, `initiative-interview`, `initiative-sync`, `meetings-standup-summary`, `grounded-meeting-summary`, `gap-analysis`, `learning-opportunity`, `deck`, `sprint-close`, `weekly-digest`, `decision-ledger-v2` |
| `fractal-tools` | Every repo | `explore`, `review`, `create-issue`, `create-plan`, `document`, `deslop`, `peer-review`, `fractal-setup` |
| `fractal-wiki` | Repos with a `wiki/` substrate | `wiki-ingest`, `wiki-query`, `wiki-lint`, `wiki-add`, `wiki-explore`, `wiki-sync`, `transcript-ingest`, `promote-to-ledger` |
| `fractal-runner` | Repos running the scheduled FRACTAL runner | `fractal-runner` |
| `fractal-pr-review` | Repos with active PR flow | `pr-assist` |

All six are pinned at version `2.0.0` — `tools/validate-plugins.sh` fails any `plugin.json`
whose `version` is not exactly `"2.0.0"`.

## `plugin.json` required fields

`name`, `version`, `description`, `author` (an object; `{"name": "..."}` is sufficient — see
`.claude/plugins/fractal-core/.claude-plugin/plugin.json` for the worked example).

## SKILL.md frontmatter spec

**Triggering is the `description` field alone.** There is no `trigger-phrases` key. Write the
description as **[what it does] + [when to use it]**, ending with the literal phrases a user
would say ("Use when the user asks to X, Y, or Z.").

`model` and `tools` are **not** valid SKILL.md frontmatter keys — `model` belongs on an
*agent*, not a skill, and tool restriction is expressed via `allowed-tools`.
`tools/validate-plugins.sh` check 6 fails a build the moment `trigger-phrases`, `model`, or
`tools` appears in any SKILL.md frontmatter.

```yaml
---
name: <kebab-case>                         # must match the folder name (validator check 5)
description: >                             # THE trigger — prose, not a list
  What the skill does, in one to two sentences. Use when the user asks to
  <phrase 1>, <phrase 2>, or <phrase 3>.
# --- optional fields ---
disable-model-invocation: true             # user-only / side-effecting skill — see below
allowed-tools: "Bash(git diff *) Read Grep" # restrict tool access (string or list form)
argument-hint: "[arg]"                     # shown to the user for slash invocation
user-invocable: true                       # explicit /name invocation is supported
context: fork                              # run in an isolated subagent context
metadata: { author: …, version: 1.0.0 }    # arbitrary k/v — not model/tools
---
```

### `disable-model-invocation: true` — when to set it

Set this on any **side-effecting or user-only** skill so it never self-fires on a passing
mention — the model can still run it via an explicit `/name` invocation, but won't decide to
on its own. Currently applied to: `commit-summarize`, `fractal-init`, `fractal-maintenance`,
`pulse`, `handoff`, `quality-pass` (`fractal-core`); `deck`, `decision-ledger-v2`,
`initiative-sync`, `learning-opportunity`, `initiative-interview`,
`meetings-standup-summary`, `stakeholder-brief` (`fractal-planning`); `create-issue`,
`create-plan`, `deslop`, `document`, `explore`, `peer-review`, `fractal-setup`, `review`
(`fractal-tools`); `promote-to-ledger`, `transcript-ingest`, `wiki-ingest` (`fractal-wiki`);
`fractal-runner` (`fractal-runner`). Extend this set as new side-effecting skills are added —
this list is a floor, not a ceiling.

### `## Gotchas` section

Add a `## Gotchas` section to every skill with a known footgun — required at minimum on the
side-effecting skills above. This is the highest-signal content in a SKILL.md: exact failure
points, field-name mappings, edge cases. Keep entries concrete — not a restatement of the
skill's own steps. Worked example:
`.claude/plugins/fractal-core/skills/fractal-init/SKILL.md`'s Gotchas section calls out the
`router.py init` foot-gun directly (see `.claude/rules/fractal-protocol.md`).

## `${CLAUDE_PLUGIN_ROOT}` usage

Scripts in `skills/<name>/scripts/` reference resources via `${CLAUDE_PLUGIN_ROOT}` so they
work regardless of install location — e.g. `wiki-query`'s SKILL.md invokes its search wrapper
as `"${CLAUDE_PLUGIN_ROOT}/skills/wiki-query/scripts/qmd-search.sh"`.

## Legacy `.claude/skills/`

Deprecated. `.claude/skills/DEPRECATED.md` is a stub pointer only — no skill content remains
there. The plugin tree under `.claude/plugins/` is the sole authoritative location; install
via the repo-root marketplace, not the flat directory.

<!-- referenced-paths
.claude-plugin/marketplace.json
tools/validate-plugins.sh
.claude/plugins/fractal-core
.claude/plugins/fractal-planning
.claude/plugins/fractal-tools
.claude/plugins/fractal-wiki
.claude/plugins/fractal-runner
.claude/plugins/fractal-pr-review
.claude/plugins/fractal-core/.claude-plugin/plugin.json
.claude/plugins/fractal-core/skills/fractal-init/SKILL.md
.claude/skills/DEPRECATED.md
-->
