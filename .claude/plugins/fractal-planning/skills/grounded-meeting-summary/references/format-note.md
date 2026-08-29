# Grounded-summary format — annotated skeleton

The canonical worked example is a 27/27 grounded summary of a design session, produced against a
companion code/stack synthesis doc. If your project has one, read it before authoring — this note is
the abstraction of that document. If it does not, the skeleton below plus `rubric.md` is the whole
contract.

```markdown
# Meeting Summary — {date} {topic}

> **Format note:** Adapted from `meetings-standup-summary` for a feature/architecture session
> (disambiguation, codename translation, traffic-light status, sources block). Standup
> Yesterday/Today/Blockers is replaced with a workflow/topic digest + decisions register + ADR
> candidates + action inventory.
>
> **The distinguishing lens is _grounding_.** Where a meeting assumption diverges from — or is
> already handled by — deployed reality, an inline 🔎 Grounding callout cross-references
> `{companion-synthesis}` so readers make weighted decisions rather than re-deriving primitives.

## Header
| | |
|---|---|
| **Date** | {date, time, duration} |
| **Attendees** | {Name (INI) · …} |
| **Non-attendee mentions** | {referenced-not-present, with initials} |
| **Purpose** | {one line} |
| **Tracker epic** | {TICKET-NNN + link} |
| **Design branch** | {branch / merge target} |
| **Companion doc** | {synthesis path — the grounding source for every 🔎} |
| **External artifacts** | {doc site / shared doc / design file links} |

## TL;DR
🟡/🔴/🟢 {2–4 bullets, each a load-bearing takeaway with a traffic-light}
🔎 {session-level grounding flag — what the room re-litigated / what the stack already answers}

## Disambiguation pass
{heard → canonical table, applied}      ← D2
Roster check (referenced, not present): {heard → canonical → context}

## The architecture in one picture
```{ASCII diagram — e.g. apps/FE → middleware services → infrastructure services}```   ← D6
**Core thesis:** {one paragraph}
> 🔎 **Grounding:** {is the headline a documented gap or greenfield? cite synthesis § / ticket}

## Workflow-by-workflow (or topic-by-topic) digest          ← D1 + D3
### N. {Workflow / topic}
- **Shape:** {proposed behaviour}
- **Decisions/changes:** {what the room decided, with attribution}
> 🔎 **Grounding:** {confirm / contradict / already-handled / ⚠️ migration risk — CITED}

## Cross-cutting themes                                       ← D3 + D7
### {Atomicity · Role taxonomy · Auth/tenant context · Sessions · Delete posture …}
{discussion} + > 🔎 **Grounding:** {cited}

## Decisions register                                         ← D4
| ✅ Decided (attribution) | 🟡 Deferred (revisit) | ❓ Open / Parked |
|---|---|---|
| {decision (who)} | {deferred item (who)} | {parked question (positions)} |

## ADR candidates (feed {TICKET-NNN})                         ← D5
1. **ADR — {title}.** *Decision needed:* … *Proposed disposition (grounded):* … *Ref: synthesis §N. Ticket: TICKET-NNN.*

## {epic} story mapping                                       ← D5
| Theme in this meeting | Child story |
|---|---|
| {theme} | {TICKET-NNN + link} |

## Action inventory                                           ← D5
**{Owner (INI)}**
- {concrete next step}

## Sources                                                    ← D8
- 📄 transcript · 📐 companion synthesis (grounding source) · 🗂️ external docs ·
  🧭 precedent format · 🤖 {agent · skill (adapted) · @Name}
```

## The grounding callout — the highest-value element

Four shapes (all **must cite**). The example phrasings below use the synthetic TaskFlow / NOVA
fixture corpus (`fixtures/taskflow/`) — fictional, illustrative only:

| Shape | Example phrasing | When |
|-------|------------------|------|
| **Confirm** | "this is a documented condition, not greenfield — the transport decision already requires a bounded per-socket queue (`decision-log/D-0001.md`, Conditions §2)" | the room re-derived an existing plan |
| **Contradict / correct** | "the vault does not need its own transport — the sync protocol is a passenger on the notification channel (`decision-log/D-0001.md`, Impact §3)" | the room's model diverges from deployed reality |
| **Already-handled primitive** | "the fanout already ships a replay window keyed on the delivery cursor; a client-side backfill queue duplicates it (`wiki/entities/websocket-fanout-service.md`)" | the room proposed building something the stack provides |
| **⚠️ Migration risk** | "this reverses the opt-in digest default; changing it silently re-introduces the fatigue complaint the study measured (`wiki/synthesis/notification-fatigue-principles.md` §2)" | a decision tensions with the current posture |

A 🔎 callout with **no** `synthesis §`, `file:line`, or function reference is opinion, not grounding —
remove it or find the citation. Grounding that cites **code** (a function, a TTL, an endpoint) beats
grounding that cites prose.
