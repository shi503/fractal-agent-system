# Architecture Patterns

**Audience:** Engineers and agents designing or extending services on this stack.
**Status:** Team standard. These are the target architectural patterns for new code.

> **Scope:** these patterns apply at design time. Existing code that predates them is not required to be refactored immediately, but new code should conform. When a pattern requires a change to existing code, treat that as a planned migration, not incidental cleanup.

---

## 1. Clean Architecture (Ports and Adapters)

This stack uses **Clean Architecture (Hexagonal / Ports and Adapters)** as the structural model. The core principle: business logic has no dependency on infrastructure — infrastructure adapts to the domain, not the other way around.

| Ring | Location | Contents |
|---|---|---|
| Interface Adapters | `app/api/**/route.ts`, React components | Route handlers, request/response shaping, UI rendering — no business logic |
| Entities | `lib/domain/` | Pure domain types — zero infrastructure dependencies |
| Application Ports | `lib/ports/` | Interfaces for external systems (a `MailSender`, a `NotificationQueue`) |
| Application Use Cases | `lib/services/` | Business logic implementations |
| Infrastructure | `lib/repositories/`, `lib/adapters/` | Concrete implementations of ports and data access (Prisma, external APIs) |

**Import discipline:** infrastructure may import port interfaces and entities. Entities and ports must never import from infrastructure. Enforce ring boundaries with lint rules (e.g. `eslint-plugin-boundaries` or a custom import rule) rather than convention alone.

```
Allowed:     repositories/adapters → ports → domain
             services → ports → domain
             route handlers / components → services
Forbidden:   domain → anything external
             ports → repositories/adapters
             services → repositories/adapters directly (must go through a port)
```

The same shape applies on the client: a component never imports `fetch` or a raw API client directly — it goes through a store or a typed query hook, which is the infrastructure ring for the frontend.

---

## 2. Contract-First API Design

For any API surface consumed by more than one caller — a public route, a webhook receiver, a message payload — the contract is the source of truth, not the implementation.

**Applies to:** REST/HTTP routes under `app/api/`, webhook receivers, any queue or pub/sub payload shared between processes.
**Does not apply to:** internal function calls within a single module, component props.

- Define request/response shapes with a schema library (`zod`) in a shared location (`lib/contracts/` or `types/`) and derive both the server-side validation and the client-side types from the same schema — `z.infer<typeof schema>`. Do not hand-maintain the type in two places.
- Treat the schema module as reviewed source code with the same standard as application code; a route handler and its client caller must import the same schema, not two independently maintained shapes.
- Prefer generating an OpenAPI document from the schema definitions when the API has external consumers, rather than hand-writing one that can drift from the actual routes.

```
lib/contracts/
  issue.ts        ← zod schema, single source of truth
  board.ts

app/api/issues/route.ts        imports issueSchema for request validation
lib/api-client/issues.ts       imports issueSchema for response typing
```

### Message and Event Payloads

- Define a versioned schema for every event or queue message type.
- Include an explicit `version` field in the payload.
- Consumers must be Tolerant Readers: ignore unknown fields, handle missing optional fields gracefully.
- Schema changes follow the Expand/Contract pattern: add fields in one deploy, remove old fields in a later deploy once all consumers are updated.

---

## 3. Deployment Context Pattern

When a service must support more than one deployment or runtime mode (e.g. a self-hosted database vs. a managed one, a queue-backed background job vs. an inline synchronous call in local development), express the difference as alternate implementations behind the same interface — not as a mode flag branching inline through business logic.

**Why:** inline mode branching (`if (process.env.DEPLOY_MODE === "self-hosted")`) scatters deployment logic throughout the codebase and makes each path harder to test. Two implementations of the same interface is explicit, testable, and extensible.

```ts
// Both implement the same port.
interface NotificationQueue {
  enqueue(event: NotificationEvent): Promise<void>
}

class RedisNotificationQueue implements NotificationQueue {
  async enqueue(event: NotificationEvent) { /* push to Redis stream */ }
}

class InlineNotificationQueue implements NotificationQueue {
  async enqueue(event: NotificationEvent) { /* process synchronously — local dev */ }
}

// Composition root selects at startup based on configuration.
function getNotificationQueue(env: Env): NotificationQueue {
  return env.REDIS_URL ? new RedisNotificationQueue(env.REDIS_URL) : new InlineNotificationQueue()
}
```

The interface, the event types, and every downstream consumer of `NotificationQueue` are identical across deployment contexts. The difference is localized to the infrastructure ring.

---

## 4. Framework Layer for Cross-Cutting Concerns

Auth enforcement, structured logging, and rate limiting are applied by a framework/middleware layer that wraps the application — individual route handlers never implement these directly.

**Why:** cross-cutting concerns duplicated in handler code create inconsistency (easy to miss in a new route), and couple handler tests to infrastructure details. A middleware layer applies them universally without per-handler participation.

**In practice:**
- Auth enforcement lives in `middleware.ts` (session/route matching) plus an explicit per-resource check in the service layer (Principle 2 of `engineering-principles.md`) — not scattered `if` checks in individual handlers.
- Logging context (request ID, user ID, team ID) is attached by a logging middleware/wrapper and consumed by every log call, not assembled ad hoc per handler.
- Rate limiting is applied at the edge (middleware or a gateway), not enforced inline inside route handlers.

**Regression note:** if the middleware layer is removed, narrowed, or bypassed by a new route added outside its matcher, routes that relied on it for auth or rate limiting silently lose that protection. Cover cross-cutting behavior with an integration-level test, not only a unit test of the middleware itself.

---

## 5. Fail-Fast Dependency Probing

Required infrastructure dependencies must be probed at process startup. If a required dependency is unreachable, the process must fail to start — not log a warning and continue serving requests.

**Why:** a process that starts successfully but fails on every request touching an unreachable dependency (a database, an auth provider) appears healthy to an orchestrator while being completely non-functional. Failing fast surfaces the problem immediately and prevents traffic from being routed to a broken instance.

**Required vs. optional:**
- **Required:** primary database, auth/session store — the process cannot serve any request without these. → Fail startup.
- **Optional:** analytics sink, a non-critical third-party integration — the process degrades gracefully without these. → Log a warning, continue.

```ts
async function probeDependencies(env: Env): Promise<void> {
  try {
    await db.$queryRaw`SELECT 1`
  } catch (err) {
    throw new Error(`database unreachable at startup: ${err}`)
  }
  // Optional dependency: log and continue rather than throw.
  try {
    await analytics.ping()
  } catch (err) {
    logger.warn("analytics.startup_probe_failed", { err })
  }
}
```

---

## 6. Standardized Health Endpoints

Every deployable service must expose the following endpoints, provided by a shared framework layer rather than hand-written per service:

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | Liveness — is the process running? |
| `GET /api/health/ready` | Readiness — are required dependencies reachable? |
| `GET /api/health/info` | Build version, commit SHA, environment |

The readiness endpoint must actively probe required dependencies (Principle 5) — not just return `200`. An endpoint that returns `ready` while its database is unreachable defeats the purpose of the readiness check.

---

## 7. Permission Model as Data, Not Code

When an application needs to define what roles can perform what actions on what resources, that definition belongs in a structured, reviewable file — not scattered as inline `if (role === "ADMIN")` checks across the codebase.

**Why:** hardcoding a permission model inline couples it to wherever it happens to be checked first, and makes it invisible to anyone auditing "what can a member do." A single structured definition is reviewable, diffable, and testable independently of the routes that use it.

**General pattern:**
- Define the permission model in one place (a TypeScript object, a small YAML file, or a table) — role → action → resource-type mappings.
- Validate its shape (a `zod` schema or a JSON Schema) so a malformed entry fails fast rather than silently granting nothing.
- Application code reads the compiled model and asks "can this role do this action on this resource type" — it does not re-derive the answer per call site.
- The underlying enforcement mechanism (in-process check, an external policy engine) is an infrastructure detail behind this model; the model itself is store-agnostic.

---

## 8. Event-Driven Integration — Queues First, Webhooks Last Resort

When a service needs to notify other parts of the system about a state change, the default choice is a durable queue or event stream. An outbound webhook to another service is a fallback of last resort, not a default integration pattern.

**Why:** a queue provides durable delivery, replay, backpressure, and decoupled scaling. A webhook is a fire-and-forget HTTP call with no delivery guarantee, no ordering, and tight temporal coupling between producer and consumer. Choosing a webhook where a queue is feasible is an architectural regression.

**Default recommendation:** evaluate a queue first. A proposal to use a webhook must explicitly state that a queue was considered and why it was ruled out.

### Required properties when a webhook is unavoidable

All three are mandatory. Missing any one is a blocking review finding.

1. **Expand/Contract schema evolution** — producer payload changes add optional fields first, remove old fields only in a later deploy once consumers are updated. No breaking change in a single deploy.
2. **Tolerant Reader consumers** — the receiving endpoint ignores unknown fields and handles missing optional fields gracefully. It never fails hard on an unrecognized payload shape.
3. **Formal versioning** — every payload carries an explicit `version` field or a versioned URL path. The consumer routes on version; "we'll stay compatible" is not a versioning strategy.

### Review checklist

- [ ] Was a queue evaluated and explicitly ruled out?
- [ ] Does the payload carry a formal version identifier?
- [ ] Is there a retry mechanism with backoff and a dead-letter or alerting path?
- [ ] Is delivery idempotent? (duplicate delivery must be assumed with webhooks — see `standards/pr-review-guides/unstable-idempotency-key.md`)
- [ ] Does the consumer ignore unknown fields (Tolerant Reader)?
- [ ] Does the producer follow Expand/Contract for schema changes?

> **Applies during:** design review, code review, and any doc proposing a new integration. Flag webhook proposals without a queue-evaluation note at any of these stages.
