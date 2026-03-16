# PRD-XXX: [Feature Name]

> **Copy this template** for each new PRD. Save as `PRD-XXX-ShortName.md` in `.SPECS/PRD/`.
> Delete this note block before saving the real PRD.

---

## Meta

| Field | Value |
|-------|-------|
| Status | Draft / Approved / In Progress / Done |
| Priority | P0 / P1 / P2 |
| Owner | [Name] |
| Target | [Date] |
| FRACTAL Blueprint | `.claude/FRACTAL/BLUEPRINT-PRD-XXX-ShortName.yaml` (if applicable) |
| Spec Ref | [Link to related design doc or previous PRD] |

---

## Problem

> 1-2 sentences: What problem does this solve? Who has this problem?

---

## Success Criteria

- [ ] Measurable outcome 1 (specific, binary pass/fail)
- [ ] Measurable outcome 2
- [ ] Measurable outcome 3

---

## Scope

### In Scope

- Feature A
- Feature B

### Out of Scope

- Explicitly excluded item (say why — prevents scope creep)

### Dependencies

- [PRD-XXX](link) — Required before this (say why)
- External API / Service
- Database migration X must be deployed first

---

## User Stories

### US-1: [Story Title]

**As a** [persona], **I want** [action], **so that** [outcome].

**Acceptance Criteria:**

- [ ] Given X, when Y, then Z
- [ ] Given X, when Y, then Z

### US-2: [Story Title]

**As a** [persona], **I want** [action], **so that** [outcome].

**Acceptance Criteria:**

- [ ] Given X, when Y, then Z

---

## Technical Approach

> Brief technical direction — enough for the Architect to decompose into workstreams.

### Key Files

| File | Change Type | Notes |
|------|------------|-------|
| `lib/actions/issues.ts` | Modify | Add `archiveIssue` Server Action |
| `components/issues/issue-card.tsx` | Modify | Add archive button |
| `prisma/schema.prisma` | Modify | Add `archivedAt DateTime?` to Issue model |
| `prisma/migrations/...` | Create | New migration for schema change |

### API / Server Actions (if applicable)

| Type | Name / Path | Purpose |
|------|-------------|---------|
| Server Action | `lib/actions/issues.ts → archiveIssue()` | Soft-archive an issue |
| Server Action | `lib/actions/issues.ts → restoreIssue()` | Restore archived issue |
| Route Handler | `app/api/webhooks/stripe/route.ts` | Handle Stripe billing events |

### Database Changes (if applicable)

| Table | Change | Migration Required? |
|-------|--------|-------------------|
| `Issue` | Add `archivedAt DateTime?` | Yes |
| `Board` | Add `settings Json?` | Yes |

> **Migration rule:** All schema changes go through `npx prisma migrate dev`. Never hand-edit migration files. Migration must be idempotent (`prisma migrate deploy` safe to re-run).

### Zod Schemas (if applicable)

```typescript
// lib/validations/issue.ts — add new schemas here
export const ArchiveIssueSchema = z.object({
  issueId: z.string().min(1),
  reason: z.string().optional(),
});
```

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Risk 1 | High/Med/Low | Plan |
| Pagination for large issue lists | Medium | Use Prisma `cursor`-based pagination, not `offset` |

---

## Open Questions

- [ ] Question 1? → Who decides / by when?
- [ ] Question 2?

---

## Verification Checklist

> Complete before setting Status → Done. Binary pass/fail gates.
> **AI Agents:** Include the output of each check in HANDOFF.md Verification Evidence.

### Compilation

- [ ] `npm run build` passes with zero TypeScript errors
- [ ] `npx tsc --noEmit` passes with zero errors
- [ ] No `console.log` / `console.warn` left in changed files
- [ ] No forbidden patterns introduced (see CLAUDE.md Forbidden Patterns table)

### Lint & Format

- [ ] `npm run lint` passes with zero warnings or errors
- [ ] `npm run format:check` passes (no formatting issues)

### Visual / Functional

- [ ] Feature works in light theme
- [ ] Feature works in dark theme (all colors via CSS variables, no hardcoded hex)
- [ ] No console errors on route navigation
- [ ] Mobile layout acceptable (if applicable)
- [ ] Loading states shown for async operations
- [ ] Error states handled and surfaced to UI (not silent failures)

### Database / Backend

- [ ] `npx prisma db push` (dev) or `npx prisma migrate dev` (with migration file) succeeds
- [ ] New DB tables/columns with `organization_id` have corresponding RLS policies
- [ ] New Server Actions verify auth before any DB operation
- [ ] Zod validation added for all new Server Action inputs
- [ ] Error messages returned to client are user-safe (no Prisma internals, no stack traces)

### Security (for compliance-gated projects)

- [ ] No secrets, credentials, or PHI in any new log statement
- [ ] New environment variables documented in `.env.example`
- [ ] PHI does not appear in any URL path or analytics event (if applicable)

### Testing

- [ ] Unit tests added for new Server Actions (unauthenticated + invalid input + success paths)
- [ ] Unit tests added for non-trivial component logic
- [ ] `npm run test:run` passes with no regressions
- [ ] Playwright E2E test added for critical user flows (if applicable)
- [ ] `npm run test:e2e` passes

---

## References

- [Design file or Figma link]
- [Related PRD](link)
- `docs/frontend-dev-guide.md` — Component patterns and anti-patterns
- `docs/testing-patterns.md` — Server Action and component test patterns
- `docs/soc2-compliance.md` — Security and compliance checklist
