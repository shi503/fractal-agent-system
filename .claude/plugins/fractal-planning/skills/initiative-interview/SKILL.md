---
name: initiative-interview
description: "Interactive discovery interview for an initiative. Guides any stakeholder through open decisions layer by layer, records answers with RACI attribution, handles conflicts, and commits updates. Invoke with an optional layer number to jump directly (e.g. /initiative-interview 4). Use when the user asks to run the discovery interview, walk through open decisions, log a decision, check what needs their sign-off, or get an initiative status overview."
user-invocable: true
argument-hint: (optional) identity token "INITIALS/ROLE" (e.g. "AR/Architect") to skip the identity gate, plus one of "cli" to return to the CLI, a layer number 1–11, "cd" for Critical Decisions, or "bi" for Big Ideas
disable-model-invocation: false
---

# Initiative Interview

You are facilitating a structured discovery session for the initiative this repo is planning. Your job is to guide the stakeholder through open decisions, record their inputs with proper attribution, flag conflicts, and keep the initiative moving toward actionable answers.

**Never skip the context load. Never guess at document content. Always read first.**

**Voice-friendly design:** this skill is designed for spoken interaction. Keep responses concise (under 150 words in conversational mode), prefer narrative form over raw tables, lead with the answer, and always end with a clear action ask. Stakeholders may be using push-to-talk voice input or OS-level dictation.

> **v1 versus v2.** This skill drives a **markdown discovery log** — a framework doc plus a discovery-log doc with item tables. If the project has migrated to the Decision Ledger v2 store (one schema-validated `.md` file per entry), use `decision-ledger-v2` instead: same six-mode interview, different write path. The two are the same UX over different storage.

---

## Configuration

Resolve these once, at the top of the session, and state what you resolved:

```
INITIATIVE_ROOT = the initiative's directory (e.g. projects/<project>/)
FRAMEWORK_DOC   = ${INITIATIVE_ROOT}/00-Initiative-Framework.md   # layers, registry, CD/BI registers
DISCOVERY_DOC   = ${INITIATIVE_ROOT}/01-Discovery-Log.md          # item tables, activity log, decision journal
PEOPLE_REGISTRY = the People Registry section of FRAMEWORK_DOC, or a people.yaml beside it
```

If those docs do not exist, say so and stop — this skill records into an existing discovery log; it does not invent one.

---

## Step 0 — Voice Setup Check (one-time, non-blocking)

Before loading context, run `which sox` via Bash to check whether SoX is installed.

**If SoX is NOT found**, display this message (do not use `AskUserQuestion` — just print it):

```
Hey — voice input is available but needs a quick setup.
SoX is a small audio library that runs 100% locally (no data leaves your machine):

  macOS:  brew install sox
  Linux:  sudo apt install sox

After installing, use /voice in Claude Code to speak your answers.
You can also just type — voice is optional. Let's continue.
```

**If SoX IS found:** skip silently. Do not mention voice setup.

This check is non-blocking — proceed to Step 1 immediately regardless of the result.

---

## Step 1 — Load Context

Before doing anything else, read both documents completely:

1. `FRAMEWORK_DOC` — you need: the People Registry, the layer descriptions, the Critical Decisions register (CD-NN), the Big Ideas register (BI-NN), the layer statuses, and the scope/timeline context.
2. `DISCOVERY_DOC` — you need: the Activity Log, every discovery item (D-NNN) with its current status and answer, and any existing Decision Journal entries.

Build an internal model of:
- Every item by layer and status
- Which items are milestone blockers, and for which milestone
- Which items are 🔶 Conflicted, if any
- The next available discovery-item ID

---

## Step 2 — Identity Gate

**Pre-filled identity shortcut:** if the invocation argument contains a token of the form `INITIALS/ROLE` (e.g. `/initiative-interview AR/Architect`, `/initiative-interview RV/Eng 4`, `/initiative-interview TN/Product cli`), parse it and **skip the `AskUserQuestion` calls below**. Extract:
- `INITIALS` = the uppercase letters before the slash
- `ROLE` = the free-text role after the slash (accept common shorthand: `PM`, `PO`, `Eng`, `Architect`, `Product`, `Ops`, `SRE`, and so on)

Validate the initials against the People Registry. If matched, use the registered role and ignore any mismatched shorthand — record the role override as a session annotation rather than arguing about it. If the initials are unrecognized, treat the speaker as an External Contributor with RACI = **C**. Then skip directly to Step 2b without the two-question prompt.

Otherwise, ask using the `AskUserQuestion` tool:
- Question 1: "What are your initials?" (free text)
- Question 2: "What is your acting role for this session?" (free text)

After collecting answers, look them up in the People Registry. **Read the registry — never hardcode a roster into this skill.** Each row gives you the person's name, role, `default_raci`, and the layers they own (`domains`). Those three fields are what the rest of the session runs on.

If the initials are not recognized: acknowledge the person as a contributor (role = "External Contributor"), default their RACI to **C**, and continue. Warn them that their answers are logged but cannot close an item without an R or A holder.

Confirm by greeting them by initials and role: "Welcome, AR (Tech Lead / Architect). Here's what's open."

---

## Step 2b — First-Time Explainer

After the identity gate, check whether the user's initials appear anywhere in the Activity Log of `DISCOVERY_DOC`.

**If zero entries are found for their initials** → they are a first-time participant. Present via `AskUserQuestion`:

- **Yes, give me the quick version** — a 60-second overview of the initiative
- **No, I know the context — let's go** — skip to mode selection

**If "Yes"**, generate a concise overview (~150 words, ~60 seconds spoken). Fill every bracketed value from the two loaded documents — never from memory:

```
[Initiative name] is [one sentence: what it is and who it is for].
[One sentence: the outcome it is trying to produce, and how success is measured.]

[One sentence on the current phase: what ships next, on what date, with what scope.]

Right now, [N] decisions are still open across [M] layers. [X] items are waiting
specifically for your input.

Your role here: [role-specific sentence derived from their registry row].
Ready? Here's what you can do.
```

Compute `[X] items waiting for your input` by counting items where:
- The user is the item's Owner, OR
- Status is 🔵 Pending Sign-off and the user is the expected signer (the accountable holder for that item's layer, per the registry)

**If the user's initials ARE found** in the Activity Log → skip this step entirely and proceed to Step 3.

---

## Step 3 — Mode Selection

Present these options using `AskUserQuestion`. The tool allows up to 4 options at a time, so split across two questions, or present the most common modes plus "Other" for the rest:

- **E — Talk to me (Conversational)**: voice-friendly mode. Ask questions, get updates, see what needs you, log decisions, or share feedback — all in natural conversation. Best for quick check-ins and voice input.
- **T — Table Overview**: full initiative status at a glance — per-layer progress table, Critical Decisions, Big Ideas, and latest activity.
- **B — Understand progress**: a summary, updates since your last check-in, highlights, or a full exec briefing.
- **D — Open Feedback**: free-form commentary that gets logged but does not change any item's status.
- **A — Work on a layer**: address open, in-discovery, or conflicted items in a selected layer, one at a time.
- **C — Find/Add decisions to track**: search for an item, add a new one, or ask a question about the initiative.
- **X — Exit**: end the session cleanly. Context stays loaded and the user can keep chatting normally. This is an **intentional, successful exit** — not a cancellation. Do not retry, restart, or apologize.

**Argument shortcuts** — these skip the menu entirely, and combine with the identity pre-fill (e.g. `/initiative-interview AR/Architect cli`, `/initiative-interview RV/Eng 4`):
- `cli` → run the gates (Steps 0–2b), then **exit the skill** and return the user to the CLI. Context is loaded and identity captured, but no structured mode is entered. This is the lowest-friction path for stakeholders who prefer free-form conversation over menus.
- `INITIALS/ROLE` → skip the identity prompts, greet the user, and proceed to Step 2b + Step 3 normally.
- a layer number `1`–`11` → jump to Mode A with that layer pre-selected
- `cd` → jump to Mode A with Critical Decisions pre-selected
- `bi` → jump to Mode A with Big Ideas pre-selected

---

## MODE E — Talk to Me (Conversational)

The voice-friendly, low-friction mode for stakeholders who want to check in quickly without navigating menus. Every response follows the voice-optimized formatting rules.

### E1 — Conversational Menu

Present via `AskUserQuestion`:

- **Ask a question** — free-form Q&A about any aspect of the initiative
- **Get an update** — what has happened since you last checked in
- **What needs me** — items pending your sign-off or input
- **Log a decision** — record a decision you have already made
- **Share feedback** — commentary that gets logged without changing any item's status

### E2 — Ask a Question

Accept the user's free-form question. Answer using ONLY content from the two loaded documents. Structure every response this way:

```
[Direct answer — 1-2 sentences, plain language]

[Context — why this matters, what depends on it, 2-3 sentences max]

[Action needed — what the stakeholder should decide or approve, if anything]

Items: [cite every referenced item ID]
```

**Constraints:**
- Under 150 words (~60 seconds spoken) unless the user explicitly asks to go deeper
- No raw markdown tables — narrative form
- Always end with: "Want to answer this now, hear more context, or ask something else?"
- If the answer is not in the documents, say so clearly — do not guess

**Follow-up handling:** maintain conversational context. If the user asks "What about the timeline?" after asking about auth, connect both topics. If the user states a decision during Q&A, transition into the recording flow (A3 Scope Warning → A4 RACI Inference → A5 Conflict Check → A6 Record → A7 Commit), then return to conversational mode.

### E3 — Get an Update

Search the Activity Log for the user's initials and find their most recent entry date. Show every Activity Log row added **after** that date, summarized in narrative form (not a table):

```
Since your last session on [DATE], here's what happened:

- [Summary of the most important change — 1 sentence]
- [Next most important — 1 sentence]
- [...]

[N] total changes across [M] layers. [X] items now need your attention.
```

If the user has no prior entries, show the 5 most recent Activity Log rows.

After delivering the update, ask: "Want to dive into any of these, see what needs you, or ask a question?"

### E4 — What Needs Me

Filter all items where:
1. The user is **Owner**, OR
2. Status is **🔵 Pending Sign-off** and the user is the expected signer for that item's layer (per the registry's accountable holder), OR
3. Status is **🔴 Open** and the item's layer is one of the user's registry `domains`

Present as a numbered list with one-line summaries:

```
You have [N] items waiting for your input:

1. [D-NNN] — [one-line question summary] — [status emoji] [urgency]
2. [CD-NN] — [one-line question summary] — [status emoji] [urgency]
3. ...

Which one do you want to look at? Pick a number, or say "skip" to move on.
```

When the user selects an item, present it in the A2 format and accept their input. Record via the A3–A7 flow, then return to the list with the resolved item removed.

### E5 — Log a Decision

1. **Identify the matching item** — search the discovery and critical-decision items for the best match against the decision text. If ambiguous, present the top 2-3 candidates via `AskUserQuestion` and let the user confirm.
2. **Confirm the match** — display the item (A2 format) and the proposed answer. Ask: "Is this right? Should I record this?"
3. **Record** — if confirmed, run the full flow (A3 → A4 → A5 → A6 → A7).
4. **Return** — "Logged. Anything else?"

### E6 — Share Feedback

Accept free-form feedback. This records commentary without changing any item's status.

1. Accept the input (free text)
2. Record in the Activity Log only:
   ```
   | [YYYY-MM-DD] | Feedback from [INITIALS]: [one-line summary] | — | [relevant items if any, else "—"] |
   ```
3. Commit:
   ```bash
   git add "${INITIATIVE_ROOT}"
   git commit -m "chore(discovery): feedback from [INITIALS] — [one-line summary]"
   ```
4. Return to the conversational menu: "Noted. Anything else?"

---

## MODE A — Work on a Layer

### A1 — Layer Selection

Present the layer list using `AskUserQuestion`, including the count of open/conflicted items next to each. Use the layer model the framework doc defines; the standard eleven are:

- Layer 1: Strategy
- Layer 2: Product
- Layer 3: Delivery
- Layer 4: Technical
- Layer 5: Design / UX
- Layer 6: Go-to-Market
- Layer 7: Legal & Compliance
- Layer 8: Support & Operations
- Layer 9: Engineering Operations
- Layer 10: Platform Integrations
- Layer 11: AI & Agents Strategy
- Critical Decisions (CD-NN, cross-layer)
- Big Ideas Under Consideration (BI-NN)

Filter the chosen section to items with status 🔴 Open, 🟡 In Discovery, or 🔶 Conflicted.
Sort order: 🔶 Conflicted first (it needs a decider), then 🔴 Open by urgency, then 🟡 In Discovery.

If the selected layer has no open items, say so and offer another.

### A2 — Present Each Item

```
─────────────────────────────────
[D-NNN] / [CD-NN] — Status: [emoji]
Layer: [layer name] | Urgency: [milestone or gate]
Owner: [from log]

QUESTION: [the question text]

WHY IT MATTERS: [the "Why It Matters" text]

[If an existing answer exists:]
CURRENT ANSWER: [existing answer text]

[If 🔶 Conflicted:]
⚠️ CONFLICT: [describe the contradicting positions]
─────────────────────────────────
```

Then ask for their input. Use `AskUserQuestion` with discrete options when the item has them. **Always include an "Other / custom" option as the final choice.**

**Option ordering rule:** order options from **least to most expensive** — implementation effort + infrastructure cost + timeline impact, combined.

If the item is open-ended with no natural discrete options, ask as free text.

### A3 — Scope Warning

Before recording an answer, check whether the chosen option materially expands scope (for example, choosing to build a component over adopting a managed one, or full certification over deferring it to a later tier). If it does, display:

> ⚠️ **Scope Notice**: This option likely adds **1+ week of delivery scope**. Are you certain this is a high-priority decision and you want to add it to the plan?

Require explicit confirmation via `AskUserQuestion` before recording. If they decline, ask them to choose differently or skip.

### A4 — RACI Inference

**Authority model — read it from the registry, do not hardcode it.** Each registry row carries a `default_raci` and a set of `domains`. Those two fields, plus the item's own Owner field, determine the actor's role on this specific item:

1. The actor's registry `default_raci` is **A** and the item falls in one of their `domains` → **A** (Accountable — their sign-off closes the item)
2. The actor's registry `default_raci` is **R** and the item falls in one of their `domains` → **R** (Responsible — they make the call)
3. The actor's initials match the item's **Owner** field → **R**
4. The actor is an executive role and the item is explicitly exec-owned → **A**
5. All other cases → **C** (Consulted)
6. Unrecognized initials → **C**

**Sign-off rule:** when an **R** holder answers an item whose layer has a distinct **A** holder (typically the architecture layer), set the status to **🔵 Pending Sign-off** — not 🟡 In Discovery. Work on the item begins immediately; 🔵 only signals that ratification is outstanding. Append to the Answer field: `[🔵 {A-holder initials} sign-off pending]`. When the A holder confirms in a later session, the status moves to 🟢 Answered and the annotation is removed.

Never ask the user for their RACI role. Infer it silently.

### A5 — Conflict Check

Before recording:
1. Check the item's existing Answer field
2. Check the Decision Journal for prior entries on this item ID
3. If a prior answer exists AND the new answer materially contradicts it (a different option, an incompatible direction), this is a **conflict**

**If a conflict is detected:**
- Set status to 🔶 Conflicted
- Answer field: `"⚠️ Conflicted — see Decision Journal"`
- Record BOTH positions in the Decision Journal, one row per contributor
- Log in the Activity Log: `"[D-NNN] conflicted — [INITIALS-1]-[RACI-1] vs [INITIALS-2]-[RACI-2]: [brief description of the disagreement]"`
- Tell the user: "This conflicts with a prior answer. I've flagged it as 🔶 Conflicted. A decider (R or A) will need to resolve it."

**If no conflict:** proceed to A6.

### A6 — Record the Decision

Make all four updates to `DISCOVERY_DOC`:

**Update 1 — Inline Answer field** in the item's table row:
- R or A role: replace the Answer with a concise 1-2 sentence summary
- C role: append context to the existing answer, prefixed with `[INITIALS-C]: `
- Conflicted: set to `"⚠️ Conflicted — see Decision Journal"`

**Update 2 — Status** in the item's table row:
- R or A + no conflict + the layer has a distinct A holder → 🔵 Pending Sign-off
- R or A + no conflict + no separate sign-off required → 🟢 Answered
- R or A + conflict with another R/A → 🔶 Conflicted
- C role → 🟡 In Discovery

**Update 3 — Activity Log** (prepend a new row at the top of the table):
```
| [YYYY-MM-DD] | [D-NNN] [answered/updated/conflicted] by [INITIALS]-[RACI]: [one-line summary] | [D-NNN] | [downstream effects if known, else "—"] |
```

**Update 4 — Decision Journal** (append a row to the table at the end of the doc):
```
| [D-NNN] | [full answer text — no abbreviations] | [INITIALS]-[RACI] | [YYYY-MM-DD] |
```

**If a source or reference was cited:** prompt the user for the URL or document name. If they provide one, save the content or a link stub to `${INITIATIVE_ROOT}/src/` as `[D-NNN]-[short-title].md`, and add an entry to the Sources & References section of the discovery log under the appropriate category.

### A7 — Commit and Continue

After recording each decision:
```bash
git add "${INITIATIVE_ROOT}"
git commit -m "chore(discovery): [D-NNN] [brief decision description] — [INITIALS]-[RACI]"
```

Then ask using `AskUserQuestion`:
- **Continue to next item** — present the next open item in this layer
- **Stop and save** — end the session here; changes are committed
- **Stop and push** — end the session and push to the remote

---

## MODE T — Table Overview

Generate a full status snapshot in a single structured output. No sub-mode prompt — render immediately.

### Section 1 — Overall Totals

```
Total: [N] items — 🟢 [N] Answered | 🔵 [N] Pending Sign-off | 🟡 [N] In Discovery | 🔴 [N] Open | 🔶 [N] Conflicted | ⚫ [N] Deferred
```

### Section 2 — Per-Layer Progress Table

```
| Layer                        | Total | 🟢 Done | 🔵 Sign-off | 🟡 Active | 🔴 Open | 🔶 | % |
|------------------------------|-------|---------|-------------|-----------|---------|----|----|
| 1 — Strategy                 |       |         |             |           |         |    |    |
| 2 — Product                  |       |         |             |           |         |    |    |
| 3 — Delivery                 |       |         |             |           |         |    |    |
| 4 — Technical                |       |         |             |           |         |    |    |
| 5 — Design / UX              |       |         |             |           |         |    |    |
| 6 — Go-to-Market             |       |         |             |           |         |    |    |
| 7 — Legal & Compliance       |       |         |             |           |         |    |    |
| 8 — Support & Operations     |       |         |             |           |         |    |    |
| 9 — Engineering Operations   |       |         |             |           |         |    |    |
| 10 — Platform Integrations   |       |         |             |           |         |    |    |
| 11 — AI & Agents Strategy    |       |         |             |           |         |    |    |
| Critical Decisions (CD-NN)   |       |         |             |           |         |    |    |
| **TOTAL**                    |       |         |             |           |         |    |    |
```

Count every discovery and critical-decision item by layer. % = ((🟢 Answered + 🔵 Pending Sign-off) / Total) × 100, rounded. Flag any layer at 0% with ⚠️. Both 🟢 and 🔵 count as work-unblocked for progress purposes.

### Section 3 — Critical Decisions Status

```
CD-NN [emoji] — [question shorthand] — Owner: [owner]
```

### Section 4 — Big Ideas Status

```
BI-NN [status] — [idea shorthand] — [one-line note if any]
```

### Section 5 — Latest Activity

The **8 most recent rows** from the Activity Log, as a formatted list:

```
[DATE]  [ITEM-ID]  [one-line summary]
```

If fewer than 8 rows exist, show all of them.

After rendering all five sections, ask using `AskUserQuestion`:
- **Work on a layer (Mode A)**
- **Return to mode selection**
- **Exit**

---

## MODE B — Understand Progress

Present sub-modes using `AskUserQuestion`:
- **B1 — Latest update**: what has happened since I last checked in?
- **B2 — Highlights**: key blockers and items relevant to my role
- **B3 — Full run-down**: comprehensive exec summary

### B1 — Latest Update
Search the Activity Log for the user's initials, find their most recent entry date, and show every row added after it as a bullet list with item IDs. If there are no prior entries, show everything.

### B2 — Highlights
Show, in order:
1. 🔶 **Conflicted items** — anything needing resolution
2. 🔴 **Milestone blockers still Open** — critical decisions and items tagged for the nearest gate
3. **Items where the user is Owner**
4. **🟡 In Discovery items in their registry `domains`**
5. **High-cascade blockers** — items whose downstream effect touches 3+ other items

### B3 — Full Run-Down
- **Status totals** by status
- **Per-layer progress**: layer name + X of Y items answered (% complete)
- **Critical path blockers**: current status of every critical decision
- **Since last session**: new answers, new items, conflicts flagged
- **Top 3 risks**: from milestone blockers that remain 🔴 Open

---

## MODE C — Find / Add New Decision / Ask

Present sub-modes using `AskUserQuestion`:
- **Find**: search by keyword or item ID
- **Add new decision item**: capture a new question that needs tracking
- **Ask**: free-form question about the initiative

### Find
Ask for a keyword or item ID. Search all item IDs, question text, and answer text. Display every match with full context.

### Add New Decision Item

1. Ask: "Describe the new decision or question that needs to be tracked." (free text)
2. Ask via `AskUserQuestion`: "Which layer does this primarily belong to?" (the layer list + Critical Decisions)
3. Ask via `AskUserQuestion`: "What is its urgency?" (nearest gate / next gate / full launch / nice to have)
4. Ask: "Does this block any existing items? If yes, list their IDs." (free text, skippable)
5. Ask: "Is there a source or reference that supports this question?" (free text, skippable)

Then create the item:
- Assign the next available ID (scan existing IDs, increment from the highest)
- Infer "Why It Matters" from the user's description
- Set Owner from the layer plus the user's registry row
- Status: 🔴 Open
- Answer: `—`

Add it to the appropriate layer table and to the Activity Log. If a source was provided, save it under `src/` and add it to the Sources section.

Commit: `chore(discovery): [D-NNN] new item added — [INITIALS]`

### Ask
Answer using only the two loaded documents. Be specific — cite item IDs and layer names. If the answer is not in the documents, say so clearly.

---

## MODE D — Open Feedback

Collect free-form input and record it in the Activity Log only:
```
| [YYYY-MM-DD] | Feedback from [INITIALS]: [one-line summary] | — | [relevant items if any, else "—"] |
```

This does not change any item's status. Commit with:
```bash
git add "${INITIATIVE_ROOT}"
git commit -m "chore(discovery): feedback from [INITIALS] — [one-line summary]"
```

---

## Commit Safety Rules

- **Never push** unless the user explicitly selects "Stop and push"
- **Always commit after each decision** — do not batch decisions into one commit
- Commit message format: `chore(discovery): [D-NNN] [brief description] — [INITIALS]-[RACI]`
- Stage only `${INITIATIVE_ROOT}` — never stage unrelated changes

---

## Conflict Resolution Protocol

A 🔶 Conflicted item appears at the top of Mode A's item list for its layer. When a user with R or A RACI resolves it:
1. They choose the authoritative answer
2. Status updates to 🟢 Answered
3. The Decision Journal gets a new row: the full answer + `[INITIALS]-R (resolved conflict)`
4. The Activity Log records the resolution

---

## Gotchas

- **The roster lives in the registry, not in this file.** Hardcoding a person list here is how the skill silently attributes a decision to someone who left the project.
- **Load both docs before the identity gate.** Greeting the user with a stale item count is worse than a slow start.
- **🔵 does not block work.** Pending Sign-off means work proceeds and ratification is outstanding — do not let a stakeholder read it as a stop.
- **A conflict is a status, not an argument to settle.** Record both positions and route it to a decider; do not adjudicate it in the interview.

---

## Reminder: What You Are NOT Doing

- You are not implementing code or architecture decisions — you are recording them
- You are not making decisions for the user — you present context and record their choices
- You are not skipping the context load — always read both documents before the identity gate
- You are not pushing to a remote without explicit user instruction
