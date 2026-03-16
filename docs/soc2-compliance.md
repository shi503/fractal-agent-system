# SOC2 / Enterprise Compliance Guardrails

**Audience:** Engineers, AI agents, and security reviewers.
**Status:** Canonical — reflects compliance requirements for enterprise and healthcare SaaS deployments.
**Last updated:** 2026-03-16

> This document is referenced from `CLAUDE.md`'s compliance section. For projects with SOC2, BAA, or HIPAA-adjacent requirements, these guardrails apply to ALL code written by humans and AI agents alike.

---

## Who This Applies To

- **Always:** Any project that handles data from multiple organizations (multi-tenant SaaS)
- **Healthcare projects:** Any project touching Protected Health Information (PHI) as defined by HIPAA
- **Enterprise projects:** Any project with a signed BAA, SOC2 Type II audit scope, or enterprise customer SLAs

If your project fits any of these categories, uncomment the compliance section in `CLAUDE.md` and ensure all agents receive this document in their context.

---

## Non-Negotiables

These rules cannot be traded away for speed, convenience, or developer experience.

### 1. No Sensitive Data in Outputs

**Rule:** Never log, print, or emit credentials, tokens, API keys, PHI, PII, or document contents in any observable channel (logs, traces, error messages, metrics, analytics events, browser console).

```typescript
// ❌ NEVER — logs the raw session token
console.log("Session:", session);

// ❌ NEVER — exposes the user's name in a debug log
console.log(`Processing document for ${user.name}: ${document.content}`);

// ✅ CORRECT — log only IDs and metadata
console.log(`Processing document id=${document.id} org=${org.id}`);

// ✅ CORRECT — log event type, not payload content
console.log(`Webhook received: type=${event.type} id=${event.id}`);
```

**PHI Definition (HIPAA Safe Harbor):** Names, dates (other than year), geographic subdivisions smaller than state, phone numbers, fax numbers, email addresses, SSN, medical record numbers, health plan beneficiary numbers, account numbers, certificate/license numbers, vehicle identifiers, device identifiers, URLs, IP addresses, biometric identifiers, full-face photographs, any other unique identifying number/code.

**Rule for PHI:** PHI belongs in the database with encryption at rest and in transit. It does NOT belong in:
- Log files
- Error messages returned to clients
- Analytics events (Amplitude, Mixpanel, GA4)
- Sentry/Datadog traces (scrub before sending)
- URL paths (use UUIDs; MRN/SSN/name are PHI)
- localStorage or sessionStorage (unencrypted client storage)

### 2. Zero-Touch Configuration

**Rule:** All environment-specific values — URLs, database connection strings, API keys, feature flags, log levels, secrets — must come from environment variables or an approved secret manager. Never hardcode.

```typescript
// ❌ FORBIDDEN
const db = new PrismaClient({ datasources: { db: { url: "postgresql://..." } } });

// ✅ CORRECT — from environment variable
const db = new PrismaClient();  // Prisma reads DATABASE_URL from env automatically

// ❌ FORBIDDEN
const stripeKey = "sk_live_abc123";

// ✅ CORRECT
const stripeKey = process.env.STRIPE_SECRET_KEY!;
```

**`.env` files:** Never commit real `.env` files. Maintain `.env.example` with placeholder values only.

### 3. Observability Required

**Rule:** Emit structured logs with consistent fields. Provide health check endpoints. Propagate request IDs.

```typescript
// Structured log format (minimum required fields):
{
  "ts": "2026-03-16T10:30:00.000Z",  // ISO 8601
  "level": "info",                    // debug | info | warn | error
  "service": "portal-api",
  "request_id": "req_abc123",
  "msg": "Issue created",
  "issue_id": "cuid_xyz",            // IDs only — no content
  "org_id": "org_456"
}

// Health check endpoint (GET /health):
{ "status": "ok", "db": "ok", "uptime": 3600 }
```

**Tracing:** If using Sentry, Datadog, or similar: configure scrubbing rules to remove PHI from error payloads before transmission. Never let raw request bodies appear in traces.

### 4. Deployability

**Rule:** Startup must run idempotent database migrations. Fail fast if migrations fail. Downgrades must be possible without destroying state.

```typescript
// In your startup script / Docker entrypoint:
// 1. Run migrations
await exec("npx prisma migrate deploy");
// 2. Fail fast if this returns non-zero — do NOT start the server
// 3. Only then start the application

// ✅ Idempotent migrations: Prisma migrate deploy is safe to re-run
// ✅ Soft deletes enable rollback: deletedAt = null means not deleted, set it to restore
// ❌ NEVER: hard-delete data during a migration (data loss on rollback)
```

### 5. Authentication First

**Rule:** Every API route and Server Action must verify auth before touching the database. No exceptions.

```typescript
// ✅ Pattern — auth check always first
export async function updateIssue(id: string, data: unknown) {
  const session = await auth();
  if (!session?.user) return { error: "Unauthorized" };  // ← before ANY db call

  // ... Zod validation
  // ... database operation
}

// ❌ Pattern — auth check after data access
export async function updateIssue(id: string, data: unknown) {
  const issue = await db.issue.findFirst({ where: { id } });  // ← data before auth check
  const session = await auth();
  // ...
}
```

---

## DO

- **Use RLS on all multi-tenant tables.** Every table with `organization_id` must have a Row Level Security policy in Supabase. Application-level checks are defense-in-depth, not the primary enforcement.
- **Log security-relevant operations** with actor ID and timestamp — login, logout, API key creation/revocation, data export, permission changes. Log the action, not the content.
- **Run dependency audit** (`npm audit`) before merging any PR that adds or upgrades dependencies.
- **Use SemVer or date-hash tags** for releases. Keep one consistent tag per release set.
- **Include compliance scan results** in HANDOFF.md Verification Evidence when relevant.
- **Rotate secrets** on a schedule. Treat any leaked secret as compromised immediately.
- **Use parameterized queries.** Prisma handles this automatically — never use template string SQL.

---

## DON'T

- **Don't use bare commit hashes as the only version identifier** (e.g., `build-123` or sha-only tags).
- **Don't introduce hidden dependencies between services.** Make all dependencies explicit and checkable in health checks.
- **Don't share stateful infrastructure across unrelated components** unless explicitly isolated (tenancy, quotas, failure domains).
- **Don't store session tokens in localStorage** without `httpOnly` cookie protection. Supabase Auth uses cookies with `httpOnly` by default.
- **Don't allow org A to query org B's data** — verify `organization_id` in every query, not just the top-level check.
- **Don't return internal error messages to clients.** Catch Prisma errors, log them server-side, return user-safe messages.

```typescript
// ❌ Leaks Prisma internals to client
return NextResponse.json({ error: err.message });  // "Unique constraint failed on field [email]"

// ✅ User-safe, no internals
return NextResponse.json({ error: "That email is already in use" });
```

---

## NEVER

- **Never ship code that can leak secrets/PHI to logs, traces, errors, or metrics.**
- **Never start the service if schema migrations are incompatible or failed.**
- **Never require container destruction/redeploy to perform a version rollback.**
- **Never commit `.env` files** with real credentials to git (even to private repos).
- **Never disable or weaken authentication/authorization checks** to "make something work faster."
- **Never put PHI in URL paths.** Use opaque UUIDs for all resource identifiers. Display-only identifiers (MRN, name) must not appear in URLs, logs, or referrer headers.
- **Never use `// @ts-ignore` to silence a type error that might be hiding a security issue.**

---

## FRACTAL Agent Instructions

When working on this codebase as a FRACTAL agent (Feature Lead, Sub-Agent, or Architect), include these checks in your HANDOFF.md Verification Evidence table:

### Layer 1 — Deterministic Gates (Agents Must Run These)

```bash
# Build passes with zero errors
npm run build 2>&1 | tail -5

# TypeScript clean
npx tsc --noEmit 2>&1 | tail -10

# No console.log in changed files
git diff --name-only HEAD~1 | xargs grep -l "console\." 2>/dev/null

# No hardcoded secrets (basic check)
git diff HEAD~1 | grep -E "(password|secret|key|token)\s*=\s*['\"][^'\"]{8,}" | grep -v "example\|placeholder\|YOUR_"
```

### Security Checklist (Per Workstream)

Before marking any workstream COMPLETE, verify:

- [ ] `npm run build` passes with zero TypeScript errors
- [ ] No `console.log`, `console.warn`, or `console.error` in changed files (except error boundaries)
- [ ] No secrets, credentials, or PHI in any new log statement
- [ ] New DB tables have RLS policies if they contain `organization_id`
- [ ] New Server Actions verify auth before any DB operation
- [ ] New API routes validate auth and input before processing
- [ ] Error messages returned to clients are user-safe (no Prisma internals, no stack traces)
- [ ] New environment variables are documented in `.env.example`
- [ ] PHI does not appear in any URL path, log statement, or analytics event

### PHI Handling in Clinical Features

For features that process clinical documents or patient data:

| Data Type | Storage | Display | Logs |
|-----------|---------|---------|------|
| Document content | DB (encrypted at rest) | In-app only | NEVER |
| Patient name | DB | In-app only | NEVER |
| MRN / ID numbers | DB | In-app only (`local_mrn` display-only) | NEVER in URLs |
| Extracted findings | DB with citation links | In-app with provenance | IDs only |
| Session tokens | Auth provider (httpOnly cookie) | Never displayed | NEVER |
| API keys | DB (hashed, SHA-256) | Shown once at creation | NEVER |

---

## Compliance Context by Deployment Tier

| Tier | Context | Key Requirements |
|------|---------|-----------------|
| **Dev / Staging** | Internal team, no real patient data | Secrets in `.env.local`, no production credentials |
| **Enterprise trial** | Real org data, no PHI | BAA not yet signed; no clinical documents |
| **Production (BAA signed)** | Real patient data, PHI possible | Full HIPAA controls; SOC2 audit scope begins |
| **SOC2 Type II** | Formal audit | All controls documented; evidence collected quarterly |

**Compliance is not a binary checkbox.** It expands with each deployment tier. Start enforcing the basics (secrets, logging, auth) from day one, even in dev.

---

## References

- HIPAA Safe Harbor identifiers: 45 CFR § 164.514(b)(2)
- OWASP Top 10 for web application security
- SOC2 Trust Services Criteria: Security (CC6, CC7), Availability (A1), Confidentiality (C1)
- `CLAUDE.md` — project-level security conventions
- `docs/platform-strategy.md` — Tier 1 absolute rules for multi-tenant architecture
