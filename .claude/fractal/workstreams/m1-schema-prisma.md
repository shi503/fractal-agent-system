# Workstream PRD: M1.1 — Prisma Schema + Seed

**Epic:** M1 — Core Data Model + Auth
**Feature Lead model:** haiku
**Dependencies:** none — execute first
**Estimated scope:** 4 files created/modified

---

## Goal

Define the complete Prisma schema for TaskFlow Phase 1 and produce a working migration + seed on a clean Postgres database. This schema is the single source of truth for all data models. Every subsequent workstream in M1–M4 depends on it being stable and correct.

---

## Acceptance Criteria

1. `npx prisma validate` passes with no errors
2. `npx prisma migrate dev --name init` succeeds against a local Postgres DB (or `npx prisma db push` for dev without migration files)
3. `npx prisma db seed` populates the DB with: 1 Organization, 1 Team, 1 Board, 3 Columns (Todo, In Progress, Done), 3 Issues distributed across columns
4. `lib/db.ts` exports a singleton Prisma client — no direct `new PrismaClient()` anywhere else
5. `.env.example` documents all required database environment variables with placeholder values
6. TypeScript: `npx tsc --noEmit` passes after schema generation (`npx prisma generate`)

---

## Data Model

### Required Models

```prisma
model Organization {
  id        String   @id @default(cuid())
  name      String
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
  teams     Team[]
}

model Team {
  id             String       @id @default(cuid())
  name           String
  organizationId String
  organization   Organization @relation(fields: [organizationId], references: [id])
  members        TeamMember[]
  boards         Board[]
  createdAt      DateTime     @default(now())
  updatedAt      DateTime     @updatedAt
}

model TeamMember {
  id        String     @id @default(cuid())
  teamId    String
  userId    String
  role      MemberRole @default(MEMBER)
  team      Team       @relation(fields: [teamId], references: [id])
  user      User       @relation(fields: [userId], references: [id])
  createdAt DateTime   @default(now())
  updatedAt DateTime   @updatedAt

  @@unique([teamId, userId])
}

model User {
  id            String       @id @default(cuid())
  name          String?
  email         String       @unique
  emailVerified DateTime?
  image         String?
  teamMembers   TeamMember[]
  assignedIssues Issue[]     @relation("AssignedIssues")
  createdIssues  Issue[]     @relation("CreatedIssues")
  comments      Comment[]
  accounts      Account[]
  sessions      Session[]
  createdAt     DateTime     @default(now())
  updatedAt     DateTime     @updatedAt
}

model Board {
  id        String    @id @default(cuid())
  name      String
  teamId    String
  team      Team      @relation(fields: [teamId], references: [id])
  columns   Column[]
  deletedAt DateTime?
  createdAt DateTime  @default(now())
  updatedAt DateTime  @updatedAt
}

model Column {
  id        String    @id @default(cuid())
  name      String
  order     Float
  boardId   String
  teamId    String
  board     Board     @relation(fields: [boardId], references: [id])
  issues    Issue[]
  deletedAt DateTime?
  createdAt DateTime  @default(now())
  updatedAt DateTime  @updatedAt
}

model Issue {
  id          String        @id @default(cuid())
  title       String
  description String?
  status      IssueStatus   @default(TODO)
  priority    IssuePriority @default(MEDIUM)
  order       Float
  boardId     String
  columnId    String
  teamId      String
  assigneeId  String?
  createdById String
  dueDate     DateTime?
  column      Column        @relation(fields: [columnId], references: [id])
  assignee    User?         @relation("AssignedIssues", fields: [assigneeId], references: [id])
  createdBy   User          @relation("CreatedIssues", fields: [createdById], references: [id])
  comments    Comment[]
  deletedAt   DateTime?
  createdAt   DateTime      @default(now())
  updatedAt   DateTime      @updatedAt
}

model Comment {
  id        String    @id @default(cuid())
  body      String
  issueId   String
  authorId  String
  teamId    String
  source    String?   // "human" | "agent" — for FRACTAL agent attribution
  agentId   String?   // FRACTAL agent identifier (Phase 2 full support, stub now)
  issue     Issue     @relation(fields: [issueId], references: [id])
  author    User      @relation(fields: [authorId], references: [id])
  deletedAt DateTime?
  createdAt DateTime  @default(now())
  updatedAt DateTime  @updatedAt
}

// Auth.js required models
model Account {
  id                String  @id @default(cuid())
  userId            String
  type              String
  provider          String
  providerAccountId String
  refresh_token     String?
  access_token      String?
  expires_at        Int?
  token_type        String?
  scope             String?
  id_token          String?
  session_state     String?
  user              User    @relation(fields: [userId], references: [id], onDelete: Cascade)

  @@unique([provider, providerAccountId])
}

model Session {
  id           String   @id @default(cuid())
  sessionToken String   @unique
  userId       String
  expires      DateTime
  user         User     @relation(fields: [userId], references: [id], onDelete: Cascade)
}

model VerificationToken {
  identifier String
  token      String   @unique
  expires    DateTime

  @@unique([identifier, token])
}

enum MemberRole {
  OWNER
  MEMBER
}

enum IssueStatus {
  TODO
  IN_PROGRESS
  IN_REVIEW
  DONE
  CANCELLED
}

enum IssuePriority {
  URGENT
  HIGH
  MEDIUM
  LOW
  NO_PRIORITY
}
```

### Notes
- `Comment.source` and `Comment.agentId` are stubs for Phase 2 agent attribution. Add fields now — do not leave them out.
- `teamId` is denormalized onto `Column`, `Issue`, `Comment` for RLS policy efficiency. It must match the parent board's teamId — enforce in application logic and Zod validation.
- Do NOT store any PHI fields. No `patientId`, `mrn`, `dob`, or clinical identifiers.

---

## File Manifest

### Write
- `prisma/schema.prisma` — full schema as specified above; update the datasource block to use `DATABASE_URL` and `DIRECT_URL`
- `prisma/seed.ts` — seed script: 1 org → 1 team → 1 user (owner) → 1 board → 3 columns (Todo/In Progress/Done) → 3 issues
- `lib/db.ts` — Prisma singleton client
- `.env.example` — document: `DATABASE_URL`, `DIRECT_URL`

### Do NOT touch
- `app/` — no UI changes in this workstream
- `lib/auth.ts` — auth is M1.2's responsibility
- Any existing files outside the manifest above

---

## Implementation Notes

### `lib/db.ts` pattern

**Important:** Prisma 6 generates the client to `app/generated/prisma` (set in `schema.prisma` generator output). Import from that path, not `@prisma/client`:

```typescript
import { PrismaClient } from '@/app/generated/prisma';

const globalForPrisma = globalThis as unknown as { prisma: PrismaClient };

export const db =
  globalForPrisma.prisma ??
  new PrismaClient({
    log: process.env.NODE_ENV === 'development' ? ['query', 'error', 'warn'] : ['error'],
  });

if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = db;
```

### `prisma.config.ts` datasource
The `prisma.config.ts` was auto-generated by `npx prisma init`. Update `prisma/schema.prisma` datasource to:
```prisma
datasource db {
  provider  = "postgresql"
  url       = env("DATABASE_URL")
  directUrl = env("DIRECT_URL")
}

generator client {
  provider = "prisma-client-js"
}
```

### Seed script
Use `ts-node` or `tsx` for seed execution. Add to `package.json`:
```json
"prisma": {
  "seed": "tsx prisma/seed.ts"
}
```
Install `tsx` as a dev dependency if not present: `npm install -D tsx`

---

## Session Protocol

1. Read `.claude/CLAUDE.md` (database conventions) and `.claude/fractal/STRATEGIST-taskflow.md` §4 before starting
2. Install `tsx`: `npm install -D tsx`
3. Add to `package.json` under a top-level `"prisma"` key: `{ "seed": "tsx prisma/seed.ts" }`
4. Write `prisma/schema.prisma` — validate with `npx prisma validate` before proceeding
5. Update `prisma.config.ts` to add `DIRECT_URL` support (see Implementation Notes)
6. Write `lib/db.ts`
7. Write `prisma/seed.ts`
8. Update `.env.example`
9. Run `npx prisma generate` — fix any TypeScript errors
10. Run `npx prisma migrate dev --name init` — DB credentials are configured, migration will apply
11. Run `npx prisma db seed` — verify seed populates successfully
12. Run `npx tsc --noEmit` — must pass before handoff
13. Emit `/handoff` when all acceptance criteria are met

**Important — Prisma 6 config:** This project uses `prisma.config.ts` (Prisma 6). The datasource URL is read from `prisma.config.ts` via `env("DATABASE_URL")`. The `prisma/schema.prisma` datasource block does NOT need a `directUrl` — that is handled in `prisma.config.ts`. To add direct URL support for migrations, update `prisma.config.ts`:
```typescript
datasource: {
  url: env("DATABASE_URL"),
  directUrl: env("DIRECT_URL"),
},
```
Also update `.env.example` to document both `DATABASE_URL` and `DIRECT_URL`.
