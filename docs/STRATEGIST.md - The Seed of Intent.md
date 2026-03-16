# STRATEGIST.md - The Seed of Intent

This document is the Tier 0 entry point for the entire FRACTAL multi-agent system. It encodes the project-level intent, constraints, and failure modes that the Architect reads before decomposing any epic into workstreams.

The Strategist agent reads this file, synthesizes the information, and then produces BLUEPRINTs and delegates to the Architect to begin the work.

---

## 1. Project Mandate

*A single, clear sentence describing the overall goal of the project.*

**Example:** Build a production-ready web application for a community-driven sports league, including user authentication, team management, and a schedule viewer.

## 2. Core Intent & Guiding Principles

*What are the core values and principles that should guide all decisions in this project? This is where you encode the "why" behind the work. List in priority order — trade-offs should be resolved by this ordering.*

**Example:**
- **User-centric design:** The user experience should be simple, intuitive, and fast.
- **Security first:** Protect user data above all else.
- **Scalability:** The system should be able to handle 10,000 concurrent users.
- **Maintainability:** Code should be clean, well-documented, and easy to understand.

## 3. Definition of Done (High-Level)

*What does it mean for the entire project to be considered "done"? This should be a list of high-level, verifiable outcomes.*

**Example:**
- [ ] The web application is deployed to a production environment.
- [ ] The application passes all end-to-end tests.
- [ ] The codebase has 90% test coverage.
- [ ] The user guide and technical documentation are complete.

## 4. Constraint Architecture

*The non-negotiable rules of the project. This includes technical constraints, budget constraints, and any other limitations. Do not propose alternatives without explicit Strategist approval.*

**Example:**
- **Tech Stack:** React, TypeScript, Node.js, PostgreSQL
- **Budget:** $10,000 USD
- **Timeline:** 3 months
- **Third-Party Services:** Must use AWS for hosting, Stripe for payments.

## 5. Failure Mode Register

*What are the subtle ways this project could fail, EVEN IF it meets the technical requirements? This is the "what does wrong look like?" question. The Architect must actively guard against each one.*

**Example:**
- **FM-1: Onboarding Cliff** — The application is technically functional but the user interface is confusing. Developers try it once, get stuck, and leave.
- **FM-2: Security Theater** — Auth works but edge cases (session expiry, token refresh, brute force) are unhandled.
- **FM-3: Latency Destroys Trust** — Features work correctly but take so long that users assume the system is broken.

## 6. Autonomy Level

*Controls the level of autonomy granted to the agent hierarchy.*

### `AUTONOMY_LEVEL: supervised`
*The Architect must seek user approval for all major decisions: blueprint, PRD generation, and evaluation of completed work.*

### `AUTONOMY_LEVEL: semi-autonomous` ← recommended default
*The Architect can approve Layer 1-2 (deterministic + LLM judgment) evaluations independently. The Strategist reviews Layer 3-4 (persona qualitative + strategic benchmark) at milestone boundaries or for high-stakes features. The Architect escalates only on 2nd evaluation failure or scope-changing discoveries.*

### `AUTONOMY_LEVEL: autonomous`
*The Architect is fully autonomous and can approve all stages. The Strategist is only engaged on high-severity blockers.*

### Evaluation Retry Policy

| Attempt | What Happens |
|---------|-------------|
| **1st fail** | Evaluator provides specific feedback. The lower tier fixes and resubmits. |
| **2nd fail** | **Stop.** Do not retry. Escalate to the next tier up. |

**Escalation chain:** Sub-Agent → Feature Lead → Architect → Strategist/User

## 7. Platform Evolution Strategy

*Current phase, next transition trigger, and decision principles for phase-appropriate architecture.*

**Example:**
- **Current Phase:** Phase 1 — Core product (auth, billing, basic workflows)
- **Next Transition:** Phase 2 — Multi-tenant isolation, shared AI layer, cross-module data flow
- **Transition Criteria:** [define specific gates, e.g. "paying customers in production + 3 workflow modules"]
- **Full strategy reference:** `.SPECS/guides/platform-strategy.md`

## 8. Milestone Roadmap

*Major checkpoints from current state to platform maturity. Each milestone is a gap-analysis trigger point. Define compliance gates per milestone — do NOT scope SOC2/compliance as a binary all-or-nothing project checkbox.*

**Example:**
| Milestone | Gate | Compliance Scope |
|-----------|------|-----------------|
| Milestone 1: Self-Serve Go-Live | New user signs up and makes first API call without human intervention | Auth, API keys, audit logging |
| Milestone 2: Production Workflows | Core workflows handle real data reliably | Data handling, PHI boundaries, audit trail |
| Milestone 3: Platform Maturity | Multiple modules sharing centralized AI service layer | Full audit scope |

### Evaluator Archetypes

Define 2-4 personas who represent your real users. These guide gap analysis prioritization and Layer 3 qualitative eval:

| Evaluator | What They Notice | Priority Filter |
|-----------|-----------------|----------------|
| [Technical Buyer / Platform Lead] | API-first design, integration burden, schema stability | "If it doesn't integrate, I'm not interested." |
| [End User / Operator] | Workflow fit, speed, trust signals | "Does this make my job easier or harder?" |
| [Compliance / Security Buyer] | Audit trail, data isolation, security posture | "Can I defend this in an audit?" |

## 9. Source Control Preferences

*Governs the Architect's epic wrap-up protocol. Set once, update via Strategist interview when preferences change.*

| Preference | Options |
|---|---|
| **Commit cadence** | (a) After each workstream HANDOFF, (b) After each BLUEPRINT phase, (c) At epic completion only, (d) Never — manual |
| **PR policy** | (a) Auto-create at epic completion, (b) Only when explicitly asked, (c) Never — manual |
| **Worktree policy** | (a) Not in use, (b) Used — Architect auto-cleans after commit |

**Recommended default:** Per-phase commits + PR at epic completion + no worktrees.
