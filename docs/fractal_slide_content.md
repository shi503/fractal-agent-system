# FRACTAL Multi-Agent System — Presentation Slide Content

Visual style: Dark, modern, technical aesthetic. Use deep navy/dark gray backgrounds with bright accent colors (electric blue, teal, white text). Clean sans-serif typography. Diagrams should feel like architectural blueprints. Minimal decoration — let the structure speak.

---

## Slide 1: Title Slide

**Heading:** The FRACTAL Multi-Agent System

**Subheading:** A Hierarchical Framework for Orchestrating AI Agent Teams in Software Development

**Footer:** Fractal · Recursive · Agentic · Context-aware · Task-driven · Autonomous · Layered

---

## Slide 2: The Problem — Why Single-Agent Prompting Breaks Down

**Heading:** Single-agent prompting collapses after 35 minutes of autonomous work

**Key Points:**

Anthropic's research reveals that the assumptions of traditional prompting break down once agents run autonomously past approximately 35 minutes. Context drift, unclear intent, and under-specified constraints compound over time, degrading agent performance. The result: most people get 70%-right outputs and spend 40 minutes cleaning them up. Meanwhile, practitioners who use structured specification documents hand off complex work and walk away with confidence. The gap between these two approaches is already 10x and compounding. The FRACTAL system is designed to close that gap by giving every level of the agent hierarchy exactly the context, intent, and constraints it needs.

---

## Slide 3: The Intellectual Foundation — Four Disciplines of Prompting

**Heading:** Prompting has split into four distinct disciplines — most people only practice one

**Key Points:**

The framework draws on Nate B. Jones's "Four Disciplines of Prompting" model. Prompt Craft is the traditional skill of writing clear requests — what to do. Context Engineering provides the AI with everything it needs to know about you, your organization, and your standards. Intent Engineering encodes organizational purpose, goals, values, and decision boundaries — what to want. Specification Engineering produces structured documents that autonomous agents can execute against for hours or days without human intervention. The FRACTAL system maps each discipline to a specific level in the agent hierarchy.

**Table:**

| Discipline | Maps To | What It Tells AI |
|---|---|---|
| Specification Engineering | Strategist + Architect | What to execute and why |
| Intent Engineering | Strategist | What to want and optimize for |
| Context Engineering | Feature Leads | What to know for this workstream |
| Prompt Craft | Sub-Agents | What to do right now |

---

## Slide 4: The Architecture — A Fractal Org Chart for AI Agents

**Heading:** The system mirrors a startup org chart where each level owns a different discipline

**Key Points:**

The FRACTAL architecture is a four-level hierarchy. At the top, the Strategist acts as the seed — it performs intake, synthesizes context, encodes intent, and spawns the Architect. The Architect is the central orchestrator: it creates the blueprint, generates PRDs, delegates workstreams, and evaluates completed work. Feature Leads own individual workstreams, managing their own context and delegating scoped tasks to Sub-Agents. Sub-Agents are the leaf nodes — they execute single, atomic tasks and terminate. The fractal quality means this pattern can recurse: a Feature Lead's sub-task could itself be complex enough to spawn its own mini-hierarchy.

**Diagram description:** A vertical hierarchy showing User → Strategist → Architect → Feature Leads (multiple) → Sub-Agents (1-2 per Feature Lead).

---

## Slide 5: The Strategist — The Seed of Intent

**Heading:** Every project begins with a structured thinking exercise before any agent runs

**Key Points:**

The Strategist is the entry point. It captures the user's Project Mandate (the single-sentence goal), Core Intent and Guiding Principles (the values that guide all decisions), Definition of Done (verifiable high-level outcomes), Constraint Architecture (non-negotiable rules — tech stack, budget, timeline), and Failure Mode Register (the subtle ways the project could fail even if it meets technical requirements). Critically, the Strategist also defines the Autonomy Level: supervised, semi-autonomous, or autonomous. This controls how much the system can do without checking in with the user — a configurable trust dial.

---

## Slide 6: The Architect — The Orchestrator That Never Writes Code

**Heading:** The Architect's context window is sacred — it orchestrates, evaluates, and delegates, but never implements

**Key Points:**

A key design principle borrowed from the OpenClaw ecosystem: the Architect agent should never consume its context window on implementation tasks or bug fixes. Its role is purely strategic: synthesize the project understanding, conduct the user interview to capture "what good looks like," generate the deterministic blueprint, create PRDs for each workstream, evaluate completed work at approval gates, and escalate to the Strategist or User when a values judgment is needed. The Architect uses hard context resets between evaluations — it loads fresh context each time rather than accumulating conversation history. This keeps it sharp over long-running projects.

---

## Slide 7: The Blueprint — A Deterministic State Machine, Not LLM Routing

**Heading:** "Don't orchestrate with LLMs" — the blueprint is a YAML state machine that code executes

**Key Points:**

This is perhaps the most critical design decision in the system, drawn directly from lessons learned in the OpenClaw community. Developer Gustavo Gondim spent two months building multi-agent pipelines and concluded: every time flow control was placed inside a prompt, it introduced a failure mode. LLMs are unreliable routers. The FRACTAL blueprint is a YAML document that defines phases, workstreams, and a dependency graph. A Python routing script parses this blueprint and determines which workstreams are ready to execute based on their dependencies. The LLMs do the creative work; the code handles the plumbing.

**Code snippet example:**
```yaml
- name: Phase 2
  workstreams:
    - feature_lead: FeatureLead-Dashboard
      dependencies: [FeatureLead-Auth]
```

---

## Slide 8: Feature Leads and Sub-Agents — The Execution Layer

**Heading:** Feature Leads own their workstream end-to-end and can delegate up to 2 sub-agents

**Key Points:**

Each Feature Lead receives a PRD from the Architect containing acceptance criteria, test cases, and constraint inheritance. It operates within its own isolated workspace with scoped permissions — it can read inherited context but cannot modify it. Feature Leads can spawn up to 2 Sub-Agents for well-defined, single-file tasks. This hard limit prevents the chaos of unbounded agent spawning. Sub-Agents are the simplest unit: they receive a task specification, a file manifest with explicit read/write permissions, and acceptance criteria. They execute and terminate. The model tier scales with responsibility: the Architect uses Opus-class models, Feature Leads use Sonnet-class, and Sub-Agents use Sonnet-class for typed/framework code (Haiku only for pure text/SQL to avoid hallucination).

**Table:**

| Role | Model Tier | Permissions | Delegation |
|---|---|---|---|
| Architect | Opus (strategic) | Read-write own folder | Spawns Feature Leads |
| Feature Lead | Sonnet (balanced) | Read-write own feature | Up to 2 Sub-Agents |
| Sub-Agent | Sonnet (reliable for code) | Read-write assigned files only | None |

---

## Slide 9: The Pulse Log — Cheap Heartbeats That Only Escalate on Signal

**Heading:** Feature Leads emit structured pulse logs every 30 minutes — the Architect only reads on alert

**Key Points:**

Inspired by OpenClaw's heartbeat pattern, the FRACTAL system uses a lightweight monitoring mechanism. Every 30 minutes, each Feature Lead appends a structured JSON entry to its PULSE.md file containing timestamp, status, tasks completed, blockers, and an escalation flag. The deterministic router includes a pulse checker that reads the most recent entry and returns either HEARTBEAT_OK or HEARTBEAT_ALERT. The Architect only consumes context tokens when something actually needs attention. This is the "cheap checks first, models only when you need them" principle — most heartbeats cost zero tokens.

**Code snippet example:**
```bash
$ python3 router.py pulse ./PULSE.md
HEARTBEAT_ALERT
  Status:   BLOCKED
  Progress: 2/5
  Blockers: Database connection timeout
  Action:   Escalation required.
```

---

## Slide 10: The Eval Framework — Tool Trace as Truth, Not Agent Narrative

**Heading:** Agents are structurally good at fooling tests — the eval framework verifies through objective criteria

**Key Points:**

The evaluation framework implements a two-layer approach. The first layer is deterministic: linting, test suite execution, static analysis, security audit, and diff scope verification. These checks are objective, repeatable, and cheap. The second layer is an LLM-based judgment that assesses alignment with the project's intent — design quality, maintainability, and adherence to guiding principles. This layer is only invoked after all deterministic checks pass. The key principle from eval harness research: agents can narrate success while actually failing. The FRACTAL system trusts tool traces and test results, not self-reported narratives.

---

## Slide 11: The Deterministic Router — Working Code That Manages the Workflow

**Heading:** Five commands give the Architect a complete workflow management toolkit

**Key Points:**

The routing logic is implemented as a Python script that any agent environment can call. The init command parses the blueprint and creates a state file tracking all workstreams. The next command resolves the dependency graph and returns which workstreams are ready to execute. The update command transitions workstream status (NOT_STARTED → IN_PROGRESS → COMPLETE). The status command provides a dashboard view with progress percentage. The pulse command checks Feature Lead heartbeat logs for escalation signals. All routing decisions are deterministic — no LLM is involved in deciding what happens next.

---

## Slide 12: Key Design Principles — What Makes FRACTAL Different

**Heading:** Six principles drawn from real-world agentic system failures and successes

**Key Points:**

First, the user is always in control — upper hierarchy can unblock lower hierarchy, but critical decisions always move up. Second, hard context resets prevent drift — agents start fresh with well-defined context files rather than accumulating conversation history. Third, deterministic orchestration eliminates LLM routing failures — code handles sequencing, agents handle creative work. Fourth, each layer can modify what it creates but what it receives is read-only — this prevents lower hierarchy from overriding higher hierarchy decisions. Fifth, scoped permissions and model tiers match capability to cost — expensive models for strategic decisions, cheap models for atomic tasks. Sixth, the autonomy level is a configurable trust dial — users can start supervised and gradually increase autonomy as confidence grows.

---

## Slide 13: Getting Started — How to Use the System

**Heading:** Three steps to launch a FRACTAL-orchestrated project

**Key Points:**

Step 1: Define your project by editing the STRATEGIST.md file — fill in the mandate, intent, constraints, failure modes, and autonomy level. Step 2: Initialize the routing state by running python3 router.py init, which parses the blueprint and creates the state tracking file. Step 3: Start the Architect agent, which reads its ARCHITECT.md context, parses the blueprint, calls router.py next to identify ready workstreams, and begins spawning Feature Leads. From there, the system runs according to the deterministic blueprint, with pulse logs providing visibility and the eval framework ensuring quality at every approval gate.

---

## Slide 14: What's Next — Extending the System

**Heading:** The FRACTAL system is a v1 foundation designed to be extended and refined

**Key Points:**

Immediate next steps include wiring the templates into a Claude project using the CLAUDE.md convention, building a /commit-summarize script for git integration at workstream completion, adding a formal escalation protocol template for structured requests up the hierarchy, and testing the full cycle end-to-end on a real software project. Longer-term extensions could include a web dashboard for real-time visualization of the agent hierarchy and pulse logs, integration with CI/CD pipelines for automated eval execution, and a template marketplace where teams can share specialized Feature Lead and Sub-Agent configurations for common workstream types.
