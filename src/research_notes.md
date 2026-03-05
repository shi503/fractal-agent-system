# Research Notes: OpenClaw & Agentic Design Patterns

## OpenClaw Architecture (from Paolo Perazzo's deep dive)

### Core Architecture: Hub-and-Spoke
- Single Gateway acts as control plane between user inputs and AI agent runtime
- Gateway = WebSocket server connecting to messaging platforms + control interfaces
- Agent Runtime runs the AI loop: context assembly → model invocation → tool execution → state persistence
- Separation of interface layer (where messages come from) and assistant runtime (where intelligence happens)

### Key Config Files
- `AGENTS.md` — agent configuration
- `SOUL.md` — personality/behavior definition
- `TOOLS.md` — available tools/capabilities

### Multi-Agent Routing
- Different channels/groups can be assigned distinct agent configurations, models, and behaviors
- Enables tailored personas and permissions per community or user

### Session Management
- Session resolution, context assembly from history + workspace configs + memory search
- Session state persistence and compaction

### Memory System
- Memory search with embedding provider selection
- Memory files in workspace
- Index management for retrieval

### Security
- Sandboxed tool execution in ephemeral Docker containers
- Session-based security boundaries
- Tool policy and precedence system

### Key Sections to Investigate Further
- Multi-Agent Routing
- Session Tools (Agent-to-Agent Communication)
- Context Assembly
- System Prompt Architecture
- Session State and Compaction
- Memory Search

## TODO: Research
- [ ] OpenClaw multi-agent orchestration guide (zenvanriel.com)
- [ ] Deterministic multi-agent dev pipeline (dev.to article)
- [ ] Medium article on org-chart of 7 agents
- [ ] Pulse logs and eval patterns
