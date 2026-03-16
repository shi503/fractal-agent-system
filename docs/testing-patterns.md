# Testing Patterns — TaskFlow

**Audience:** Engineers and AI agents writing tests for this codebase.
**Status:** Canonical — patterns drawn from the test files in `src/`.
**Last updated:** 2026-03-16

---

## Quick Facts

| Topic | Answer |
|-------|--------|
| Test runner | **Vitest** (via `npm run test`) |
| Component testing | **React Testing Library** (`@testing-library/react`) |
| E2E testing | **Playwright** (via `npm run test:e2e`) |
| `vi.fn()` / `vi.mock()` | Available **globally** — no import needed in spec files |
| Test file naming | `<component-or-util>.test.ts(x)` co-located next to the file under test |
| Assertion library | Vitest `expect` — identical API to Jest |
| `describe` / `it` / `beforeEach` | Global — no import needed |
| Prisma in tests | Always mock via `vi.mock('@/lib/db')` — never hit a real DB |
| Auth in tests | Mock `auth()` from `@/lib/auth` — never use real sessions |

---

## Pattern 1: Server Action Test (Zod validation + Prisma mock)

```typescript
// lib/actions/issues.test.ts
import { createIssue } from "./issues";

// Mock Prisma — never hit a real database in unit tests
vi.mock("@/lib/db", () => ({
  db: {
    issue: {
      create: vi.fn(),
      findFirst: vi.fn(),
    },
  },
}));

// Mock Auth.js
vi.mock("@/lib/auth", () => ({
  auth: vi.fn(),
}));

// Mock Next.js cache invalidation
vi.mock("next/cache", () => ({
  revalidatePath: vi.fn(),
}));

import { db } from "@/lib/db";
import { auth } from "@/lib/auth";

describe("createIssue", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns error when user is not authenticated", async () => {
    vi.mocked(auth).mockResolvedValue(null);

    const formData = new FormData();
    formData.set("title", "New Issue");
    formData.set("boardId", "board-1");

    const result = await createIssue(formData);
    expect(result).toEqual({ error: "Unauthorized" });
    expect(db.issue.create).not.toHaveBeenCalled();
  });

  it("returns validation error when title is missing", async () => {
    vi.mocked(auth).mockResolvedValue({
      user: { id: "user-1", teamId: "team-1" },
    } as any);

    const formData = new FormData();
    formData.set("boardId", "board-1");
    // title is missing

    const result = await createIssue(formData);
    expect(result).toHaveProperty("error");
    expect(db.issue.create).not.toHaveBeenCalled();
  });

  it("creates issue and returns issueId on success", async () => {
    vi.mocked(auth).mockResolvedValue({
      user: { id: "user-1", teamId: "team-1" },
    } as any);
    vi.mocked(db.issue.create).mockResolvedValue({
      id: "issue-abc",
      boardId: "board-1",
    } as any);

    const formData = new FormData();
    formData.set("title", "Fix the login bug");
    formData.set("boardId", "board-1");

    const result = await createIssue(formData);
    expect(result).toEqual({ success: true, issueId: "issue-abc" });
    expect(db.issue.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          title: "Fix the login bug",
          teamId: "team-1",
          createdById: "user-1",
        }),
      })
    );
  });
});
```

Key rules:
- Always mock `@/lib/db` and `@/lib/auth` — never hit real services in unit tests
- Mock `next/cache` to avoid "revalidatePath is not a function" errors
- Test the three critical paths: unauthenticated, invalid input, success

---

## Pattern 2: React Component Test (RTL)

```typescript
// components/issues/status-badge.test.tsx
import { render, screen } from "@testing-library/react";
import { StatusBadge } from "./status-badge";

describe("StatusBadge", () => {
  it("renders correct label for IN_PROGRESS status", () => {
    render(<StatusBadge status="IN_PROGRESS" />);
    expect(screen.getByText("In Progress")).toBeInTheDocument();
  });

  it("renders correct label for DONE status", () => {
    render(<StatusBadge status="DONE" />);
    expect(screen.getByText("Done")).toBeInTheDocument();
  });

  it("applies destructive class for BLOCKED status", () => {
    render(<StatusBadge status="BLOCKED" />);
    const badge = screen.getByText("Blocked");
    expect(badge.closest("[class]")).toHaveClass("destructive");
  });
});
```

### Component test with form submission

```typescript
// components/issues/create-issue-form.test.tsx
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CreateIssueForm } from "./create-issue-form";

// Mock the Server Action
vi.mock("@/lib/actions/issues", () => ({
  createIssue: vi.fn(),
}));

import { createIssue } from "@/lib/actions/issues";

describe("CreateIssueForm", () => {
  it("calls createIssue with form data on submit", async () => {
    const user = userEvent.setup();
    vi.mocked(createIssue).mockResolvedValue({ success: true, issueId: "new-1" });

    render(<CreateIssueForm boardId="board-1" />);

    await user.type(screen.getByPlaceholderText("Issue title"), "Fix login bug");
    await user.click(screen.getByRole("button", { name: "Create Issue" }));

    await waitFor(() => {
      expect(createIssue).toHaveBeenCalled();
    });
  });

  it("shows validation error when title is empty", async () => {
    const user = userEvent.setup();
    vi.mocked(createIssue).mockResolvedValue({
      error: { title: ["Title is required"] },
    });

    render(<CreateIssueForm boardId="board-1" />);
    await user.click(screen.getByRole("button", { name: "Create Issue" }));

    await waitFor(() => {
      expect(screen.getByText("Title is required")).toBeInTheDocument();
    });
  });
});
```

Key rules:
- Use `userEvent` for realistic user interactions (not `fireEvent` — too low-level)
- `waitFor` wraps assertions that depend on async state updates
- Mock Server Actions with `vi.mock()` — don't test the action itself in component tests

---

## Pattern 3: Zustand Store Test

```typescript
// lib/stores/board.test.ts
import { useBoardStore } from "./board";
import { type Issue } from "@prisma/client";

// Reset store between tests to avoid state bleed
beforeEach(() => {
  useBoardStore.setState({
    activeIssue: null,
    overColumnId: null,
    isDragging: false,
  });
});

describe("useBoardStore", () => {
  const mockIssue = {
    id: "issue-1",
    title: "Fix the bug",
    status: "TODO",
  } as unknown as Issue;

  it("starts with no active issue", () => {
    const { activeIssue, isDragging } = useBoardStore.getState();
    expect(activeIssue).toBeNull();
    expect(isDragging).toBe(false);
  });

  it("sets isDragging to true when setActiveIssue is called", () => {
    useBoardStore.getState().setActiveIssue(mockIssue);
    const { activeIssue, isDragging } = useBoardStore.getState();
    expect(activeIssue).toEqual(mockIssue);
    expect(isDragging).toBe(true);
  });

  it("clears active issue and isDragging when setActiveIssue(null) is called", () => {
    useBoardStore.getState().setActiveIssue(mockIssue);
    useBoardStore.getState().setActiveIssue(null);
    const { activeIssue, isDragging } = useBoardStore.getState();
    expect(activeIssue).toBeNull();
    expect(isDragging).toBe(false);
  });
});
```

Key rules:
- Use `useBoardStore.getState()` to read/write state directly in tests (no React hook context needed)
- Use `useBoardStore.setState()` in `beforeEach` to reset between tests
- Test state transitions, not implementation details

---

## Pattern 4: Auth-Gated Route Test

```typescript
// app/(dashboard)/board/[boardId]/page.test.tsx
import { render, screen } from "@testing-library/react";
import BoardPage from "./page";

vi.mock("@/lib/auth", () => ({
  auth: vi.fn(),
}));
vi.mock("next/navigation", () => ({
  redirect: vi.fn(),
  notFound: vi.fn(),
}));
vi.mock("@/lib/queries/boards", () => ({
  getBoardById: vi.fn(),
  getIssuesByBoard: vi.fn(),
}));

import { auth } from "@/lib/auth";
import { redirect, notFound } from "next/navigation";
import { getBoardById, getIssuesByBoard } from "@/lib/queries/boards";

describe("BoardPage", () => {
  it("redirects to /login when unauthenticated", async () => {
    vi.mocked(auth).mockResolvedValue(null);

    const params = Promise.resolve({ boardId: "board-1" });
    // RSC: render the async component and await it
    await BoardPage({ params });

    expect(redirect).toHaveBeenCalledWith("/login");
  });

  it("calls notFound() when board does not exist", async () => {
    vi.mocked(auth).mockResolvedValue({
      user: { id: "user-1", teamId: "team-1" },
    } as any);
    vi.mocked(getBoardById).mockResolvedValue(null);

    const params = Promise.resolve({ boardId: "nonexistent" });
    await BoardPage({ params });

    expect(notFound).toHaveBeenCalled();
  });

  it("renders board name when board exists", async () => {
    vi.mocked(auth).mockResolvedValue({
      user: { id: "user-1", teamId: "team-1" },
    } as any);
    vi.mocked(getBoardById).mockResolvedValue({
      id: "board-1",
      name: "Sprint 42",
      columns: [],
    } as any);
    vi.mocked(getIssuesByBoard).mockResolvedValue([]);

    const params = Promise.resolve({ boardId: "board-1" });
    const jsx = await BoardPage({ params });
    render(jsx);

    expect(screen.getByText("Sprint 42")).toBeInTheDocument();
  });
});
```

Key rules:
- RSC async components can be tested by awaiting the component function itself
- Mock `next/navigation` to assert on `redirect` and `notFound` calls
- Always test the unauthenticated path first

---

## Pattern 5: Playwright E2E Test

```typescript
// e2e/board.spec.ts
import { test, expect } from "@playwright/test";

// Reuse auth state across tests — set up once in global setup
test.use({ storageState: "e2e/.auth/user.json" });

test.describe("Board — issue management", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/board/test-board-id");
    await expect(page.getByRole("heading", { name: "Test Board" })).toBeVisible();
  });

  test("creates a new issue via Cmd+K", async ({ page }) => {
    await page.keyboard.press("Meta+k");
    await expect(page.getByPlaceholder("Type a command…")).toBeVisible();

    await page.keyboard.type("create issue");
    await page.getByRole("option", { name: "Create Issue" }).click();

    await page.getByPlaceholder("Issue title").fill("Fix the login bug");
    await page.getByRole("button", { name: "Create Issue" }).click();

    await expect(page.getByText("Fix the login bug")).toBeVisible();
  });

  test("drag issue from Backlog to In Progress", async ({ page }) => {
    const issueCard = page.getByText("Fix the login bug").locator("..");
    const inProgressColumn = page.getByRole("region", { name: "In Progress" });

    await issueCard.dragTo(inProgressColumn);

    await expect(
      inProgressColumn.getByText("Fix the login bug")
    ).toBeVisible();
  });

  test("keyboard shortcut C opens create issue form", async ({ page }) => {
    await page.keyboard.press("c");
    await expect(page.getByRole("dialog", { name: "Create Issue" })).toBeVisible();
  });
});

// Global setup: log in once and save auth state
// e2e/global-setup.ts
import { chromium, type FullConfig } from "@playwright/test";

async function globalSetup(config: FullConfig) {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  await page.goto("http://localhost:3000/login");
  await page.fill('[name="email"]', process.env.TEST_USER_EMAIL!);
  await page.fill('[name="password"]', process.env.TEST_USER_PASSWORD!);
  await page.click('[type="submit"]');
  await page.waitForURL("**/board/**");

  await page.context().storageState({ path: "e2e/.auth/user.json" });
  await browser.close();
}

export default globalSetup;
```

Key rules:
- Store auth state in `e2e/.auth/user.json` so login happens once, not per test
- Use `storageState` to reuse auth across test files
- Test keyboard shortcuts — they're a core differentiator for TaskFlow
- `dragTo` for drag-and-drop; it uses mouse events that dnd-kit responds to

---

## What to Test

| Thing | Test it when |
|-------|-------------|
| Server Action validation | Required: test unauthenticated + invalid input + success paths |
| Component rendering from props | Conditional renders, status variants, priority colors |
| Server Action mock interactions | `vi.fn()` called with expected args |
| Route guards (redirect/notFound) | Auth and 404 paths |
| Zustand state transitions | State changes from drag start/end |
| E2E: Critical user flows | Signup → first board, create issue, drag issue, Cmd+K |

**Do NOT test:**
- shadcn/ui internal component behavior (they have their own tests)
- CSS class presence (brittle; test visible text or accessible role instead)
- Next.js framework internals (routing, cache invalidation — test effects, not mechanisms)
- Pure type-only code (TypeScript already verifies at compile time)

---

## Static Analysis & Quality Gates

These checks are cheaper than unit tests and should run first.

### Quality Gate Sequence (cheapest → most expensive)

```bash
# 1. Format check — ~1s, catches whitespace/formatting issues
npm run format:check

# 2. Lint — ~5s, catches common anti-patterns
npm run lint

# 3. TypeScript — ~10s, catches type errors
npx tsc --noEmit

# 4. Unit tests — ~20s, catches logic regressions
npm run test:run

# 5. Build — ~30s, catches Next.js-specific errors (missing exports, bad imports)
npm run build

# 6. E2E — ~2min, catches integration failures (run in CI only)
npm run test:e2e
```

### What ESLint Enforces

Key rules active in this project (via `eslint-config-next`):
- No unused imports or variables
- No `any` type (via `@typescript-eslint/no-explicit-any`)
- Tailwind class ordering (`eslint-plugin-tailwindcss`)
- React hooks rules (no hooks in non-component functions)
- No `console.log` in production code (`no-console`)
- Import order consistency

Run `npm run lint:fix` to auto-correct what ESLint can fix.

### Prisma Schema Contract Validation

Prisma infers TypeScript types from `schema.prisma`. `tsc --noEmit` catches insert/query shape mismatches at compile time:

```typescript
// schema.prisma defines: issue.title as String (not null)
// This TypeScript error fires before any test runs:
await db.issue.create({
  data: {
    boardId: "board-1",
    // title omitted → TS error: "Property 'title' is missing"
  },
});
```

No additional runtime schema tests needed — if `tsc` passes, the Prisma shape is correct.

---

## Diagnosing Common Test Failures

| Symptom | Cause | Fix |
|---------|-------|-----|
| `auth is not a function` | `@/lib/auth` not mocked | Add `vi.mock("@/lib/auth", ...)` at top of test file |
| `Cannot find module '@/lib/db'` | Path alias not configured for Vitest | Add `resolve.alias` in `vitest.config.ts` |
| `revalidatePath is not a function` | `next/cache` not mocked | Add `vi.mock("next/cache", ...)` |
| `redirect is not a function` | `next/navigation` not mocked | Add `vi.mock("next/navigation", ...)` |
| Component renders empty / no elements | RSC async component not awaited | `const jsx = await PageComponent(props); render(jsx)` |
| E2E auth fails | `e2e/.auth/user.json` stale or missing | Run `npm run test:e2e:setup` to regenerate auth state |
| Drag-and-drop E2E doesn't work | `dragTo` not triggering dnd-kit | Use `page.mouse` with slow drag simulation; see Playwright dnd-kit docs |
| Zustand state persists between tests | Store not reset in `beforeEach` | Call `useMyStore.setState({ ...initialState })` in `beforeEach` |
| `vi.fn()` not reset between tests | Mock not cleared | Add `vi.clearAllMocks()` to `beforeEach` |

---

## Vitest Config Reference

```typescript
// vitest.config.ts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tsconfigPaths from "vite-tsconfig-paths";

export default defineConfig({
  plugins: [react(), tsconfigPaths()],
  test: {
    environment: "jsdom",
    globals: true,                          // vi.fn(), describe, it, etc. without imports
    setupFiles: ["./vitest.setup.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text", "lcov"],
    },
  },
});
```

```typescript
// vitest.setup.ts
import "@testing-library/jest-dom";         // adds .toBeInTheDocument(), .toHaveClass(), etc.
```
