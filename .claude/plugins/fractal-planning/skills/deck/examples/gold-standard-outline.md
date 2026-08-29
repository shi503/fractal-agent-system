# Gold-Standard Deck Outline — Example

> Worked example built on the synthetic TaskFlow / NOVA fixture corpus (`fixtures/taskflow/`). Every person, number, and system named below is fictional — the point of the example is the *shape* of the outline, not its content.

**Topic:** NOVA Phase 1 — Engineering All-Hands
**Audience:** Engineering team (20 engineers, mix of frontend/backend/infra)
**One-sentence takeaway:** NOVA ships a real notification channel this phase, and every team owns exactly one unblock.
**Narrative arc:** Problem (polling makes the product feel stale) → Tension (activity climbs while the self-host envelope stays flat) → Resolution (a WebSocket fanout that Phase 2 can ride)
**Visual mood:** Blue Professional — considered, modern, professional
**Output:** `decks/nova-phase-1/nova-phase-1.html`

---

## Slide Structure (10 slides total = gold standard)

### Slide 1 — Title (required)
**Type:** Title slide
**Headline:** NOVA Phase 1
**Subhead:** From polling to push, without a second transport
**Speaker notes:** Set context — this is the moment the product stops feeling stale between refreshes. Three things this talk covers: where we are, what ships in Phase 1, and what each team needs to do.

---

### Slide 2 — The Problem
**One idea:** Polling makes staleness a floor, not a bug we can tune away
**Visual:** Single large stat — "30s poll interval = 30s of guaranteed staleness"
**Speaker notes:** Today the inbox is polled on a fixed interval. The interval *is* the staleness ceiling, so no amount of tuning removes the complaint that started the initiative. Worse, the cost is inverted: the quietest workspace burns the most requests for the least value. The problem is structural, not a resource ask.

---

### Slide 3 — The Tension
**One idea:** Workspace activity keeps climbing while the self-host resource envelope stays flat
**Visual:** Two-line chart — events per workspace (rising) vs. memory envelope on a reference box (flat)
**Speaker notes:** Our self-host reference boxes have not grown. Event volume has. We cannot poll our way out of that, and we cannot ask self-hosters to buy bigger hardware just to get a notification sooner.

---

### Slide 4 — The Resolution
**One idea:** One bidirectional channel replaces polling — and Phase 2 rides it
**Visual:** Before/After flow — periodic poll loop → single persistent fanout connection
**Speaker notes:** WebSocket fanout wins on one measured argument and one structural one. Measured: delivery is comfortably fast at self-host scale when the frame is pre-encoded once per event. Structural: it is bidirectional, so the Phase 2 offline vault syncs over the same connection instead of introducing a second transport a self-hoster has to configure.

---

### Slide 5 — Architecture (What We Built)
**One idea:** Three surfaces, one cohesive flow
**Visual:** Minimal service diagram — fanout service → preference resolver → client inbox
**Speaker notes:** The three surfaces map to three owners. The fanout service owns delivery and the replay window. The preference resolver owns who a given event expands to. The client inbox owns presentation and read state. Each has a clear boundary and a stable contract.

---

### Slide 6 — Phase Scope
**One idea:** Phase 1 ships the channel; Phase 2 ships the offline vault on top of it
**Visual:** Two-column table — Phase 1 (green checkmarks) vs. Phase 2 (gray clock icons)
**Speaker notes:** Scope discipline is how we ship. Phase 1 is: the fanout service, the preference defaults, the replay window, the client inbox. Phase 2 is: the vault storage layer, the sync protocol, and conflict-resolution UX. Nothing from Phase 2 moves into Phase 1 without the accountable owner's sign-off.

---

### Slide 7 — Key Risk
**One idea:** A stalled consumer is the one failure mode that can take the fanout loop down
**Visual:** Risk card — impact (high) × likelihood (medium) × owner (RV)
**Speaker notes:** The spike found it: one slow socket back-pressures the whole loop if the outbound queue is unbounded. The mitigation is already a hard condition on the decision — bound the queue, drop and record rather than block. RV owns it. If the bound proves too aggressive under real load, the contingency is a wider replay window, not a re-scope.

---

### Slide 8 — Team Unblocks
**One idea:** Each team has exactly one action item before the phase gate
**Visual:** Three-row table — Team | Action | Due date
**Speaker notes:** Backend: bounded per-socket queue plus the replay cursor. Frontend: preference center wired to the resolved defaults. Infra: documented proxy idle-timeout guidance for self-hosters. Those three unblocks are all that stands between us and the Phase 1 gate.

---

### Slide 9 — Success Metrics
**One idea:** We'll know it worked when staleness stops showing up in feedback
**Visual:** Three KPIs — delivery p95 target, digest opt-in rate, memory headroom on the reference box
**Speaker notes:** These are the three numbers we track this phase. Delivery p95 is the north star — if it regresses past the envelope, we investigate before adding features. Opt-in rate tells us the defaults are right rather than merely quiet. Memory headroom is the self-host promise, and it appears in the phase review.

---

### Slide 10 — Next Steps (required)
**Type:** Closing / next-steps slide
**Headline:** What happens next
**Content:**
- Week 1 — bounded outbound queue + replay cursor (RV)
- Week 2 — preference center wired to resolved defaults (SP)
- Week 3 — proxy idle-timeout guidance published (CL)
- Week 4 — Phase 1 gate review (AR + TN)
- Phase 2 kickoff: immediately after the gate

**Speaker notes:** The next four weeks are the execution window. If all three unblocks land on time, the gate review is a formality. Today's ask: confirm your action item in the team tracker by Friday.

---

## 80:20 Principle Applied

Each slide above carries **one idea**. The supporting data, context, and alternatives are in speaker notes — not on the slide. A viewer seeing only the slides gets the story arc. A presenter with the notes gets the depth.

**What was cut:**
- The full transport comparison, including the rejected candidates (belongs in the decision entry, not a slide)
- Full protocol detail for the replay window (link the design doc from the speaker notes)
- Phase 3 hardening plans (mentioned briefly at the Slide 6 scope boundary, not a full slide)
- Budget discussion (separate conversation, not part of this narrative arc)
- Team org chart (not relevant to this message)

---

## Format Gate Check

- Title slides: 1 (Slide 1) — PASS
- Content slides: 8 (Slides 2–9) — PASS (at maximum; any addition requires a cut)
- Next-steps slide: 1 (Slide 10) — PASS
- Total: 10 slides — PASS

If this deck were requested with 12 content slides, the skill would refuse and propose cuts to reach 8.
