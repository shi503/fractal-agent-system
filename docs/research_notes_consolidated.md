# Consolidated Research: Agentic Design Patterns for Fractal Multi-Agent Architecture

## Source 1: OpenClaw Architecture (Paolo Perazzo, Substack)

OpenClaw follows a hub-and-spoke model with a single Gateway as the control plane. The Agent Runtime handles context assembly from session history, workspace configs (AGENTS.md, SOUL.md, TOOLS.md), and memory search. Each agent is an isolated environment with its own workspace directory, session store, and authentication context. Multi-agent routing allows different channels to be assigned distinct agent configurations, models, and behaviors. The system supports session-based security boundaries and sandboxed tool execution.

Key config files: AGENTS.md (agent configuration), SOUL.md (personality/behavior), TOOLS.md (available capabilities).

## Source 2: Multi-Agent Orchestration Guide (Zen van Riel, GitHub Senior AI Engineer)

Three components define an agent: (1) Workspace and Agent Directory with isolated config/memory/skills, (2) Session Store for conversation history and state, (3) Authentication Context for per-agent credentials. The "Opus Orchestrator with Codex Workers" pattern is the most practical: one orchestrator agent (capable model like Claude Opus) coordinates multiple worker agents (faster, cheaper models). The orchestrator receives complex requests, breaks them into subtasks, delegates to workers, and synthesizes results. Workers handle bounded tasks within narrow scopes. This mirrors how senior engineers think about problem decomposition.

Key insight: "Start simple, scale deliberately." Add agents one at a time. Validate each before adding another.

## Source 3: Deterministic Multi-Agent Dev Pipeline (Gustavo Gondim, dev.to)

Critical lesson: "Don't orchestrate with LLMs." Every time flow control was put in a prompt, it introduced a failure mode. LLMs are unreliable routers. Use them for creative work, use code for plumbing. The solution was Lobster (OpenClaw's workflow engine) — a typed, local-first pipeline runtime with deterministic execution, approval gates, resume tokens, and structured data flow.

The Ralph Orchestrator pattern: hard context resets between iterations. The agent has no memory except a session file (goal, plan, status, log), and each iteration starts fresh with only that file as context. This trades throughput for correctness.

Session keys as data model: the pattern `pipeline:<project>:<role>` gives project isolation, role separation, and addressability in one string. No database needed.

Sub-workflow architecture: main workflow delegates to sub-workflows (sub-lobsters) with loop support. Each agent gets own workspace with AGENTS.md, SOUL.md, own tools (programmer gets exec/write; reviewer gets read-only; tester gets exec + test runners), own model selection, own memory and session history.

## Source 4: Heartbeats / Pulse Logs (Damien Gallagher, dev.to)

A heartbeat is a regular pulse where the agent checks a short checklist and decides: (1) Nothing important changed → HEARTBEAT_OK, or (2) Something needs attention → HEARTBEAT_ALERT + summary. The key pattern is "cheap mode first": run a lightweight deterministic script first, only involve an LLM model when there's actual signal. This gives $0 heartbeats most of the time, with clean human summaries when something real happens.

Frequency tuning: active shipping = 5-15 min, build mode = 30 min, watching = 60-120 min.

The heartbeat is a gate, not a workflow. It checks: Did anything break? Did anything change? Is anything time-sensitive?

## Source 5: Eval Harness Patterns (Duckweave, Medium — paywalled but key concepts visible)

12 eval harness patterns for AI agents. Key concepts from the preview: agents are "uniquely good at fooling tests" — not maliciously, but structurally. They operate across tools, external state, timing, and partial observability. Classic model evals check "input → output" but agents are "input → plan → tool calls → state changes." The eval harness needs to treat the tool trace as the truth: every call, args, response, latency, and error.

Visible patterns from the diagram: Scenario Spec → Sandbox Setup → Tool Proxy & Recording → State Oracle → Scoring & Report. Metrics include: Accuracy, Robustness, Drift, Efficiency, Honesty. Key distinction between "Truth" and "Storytelling" — agents can narrate success while actually failing.

## Patterns Applicable to Our Fractal Architecture

### 1. Hard Context Resets (from Ralph Orchestrator)
Each agent level should start with a clean context file (goal, plan, status, log) rather than accumulating conversation history. This preserves the Architect's context window.

### 2. Deterministic Orchestration (from Lobster)
The Architect should not use LLM reasoning to decide workflow order. Instead, the blueprint.md should define a deterministic execution plan that is followed mechanically.

### 3. Heartbeat/Pulse Pattern (from OpenClaw Heartbeats)
Feature Leads should emit periodic pulse logs — cheap deterministic checks first, LLM summarization only when something needs attention. This gives the Architect visibility without consuming context.

### 4. Session Key Addressing (from Lobster pipeline)
Use structured session keys like `project:<name>:architect:<name>:feature:<name>:agent:<role>` for addressability and isolation.

### 5. Tool Trace as Truth (from Eval Harness)
Validation should be based on actual tool traces and state changes, not agent self-reports. The Architect should verify Feature Lead completion through objective criteria, not narrative.

### 6. Approval Gates (from Lobster)
The Architect's evaluation of Feature Lead work should be an explicit approval gate before commit-summarize.

### 7. Isolated Workspaces with Scoped Permissions (from OpenClaw)
Each agent level gets its own workspace, tools, and model selection. Lower hierarchy agents get scoped-down permissions.
