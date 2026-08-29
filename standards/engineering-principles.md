# Engineering Principles

**Audience:** Any engineer or agent contributing code to a project built on this stack (TypeScript, React, Next.js App Router, Prisma).
**Status:** Team standard. Apply to all new code and use as regression checks when modifying existing code.

> **Why principles, not just patterns:** every principle here must hold regardless of which framework, library, or infrastructure component is in use. Enforcing a principle via a current tool — a middleware, a state library, an ORM — does not substitute for an explicit check, because tools get swapped and upgrades can silently remove the protection. These principles are written as regression guards: if a refactor removes the behavior a principle requires, that is a defect regardless of whether the current tooling would have prevented it.

---

## 1. Single Responsibility — Each Unit Owns One Concern

A component, hook, route handler, or service function should own exactly one concern. The concerns in a typical full-stack TypeScript app are: presentation, application/business logic, and infrastructure access. These must not mix.

Mixing concerns creates units that are impossible to test in isolation, code that cannot be swapped, and bugs that are hard to localize. A component that fetches data, transforms it, and renders it has three reasons to change — and three paths to regression.

- A React component owns rendering and user interaction only. It calls a store or a query hook; it does not call `fetch` or a database client directly.
- A client-side store (e.g. a Zustand slice) owns state management and orchestrates calls to a typed API client for one feature. It does not embed presentation JSX.
- A Next.js Route Handler (`app/api/**/route.ts`) owns request parsing, delegation to one service function, and response shaping. Handlers longer than ~20 lines usually indicate logic leakage into the route.
- A service function (e.g. `lib/services/issues.ts`) owns business logic for a domain. It calls repositories; it does not call the Prisma client directly.
- A repository (e.g. `lib/repositories/issue-repository.ts`) owns all reads/writes for a single aggregate. No service imports `db` (the Prisma client) directly when a repository exists for that model.

```ts
// Bad — the route handler does parsing, business logic, and the DB call.
export async function POST(req: Request) {
  const body = await req.json()
  const issue = await db.issue.create({
    data: { title: body.title, columnId: body.columnId, order: Date.now() },
  })
  return Response.json(issue)
}

// Good — the route handler delegates; the service owns ordering + validation.
export async function POST(req: Request) {
  const input = createIssueSchema.parse(await req.json())
  const issue = await issueService.createIssue(input)
  return Response.json(issue)
}
```

---

## 2. Authorization at Every Layer

Authentication and authorization checks must be enforced at the framework boundary **and** at the data/service layer. Boundary-only enforcement is insufficient.

Boundary checks (middleware, session guards) prevent unauthenticated requests from reaching a handler. They do not guarantee that the authenticated user is permitted to act on the specific resource requested. Data-layer checks — verifying team or resource ownership for the specific record — must be explicit in service or query logic. Do not assume the current auth framework enforces this transitively: a middleware change, a route added outside the matcher, or a library upgrade can silently remove the protection. Explicit checks in service code are the regression guard.

- `middleware.ts` (or an auth-aware layout) enforces session presence at the routing boundary. A check that only confirms "a session exists" is not a substitute for resource-level permission checks.
- Server Actions and Route Handlers that read or mutate team-scoped data must verify the session's team membership against the specific resource being touched — not assume that "the request reached this handler" implies authorization for every record in it.

```ts
// Bad — team membership is never checked; any signed-in user can read any board.
export async function getBoard(boardId: string) {
  return db.board.findUniqueOrThrow({ where: { id: boardId } })
}

// Good — resource-level check lives in the service, independent of the route guard.
export async function getBoard(boardId: string, userId: string) {
  const board = await db.board.findUniqueOrThrow({
    where: { id: boardId },
    include: { team: { include: { members: true } } },
  })
  const isMember = board.team.members.some((m) => m.userId === userId)
  if (!isMember) throw new ForbiddenError("not a member of this board's team")
  return board
}
```

> **Regression note:** if a refactor removes a team-scope filter from a query, or a middleware matcher is narrowed so a sensitive route falls outside it, treat it as a security regression regardless of what the current auth library would have caught.

---

## 3. Validation at the Boundary

Input validation belongs at the entry point — the form layer (client) or the request-schema layer (server). Inline validation scattered inside component logic or handler bodies is a maintenance anti-pattern.

Inline checks (`if (!title.trim())` repeated in three handlers) scatter validation rules, are not reusable, and are easy to miss when inputs change. A declarative schema at the boundary is the single source of truth for what constitutes valid input.

- Define request and form schemas with `zod` (or an equivalent schema library) and parse at the boundary — `schema.parse(input)` in the Route Handler, `zodResolver(schema)` in the form. Do not validate ad hoc inside the submit handler or handler body.
- For non-form inputs (route params, search params, headers), validate explicitly before use — do not trust URL-derived values inline in component or handler logic.

```ts
const createIssueSchema = z.object({
  title: z.string().trim().min(1).max(200),
  columnId: z.string().cuid(),
  priority: z.enum(["LOW", "MEDIUM", "HIGH", "URGENT"]).default("MEDIUM"),
})

export async function POST(req: Request) {
  const input = createIssueSchema.parse(await req.json())
  // input is now a typed, validated value — no further ad hoc checks needed downstream
  return Response.json(await issueService.createIssue(input))
}
```

Validators on security-sensitive inputs (role values, resource IDs, redirect URLs) are required, not optional — an unvalidated `redirectTo` query parameter is an open-redirect risk.

---

## 4. Delegation for Multi-Step Orchestration

When a handler or component needs to coordinate more than one or two operations across different services, extract the orchestration into a dedicated coordinator function. Handlers and components own binding and delegation — not multi-step workflows.

A handler that calls three services has mixed binding concerns with workflow logic. The workflow becomes invisible at the service layer, and changes to it require touching the handler — the route-level equivalent of a god object.

- A component that would need to call more than one store method or API client method to respond to a single user action should extract the orchestration into the store instead. The component calls one method; the store coordinates.
  - Example: an "archive board" action that must call `boardApi.archive()`, then `columnApi.archiveAll()`, then update local state, belongs in `useBoardStore().archiveBoard()` — not spread across the click handler.
- A Route Handler that would need to make more than 1–2 distinct service calls should delegate to a single service function that owns the workflow.
  - Example: an "invite team member" handler that creates a `TeamMember` row, sends an invite email, and writes an audit `Comment` should call `teamService.inviteMember()`, not inline all three steps in the handler.

---

## 5. Explicit Exception Handling — No Silent Failures

Every caught exception must be explicitly handled — at minimum, logged. An empty `catch` block, or a `catch` that swallows the error and returns a default with no log, is a defect.

Silently swallowing errors removes observability and makes failures invisible. Code that catches exceptions and continues appears healthy while silently failing — the worst possible failure mode in production. This is a documented anti-pattern with no valid use case.

```ts
// Bad — the failure vanishes; callers see an empty array and assume "no issues".
async function listIssues(boardId: string) {
  try {
    return await db.issue.findMany({ where: { boardId } })
  } catch {
    return []
  }
}

// Good — logged before any fallback, and the caller can distinguish failure from "empty".
async function listIssues(boardId: string) {
  try {
    return await db.issue.findMany({ where: { boardId } })
  } catch (err) {
    logger.error("issues.list_failed", { boardId, err })
    throw err
  }
}
```

- A `.catch()` on a promise, or a `try/catch` around an `await`, with no logging and no rethrow is never acceptable.
- Minimum: `logger.error("module.context", { ...context, err })` before continuing, or rethrow.
- Error boundaries and Route Handler `catch` blocks that forward a raw upstream error body (`err.message` from a third-party client) to the client response are security defects — log internally, return a sanitized message externally.

---

## 6. Type-Safe Interfaces at Boundaries

All data crossing a module or network boundary must use named, typed structures. `any`, untyped `object`, and positional tuples at boundaries are latent defects.

Positional data structures require the reader to know field order. A field-order change or a new field silently breaks callers. Named types make boundaries self-documenting and make breaking changes visible at compile time.

- `any` is forbidden at service, API-client, and repository boundaries. All API response and request shapes must be declared as `interface` or `type`, either inferred from a `zod` schema (`z.infer<typeof schema>`) or hand-maintained in a shared `types/` module.
- Functions must not return tuple types like `[Issue, boolean, string]`. Return a named object: `{ issue, created, warning }`.
- `Record<string, unknown>` as a public function's return type requires a typed shape instead — reserve `unknown` for values that are genuinely opaque at that boundary, and narrow before use.
- Explicit return type annotations are required on all exported functions.

---

## 7. Minimum Error-Path Test Coverage

Tests must cover failure paths, not just the happy path. The minimum coverage for any externally reachable operation is: authentication/authorization failure, invalid input, upstream failure, and the happy path. Additional cases are expected for meaningful coverage.

Production failures occur at the edges — invalid input, missing sessions, a database call that rejects. Tests covering only the happy path provide false confidence. The minimum four scenarios are the cases most likely to regress silently when code changes.

- Component tests must cover the happy-path render, an error state (the query/mutation hook returns an error), and the loading/pending state.
- Route Handler tests must cover: unauthenticated (401/redirect), invalid input (400, schema rejects), the resource-not-found or not-authorized case, and the happy path.
- Store/service tests must cover the success path and the error path, including that any error state is set correctly and any partial side effects are not left inconsistent.
- Adding a field to a response shape without adding a test assertion for that field means regressions in that field are invisible.

---

## 8. Type-Safe Handling of Secrets

Any value holding a credential, API key, or token must never appear in a log line, an error message, a serialized object dump, or a stack trace. Passing a secret around as a plain `string` alongside ordinary data makes it trivially easy for a debug log or a thrown error to leak it.

- Never `console.log`, `JSON.stringify`, or interpolate a full request/settings object that contains a secret field — log an explicit allowlist of fields instead.
- Read secrets from environment variables at the point of use (or via a narrow, typed config module); do not pass raw secret values as function parameters beyond the call that needs them.
- Prefer a distinct, clearly named type or wrapper (e.g. a `type ApiKey = { readonly value: string } & { __brand: "ApiKey" }`) for secret-shaped values passed through more than one function, so a reviewer can see at the type level that a value is sensitive — and so a generic serializer does not accidentally include it in a log payload.
- Redact secret fields in any error-reporting or logging middleware by name (`apiKey`, `token`, `password`, `secret`) as a defense-in-depth backstop, not as the only control.

> **Regression note:** a refactor that widens a secret-carrying parameter from a narrow wrapper type to a plain `string`, or that adds a full-object log call where a field-allowlist log call previously existed, is a security regression — even if no leak has occurred yet in practice.

---

## 9. Design and Decision Discipline

### Iterative Planning Over Waterfall

Break work into increments where each delivers a demoable artifact. Commit to what's achievable in the next 1–2 milestones with high confidence; iterate on the remainder after real data is available.

**Why:** large scope plans with optimistic estimates create false confidence and lock in decisions before assumptions are validated. Small increments surface blockers early while the blast radius is still small.

**In practice:**
- Separate every scope list into Must-Ship / Should-Ship / Can-Wait. When trade-offs arise, resolve against that order — do not default to building everything.
- Present estimates as hypotheses requiring validation, not commitments.
- Surface risks in a dedicated section — not buried in prose.

### Trace Technical Decisions to Requirements

Every technical decision must connect to a stated requirement. "We need X" is incomplete; "requirement Y drove Z, which led to decision X" is the minimum acceptable framing.

**Why:** technical decisions that can't be traced back to a real need are candidates for removal. Traceability makes the cost of a decision visible and prevents gold-plating.

**In practice:**
- Design notes and PR descriptions must state the driving requirement, not just the technical rationale.
- Before adding complexity, state which requirement it serves.
- During review: changes that introduce new abstractions without a traceable requirement get flagged.

### Complexity Analysis for Cross-Cutting Requirements

Security, performance, and reliability requirements must be implemented, but not applied as blanket mandates without analyzing complexity and cost.

**Why:** a rule like "add a team-scope filter to every query" may be trivial on flat tables and expensive on deep join chains. Applying it without analysis creates both performance problems and false confidence that the requirement was actually met.

**In practice:**
- When implementing a cross-cutting requirement, document what it mandates, how the implementation meets it, and any trade-offs.
- Flag requirements that are infeasible as stated — propose an equivalent control that achieves the same outcome at acceptable cost.
- Do not shortcut the requirement, but do challenge it when it's stated as a specific mechanism rather than the actual outcome it's protecting.
