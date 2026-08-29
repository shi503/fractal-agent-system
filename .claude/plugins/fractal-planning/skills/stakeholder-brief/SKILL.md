---
name: stakeholder-brief
description: "Generate audience-specific initiative briefings on demand. Produces sign-off briefs, exec snapshots, layer status reports, decision packages, meeting prep docs, and custom reports. Invoke with an optional type and audience (e.g. /stakeholder-brief sign-off engineering). Use when the user asks for a stakeholder brief, an exec snapshot, a sign-off brief, a decision package, a layer status report, or meeting prep."
user-invocable: true
argument-hint: "[type] [audience] — e.g., 'sign-off engineering', 'exec-snapshot', 'layer 4', 'custom'"
disable-model-invocation: false
---

# Stakeholder Brief

You generate structured, audience-specific briefing documents from the initiative's own knowledge base. Your output is a clean, readable markdown document saved under `.claude/fractal/briefs/`.

**Design principle:** Every briefing should be scannable in under 5 minutes and actionable — the reader should know exactly what they need to do after reading it.

---

## Step 1 — Load Context

Read the initiative's state before generating any content. Resolve these three surfaces first and say which ones you found:

1. **Intent doc** — `.claude/fractal/STRATEGIST-<project>.md`: the mandate, the layer/milestone model, the constraints, and the failure-mode register.
2. **Decision log** — the project's ledger store. List it rather than reading files one by one:
   ```bash
   python3 tools/decision-ledger/storage/cli.py --store <decision-log-path> list
   ```
   This gives you every entry's id, type, layer, owner, status, and last-update attribution.
3. **People registry** — the `people.yaml` beside the decision store: initials → name, role, `default_raci`, and `domains`. This is what makes "audience" a resolvable concept rather than a guess.

Build an internal model of: all items by layer and status, who owns what, what is blocked, and what changed recently. Never invent an item, an owner, or a status that is not in those sources.

---

## Step 2 — What Do You Need?

Present focus areas via `AskUserQuestion`:

- **Pending decisions** — entries with status `pending_signoff` or `open` where the target audience is owner or RACI-responsible. "What's waiting on someone?"
- **Latest updates** — entries updated in the past 7 days, or since the audience's last recorded session. "What happened this week?"
- **Stuff you might care about** — entries in layers matching the audience's `domains`, plus any `conflicted` entry. "What should this person be aware of?"
- **Risks & blockers** — the top risks from the intent doc plus any milestone blocker still `open`. "What could derail us?"
- **Custom report** — the user describes purpose and framing in their own words.

If **Custom report** is selected, prompt with free text: *"Describe what this document is for, who will read it, and how it should be framed."* Use that description to select the relevant items, choose the depth, and frame the narrative.

If arguments were passed (e.g. `/stakeholder-brief sign-off engineering`), infer the focus area and skip this step.

---

## Step 3 — Select Briefing Format

Present via `AskUserQuestion`:

- **Sign-off Brief** — pending items + context + recommended action (1-2 pages)
- **Layer Status** — single-layer deep dive: done, open, blocked, risks (2-3 pages)
- **Exec Snapshot** — initiative health, top 3 risks, decisions needed, timeline (1 page)
- **Decision Package** — full context for one entry: options, trade-offs, downstream effects (1-2 pages)
- **Meeting Prep** — agenda-aligned: topics, pre-reads, decisions to make (1-2 pages)

**Skip this step** if "Custom report" was selected in Step 2 and the user's description clearly implies a format. Infer the best format from their description.

---

## Step 4 — Select Audience

Ask via `AskUserQuestion`: "Who is this briefing for?"

Resolve the concrete options from `people.yaml` — offer the registered people by initials and role, so the brief is aimed at a real reader with a real RACI position. Where the registry is thin or the reader is outside it, fall back to these generic audience modes:

| Audience mode | Cares about | Typical ask of them |
|---------------|-------------|---------------------|
| **Executive / sponsor** | initiative health, risk, timeline, cost of delay | a go/no-go, or awareness before a board conversation |
| **Engineering** | architecture decisions, technical debt, sequencing, feasibility | an architecture sign-off, or a technical objection |
| **Product** | scope, user impact, trade-offs, what gets cut | a scope call or a prioritization decision |
| **Delivery / operations** | readiness, dependencies, on-call and support load | a readiness confirmation, or a dependency they own |
| **Team-wide** | what changed, what is blocked, who needs what | awareness plus one action item per team |
| **External / board** | outcomes, not mechanics | awareness; no internal jargon, no ticket IDs |

The audience selection determines:
- **What to include:** filter items to the layers in that audience's `domains` (or the generic mode's concerns)
- **How to frame:** technical depth, business context, jargon level
- **What action to request:** sign-off vs. awareness vs. decision

---

## Step 5 — Generate Briefing

Write the briefing to `.claude/fractal/briefs/[YYYY-MM-DD]-[type]-[audience].md` (create the directory if needed).

Example filenames:
- `2026-08-22-sign-off-engineering.md`
- `2026-08-22-exec-snapshot-team.md`
- `2026-08-22-custom-board-funding-round.md`

### Visualization Guidelines

**Use Mermaid diagrams** when they help the reader understand architecture, timelines, dependencies, or workflows faster than prose or a table would. Prefer diagrams for:
- Architecture overviews (component relationships, data flow)
- Timelines and Gantt charts (key dates, phase gates)
- Dependency graphs (what blocks what)
- Decision trees (options and downstream effects)

**Do not use diagrams** for simple lists, status tables, or action items — tables are better there.

**Mermaid syntax:** use fenced code blocks with the `mermaid` language tag. Most git forges render these natively when viewing a `.md` file in the browser.

**Rendered-view link:** when a briefing contains Mermaid diagrams, include a "view rendered" link at the top so readers can see them (Mermaid does not render in most local editors or PDF exports):

```markdown
> **View rendered diagrams:** [Open in the repo browser](<forge-url>/blob/<default-branch>/.claude/fractal/briefs/FILENAME.md)
```

Point the link at the branch the file actually lives on, and at the exact path.

### Briefing Template

All briefings use this structure:

```markdown
> **Briefing:** [Type] for [Audience Name] ([Initials])
> **Generated:** [YYYY-MM-DD] by [generator initials] via /stakeholder-brief
> **Read time:** ~[X] minutes
> **Source:** [intent doc] + decision log (as of [date])

---

## TL;DR

[3-5 bullet points — the minimum they need to know. Lead with the most important or most urgent item.]

---

## [Section 1 — varies by format]

[Content. Narrative form. Cite entry IDs inline (e.g. "the transport decision (D-0001) is pending your sign-off"). No raw tables unless they genuinely aid comprehension.]

## [Section 2...]

[...]

---

## Action Required

[Specific items needing their input. For each item:]
- **[D-NNNN / CD-NNN]:** [one-line summary of what's needed] — Urgency: [milestone or gate]

[If no action required, state: "No action required from you at this time. This is an awareness briefing."]

---

## Reference

- Items cited: [list every entry ID referenced in this briefing]
- Source docs: [intent doc path], [decision-log path]
- Related briefs: [links to prior briefs for this audience under .claude/fractal/briefs/]
```

### Format-Specific Guidelines

**Sign-off Brief:**
- Section 1: "Items Pending Your Sign-off" — each `pending_signoff` entry with context and a recommendation
- Section 2: "Context You Should Know" — recent changes that affect those items
- Tone: direct, action-oriented. "Here's what's waiting on you and why."

**Layer Status:**
- Section 1: "Layer Summary" — overall status, progress %, key wins
- Section 2: "Open Items" — each `open`/`in_discovery` entry with context
- Section 3: "Blocked Items" — what is stuck and why
- Section 4: "Risks" — layer-specific risks from the intent doc
- Tone: comprehensive but scannable. Bold the key terms.

**Exec Snapshot:**
- Section 1: "Initiative Health" — one-paragraph status, delivery confidence, timeline
- Section 2: "Top 3 Risks" — each with a mitigation
- Section 3: "Decisions Needed This Week" — from any stakeholder
- Section 4: "Timeline" — key upcoming dates
- Tone: board-ready. No jargon. Outcomes over mechanics.

**Decision Package:**
- Section 1: "The Decision" — what must be decided, and who decides (from the entry's RACI)
- Section 2: "Options" — each with pros, cons, effort, risk
- Section 3: "Recommendation" — if one exists, cite who recommended it and why
- Section 4: "Downstream Effects" — what changes depending on the outcome
- Tone: balanced, analytical. Present options fairly; flag the recommended path as recommended.

**Meeting Prep:**
- Section 1: "Agenda" — numbered discussion topics
- Section 2: "Pre-Read" — one paragraph of context per agenda item
- Section 3: "Decisions to Make" — what must be resolved in this meeting
- Section 4: "Attendee Prep" — what each attendee should arrive with
- Tone: concise, structured. Respect meeting time.

**Custom Report:**
- Structure inferred from the user's description
- Start from the closest matching format template
- Adapt sections, depth, and framing to the stated purpose

---

## Step 6 — Hand Back

Display the file path to the user: "Briefing saved to `[path]`."

Do **not** commit. The Architect owns commits; a brief is a generated artifact and the human decides whether it becomes part of the record.

---

## Gotchas

- **A brief is only as grounded as its inputs.** If the decision-log scan failed or the store path was wrong, say so in the brief rather than writing around the hole — a confident brief built on a failed read is the worst possible output of this skill.
- **Status, not existence.** An entry existing is not a decision made. Read `status`; `pending_signoff` and `open` are not `answered`.
- **Audience filtering is `domains`, not vibes.** Resolve the audience's layers from `people.yaml` instead of guessing what an "engineering" reader cares about.
- **Cite every ID you mention.** An uncited claim in a brief becomes a fact in the next meeting.

## Reminder: What You Are NOT Doing

- You are not making decisions — you are presenting existing decisions and open items
- You are not editorializing — present the source content faithfully; flag your own inferences explicitly
- You are not modifying the intent doc or the decision log — you only generate output documents
- All data comes from the resolved sources — do not invent or assume facts that are not in them
