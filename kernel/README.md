# FRACTAL kernel

Portable **spec / installer contract**. Not a Claude Code plugin rewrite.

The kernel is the shared BLUEPRINT, PRD, evidence, and graph law. Each runtime (installer) copies those artifacts, then applies its own scheduler. Claude Code is the **default / primary** installer. Grok Bot and Cursor are adapters.

Existing Claude first-run in the [root README](../README.md) is unchanged. Full Claude setup: [SETUP-CLAUDE-CODE.md](../SETUP-CLAUDE-CODE.md). Do not duplicate that guide here.

---

## Kernel vs installer

| | Kernel (this directory) | Installer (Claude / Grok Bot / Cursor) |
|---|---|---|
| Owns | BLUEPRINT fields, PRD sections, evidence sections, graph law, JSON Schemas, harness-neutral templates | Where files live on disk, how work is scheduled, model routing, plugins, PRs, CI YAML |
| Source of workstream readiness | Every `depends_on` id has **accepted evidence** | How “accepted” is recorded (Claude: router state; Grok Bot: PR/CI; Cursor: files + GitHub hooks) |
| Must not own | `model: opus\|sonnet\|haiku`, `.claude/` paths, `router.py`, plugin marketplace, slash commands, PULSE.md as required protocol, Grok Bot teammates, Cloud Agent, GitHub Actions YAML, stored PRD Status | Kernel templates and schemas (consume them; do not fork a second contract) |

**KERNEL MUST include**

- **BLUEPRINT:** `name`, `title`, `date`, `status`, `revised`, `trigger`, `context` (`source_documents`, `locked_decisions`, `pending`), `workstreams[]` (`id`, `name`, `prd`, `description`, `depends_on`, `acceptance`), plus `parallel` and `notes` (execution order only).
- **PRD:** feature overview, acceptance criteria, read / write / create file manifest, CI gate, out of scope, blockers.
- **Evidence:** work completed, work not completed, technical debt, key decisions / deviations, Layer 1 command table with **pasted output** (not self-assessment).
- **Graph law:** `depends_on` is workstream **ids**. A workstream is ready only when every dependency’s evidence is accepted.

**KERNEL MUST NOT include**

- `model: opus|sonnet|haiku` (Claude installer extension)
- `.claude/` paths in schemas or kernel templates (use `workstreams/{kebab}/prd-{kebab}.md`)
- `router.py`, plugin marketplace, slash commands, or PULSE.md as required protocol
- Grok Bot account-level agents, Cloud Agent, or GitHub Actions YAML as required kernel files
- Stored PRD Status as source of truth (Claude may keep router state; Grok Bot derives status from PRs/CI)

---

## Graph law

1. `depends_on` lists workstream `id` values only — not Feature Lead names, phase titles, or PR numbers.
2. Empty `depends_on` means ready when the epic is active.
3. A workstream is **ready** only after every dependency has evidence with `accepted: true` (markdown: **Accepted:** yes).
4. `parallel` and `notes` document execution order. They do not replace `depends_on` and they do not unlock work.
5. PRD Status is not a readiness signal.

---

## Installer matrix

For each runtime: **(a)** what you copy from `kernel/`, **(b)** what you must **not** copy, **(c)** native scheduler.

### 1. Claude Code — DEFAULT

Primary installer. First-run in the [root README](../README.md) stays valid. Details: [SETUP-CLAUDE-CODE.md](../SETUP-CLAUDE-CODE.md).

**(a) Copy from `kernel/`**

| Kernel path | Lands in the consuming project |
|---|---|
| `templates/BLUEPRINT.yaml` | `.claude/fractal/BLUEPRINT-{Epic}.yaml` (or keep an existing project BLUEPRINT) |
| `templates/prd.md` | `.claude/fractal/workstreams/{kebab}/prd-{kebab}.md` (Claude may keep flat `workstreams/{kebab}.md` if that is already the project layout) |
| `templates/evidence.md` | `.claude/fractal/workstreams/{kebab}/HANDOFF.md` or `evidence.md` — same sections; Claude’s handoff skill already matches this shape |
| `schemas/*.json` | Optional, next to the fractal root, if you want local validation |

You may **keep using the existing project layout** (`example-claude` copied to `.claude/`). Copying kernel templates is not required to run first-run.

**(b) Do not copy**

| Do not copy | Why |
|---|---|
| Kernel files over `example-claude/agents/*` or `.claude/agents/*` | Agents stay Claude installer plugins |
| Kernel files over `ROUTING_LOGIC/router.py` or `.claude/fractal/router.py` | Scheduler stays `router.py` |
| Kernel README as a replacement for root first-run | First-run remains the root README + SETUP-CLAUDE-CODE.md |
| Grok Bot / Cursor rows below into `.claude/` | Those are other installers |

Claude **may** keep installer extensions the kernel forbids: `model:` on workstreams, `feature_lead` names, phase-list BLUEPRINTs, `.state.json`, slash commands, PULSE.md. Those are Claude-only. Do not put them back into `kernel/`.

**(c) Native scheduler**

**fractal-core plugins + `router.py`.** Architect writes BLUEPRINT + PRDs; `python3 .claude/fractal/router.py init\|next\|update\|status` is the ready-queue; Feature Lead sessions execute one workstream; handoff writes evidence; Architect accepts evidence before dependents start. Plugin marketplace and slash commands (`/fractal-init`, `/handoff`, `/pulse`) are Claude installer, not kernel.

---

### 2. Grok Bot

Same kernel artifacts. Different scheduler. No four-persona sidebar.

**(a) Copy from `kernel/`**

| Kernel path | Lands in the consuming project |
|---|---|
| `templates/BLUEPRINT.yaml` | `BLUEPRINT-{Epic}.yaml` at a harness-neutral project root (for example `fractal/`) |
| `templates/prd.md` | `workstreams/{kebab}/prd-{kebab}.md` |
| `templates/evidence.md` | `workstreams/{kebab}/evidence.md` (on the workstream PR) |
| `schemas/*.json` | Optional, for CI validation of the BLUEPRINT |

**(b) Do not copy**

| Do not copy | Why |
|---|---|
| `.claude/` plugins, `example-claude/`, or `router.py` as required files | Not this installer |
| `kernel/` agent markdown (there is none) into Grok Bot teammates | Do **not** create four Grok Bot teammates that clone `architect.md` / `feature-lead.md` / `sub-agent.md` |
| PULSE.md, slash commands, plugin marketplace | Claude installer protocol |
| GitHub Actions YAML from this repo as a required kernel file | Actions are the Grok scheduler, authored in the consuming repo later |

The durable **Architect** is an **account-level** Grok Bot agent. Feature Lead execution is a **Cloud Agent PR**, not a sidebar persona.

**(c) Native scheduler**

**GitHub.** One PR per workstream. GitHub Actions are Layer 1 (lint / build / typecheck / test). Merge and CI events record evidence acceptance. Ready queue = workstreams whose `depends_on` evidence is accepted on merged PRs. Status is derived from PRs/CI — do not store PRD Status as source of truth.

---

### 3. Cursor

Same kernel templates as Grok Bot. **`SETUP-CURSOR.md` is stale — do not follow it.**

**(a) Copy from `kernel/`**

| Kernel path | Lands in the consuming project |
|---|---|
| `templates/BLUEPRINT.yaml` | Harness-neutral `BLUEPRINT-{Epic}.yaml` (for example `fractal/` or project root) |
| `templates/prd.md` | `workstreams/{kebab}/prd-{kebab}.md` |
| `templates/evidence.md` | `workstreams/{kebab}/evidence.md` |
| `schemas/*.json` | Optional, for local or CI validation |

Cursor adapter = **consume kernel templates**.

**(b) Do not copy**

| Do not copy | Why |
|---|---|
| `.claude/agents/*.md` or `example-claude/agents/*.md` into `.cursor/rules/*.mdc` | Stale SETUP-CURSOR.md path. Rules are not a kernel install. |
| Agent markdown rewritten as `.mdc` “personas” | Not the Cursor adapter |
| `SETUP-CURSOR.md` steps (copy router into `.fractal/`, copy skills into `.cursor/skills/`) | That guide is stale and is not the Cursor path |
| Claude `model:` fields or `.claude/` paths into kernel files | Kernel contract |

**(c) Native scheduler**

**Files + GitHub hooks** — same level of description as Grok Bot. BLUEPRINT and PRDs are committed files. One PR per workstream. Actions (or the host repo’s existing CI) are Layer 1. Merge/CI accept evidence. `depends_on` + accepted evidence is the ready queue. Cursor Cloud Agent / Task may **execute** a ready workstream; it is not a replacement graph, and it is not “paste architect.md into a rule.”

---

## Layout

```
kernel/
├── README.md                 # This matrix
├── validate.py               # Example BLUEPRINT + graph-law check
├── schemas/
│   ├── blueprint.schema.json
│   └── evidence.schema.json
├── templates/
│   ├── BLUEPRINT.yaml
│   ├── prd.md
│   └── evidence.md
└── examples/
    └── nova-p1-notification-core/
        ├── BLUEPRINT-NOVA-P1-NotificationCore.yaml
        └── workstreams/{kebab}/prd-{kebab}.md
```

---

## Validation

No new router. From repo root:

```bash
python3 -m pip install pyyaml jsonschema
python3 kernel/validate.py
```

CI: `.github/workflows/kernel.yml`.

---

## Example

[`examples/nova-p1-notification-core/`](examples/nova-p1-notification-core/) is a worked Notification Core epic for TaskFlow. The named fixture `fixtures/taskflow/blueprints/BLUEPRINT-NOVA-P1-NotificationCore.yaml` was **not** on `main`; this example is reconstructed from in-repo notification intent (unread count, nav badge, per-category toggles) and uses kernel paths only.
