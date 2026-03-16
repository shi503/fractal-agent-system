# Frontend Developer Guide — TaskFlow

**Audience:** Engineers and AI agents writing Next.js code for this codebase.
**Status:** Canonical — reflects confirmed patterns from the live codebase.
**Last updated:** 2026-03-16

> Start here before reading CLAUDE.md. This guide shows **what we actually do**, with real patterns and copy-paste examples.

---

## Top 10 Facts (Read These First)

| # | Rule | Why it breaks when violated |
|---|------|----------------------------|
| 1 | Default to Server Components. Only add `"use client"` when you need state, effects, or event handlers | Without this, you ship unnecessary JS to the browser and lose RSC performance benefits |
| 2 | All data mutations go through Server Actions in `lib/actions/`. Never `fetch('/api/')` from a form | `fetch()` loopback calls bypass auth context and add unnecessary round-trips |
| 3 | Always validate Server Action inputs with Zod before touching Prisma | Raw `formData` is user input — never trust it |
| 4 | Use **shadcn/ui tokens** only (`--card`, `--primary`, etc.) — never hardcode hex colors | Hardcoded colors break dark mode; CSS vars adapt automatically |
| 5 | Prisma queries belong in `lib/queries/` (for RSC) or `lib/actions/` (for mutations) — never in Client Components | Client Components are sent to the browser; DB queries there leak connection strings |
| 6 | Board drag-and-drop state lives in Zustand (`lib/stores/board.ts`) — not in component state | `useState` in parent causes full re-renders during drag; Zustand is granular |
| 7 | Files stay under 300 lines — extract components, hooks, or utilities when larger | Large files are hard for FRACTAL agents to reason about and cause context drift |
| 8 | Use `revalidatePath` or `revalidateTag` after every mutation — never force full page reload | RSC cache invalidation is how mutations propagate to the UI |
| 9 | `process.env.*` is server-only. `NEXT_PUBLIC_*` is the only client-safe env pattern | Non-public env vars in Client Components are silently `undefined` in production |
| 10 | Never log user content, PII, or session tokens | Logs are observable by your infra team; keep them clean |

---

## Component Anatomy (Copy This)

### Server Component (default for all data-fetching pages)

```typescript
// app/(dashboard)/board/[boardId]/page.tsx

import { auth } from "@/lib/auth";
import { getBoardById, getIssuesByBoard } from "@/lib/queries/boards";
import { redirect, notFound } from "next/navigation";
import { BoardView } from "@/components/board/board-view";

interface BoardPageProps {
  params: Promise<{ boardId: string }>;
}

export default async function BoardPage({ params }: BoardPageProps) {
  // 1. Auth check — always first in page RSCs
  const session = await auth();
  if (!session?.user) redirect("/login");

  const { boardId } = await params;

  // 2. Data fetch — direct Prisma via lib/queries/
  const board = await getBoardById(boardId, session.user.teamId);
  if (!board) notFound();

  const issues = await getIssuesByBoard(boardId);

  // 3. Render — pass data to client components that need interactivity
  return (
    <div className="flex h-full flex-col">
      <header className="border-b border-border px-6 py-4">
        <h1 className="text-lg font-semibold text-foreground">{board.name}</h1>
      </header>
      <BoardView board={board} initialIssues={issues} />
    </div>
  );
}
```

### Client Component (only when interactivity is needed)

```typescript
// components/board/issue-card.tsx
"use client";

import { useState } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { StatusBadge } from "@/components/issues/status-badge";
import { type Issue } from "@prisma/client";

interface IssueCardProps {
  issue: Issue;
  onStatusChange: (issueId: string, status: string) => void;
}

export function IssueCard({ issue, onStatusChange }: IssueCardProps) {
  const [isEditing, setIsEditing] = useState(false);

  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: issue.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className={`rounded-md border border-border bg-card p-3 shadow-sm cursor-grab
        ${isDragging ? "opacity-50 ring-2 ring-primary" : ""}`}
    >
      <p className="text-sm font-medium text-foreground">{issue.title}</p>
      <StatusBadge status={issue.status} />
    </div>
  );
}
```

### Form with Server Action

```typescript
// components/issues/create-issue-form.tsx
"use client";

import { useActionState } from "react";
import { createIssue } from "@/lib/actions/issues";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const initialState = { error: null, success: false };

export function CreateIssueForm({ boardId }: { boardId: string }) {
  const [state, action, isPending] = useActionState(createIssue, initialState);

  return (
    <form action={action} className="flex flex-col gap-3">
      <input type="hidden" name="boardId" value={boardId} />
      <Input
        name="title"
        placeholder="Issue title"
        className="bg-background"
        required
      />
      {state.error && (
        <p className="text-sm text-destructive">{state.error.title?.[0]}</p>
      )}
      <Button type="submit" disabled={isPending}>
        {isPending ? "Creating…" : "Create Issue"}
      </Button>
    </form>
  );
}
```

---

## Design Tokens (shadcn/ui — Use These)

All values come from CSS custom properties in `app/globals.css`. Dark mode values are automatically applied via `.dark` class on `<html>`.

### Core Tokens

| Token | Use For |
|-------|---------|
| `--background` | Page background (`bg-background`) |
| `--foreground` | Primary text (`text-foreground`) |
| `--card` | Card/panel surfaces (`bg-card`) |
| `--card-foreground` | Text inside cards (`text-card-foreground`) |
| `--primary` | Brand buttons, links, CTAs (`bg-primary`) |
| `--primary-foreground` | Text/icons on primary bg (`text-primary-foreground`) |
| `--secondary` | Secondary buttons, chips (`bg-secondary`) |
| `--secondary-foreground` | Text on secondary bg |
| `--muted` | Subtle backgrounds, code blocks (`bg-muted`) |
| `--muted-foreground` | Placeholder text, captions (`text-muted-foreground`) |
| `--accent` | Hover states, selected rows (`bg-accent`) |
| `--border` | Dividers, input borders (`border-border`) |
| `--input` | Input element borders (`border-input`) |
| `--ring` | Focus ring (`ring-ring`) |
| `--destructive` | Error states, danger buttons (`bg-destructive`) |
| `--destructive-foreground` | Text on destructive bg |

### Tailwind Usage

```html
<!-- Backgrounds -->
<div class="bg-background">           <!-- page background -->
<div class="bg-card">                 <!-- card surface -->
<div class="bg-muted">                <!-- subtle bg, sidebars -->
<div class="bg-primary">              <!-- brand color -->
<div class="bg-destructive">          <!-- error state -->

<!-- Text -->
<p class="text-foreground">           <!-- primary text -->
<p class="text-muted-foreground">     <!-- captions, placeholders -->
<p class="text-primary">              <!-- brand-colored text -->
<p class="text-destructive">          <!-- error text -->

<!-- Borders -->
<div class="border border-border">    <!-- standard border -->
<input class="border-input">          <!-- input border -->
```

### Status & Priority Colors (Extended Tokens)

Add these to `app/globals.css` for issue status colors:

```css
:root {
  --status-backlog:     oklch(0.6 0 0);        /* gray */
  --status-todo:        oklch(0.5 0.15 250);   /* blue */
  --status-in-progress: oklch(0.6 0.18 140);  /* green */
  --status-done:        oklch(0.55 0.15 140);  /* dark green */
  --status-cancelled:   oklch(0.55 0 0);       /* dark gray */
  --priority-urgent:    oklch(0.55 0.22 30);   /* red */
  --priority-high:      oklch(0.65 0.18 45);   /* orange */
  --priority-medium:    oklch(0.7 0.15 80);    /* yellow */
  --priority-low:       oklch(0.65 0 0);       /* gray */
}
```

---

## shadcn/ui Patterns (Copy-Paste Ready)

### Card

```typescript
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/card";

// Template:
<Card>
  <CardHeader>
    <CardTitle>Issue Title</CardTitle>
    <CardDescription>Created 2 hours ago</CardDescription>
  </CardHeader>
  <CardContent>
    <p className="text-sm text-muted-foreground">Description here</p>
  </CardContent>
  <CardFooter className="flex justify-end gap-2">
    <Button variant="outline">Cancel</Button>
    <Button>Save</Button>
  </CardFooter>
</Card>
```

### Button Variants

```html
<!-- Primary (default) -->
<Button>Create Issue</Button>

<!-- Secondary -->
<Button variant="secondary">Cancel</Button>

<!-- Ghost (icon buttons, nav) -->
<Button variant="ghost" size="icon">
  <TrashIcon className="h-4 w-4" />
</Button>

<!-- Destructive -->
<Button variant="destructive">Delete Board</Button>

<!-- Outline -->
<Button variant="outline">View Details</Button>

<!-- Link -->
<Button variant="link">Learn more</Button>

<!-- Loading state -->
<Button disabled={isPending}>
  {isPending ? "Saving…" : "Save"}
</Button>
```

### Dialog (for confirmations + forms)

```typescript
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";

<Dialog open={open} onOpenChange={setOpen}>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Delete Issue</DialogTitle>
      <DialogDescription>
        This action cannot be undone. The issue will be archived.
      </DialogDescription>
    </DialogHeader>
    <DialogFooter>
      <Button variant="outline" onClick={() => setOpen(false)}>
        Cancel
      </Button>
      <Button variant="destructive" onClick={handleDelete}>
        Delete
      </Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

### Badge (for status and priority)

```typescript
import { Badge } from "@/components/ui/badge";

<Badge>Default</Badge>
<Badge variant="secondary">In Progress</Badge>
<Badge variant="destructive">Blocked</Badge>
<Badge variant="outline">Backlog</Badge>
```

### Toast Notifications

```typescript
import { toast } from "sonner";  // sonner is the shadcn/ui recommended toast library

toast.success("Issue created successfully");
toast.error("Failed to create issue");
toast.info("Copied to clipboard");
toast.loading("Creating issue…", { id: "create-issue" });
toast.dismiss("create-issue");
```

### Dropdown Menu

```typescript
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";

<DropdownMenu>
  <DropdownMenuTrigger asChild>
    <Button variant="ghost" size="icon">
      <MoreHorizontalIcon className="h-4 w-4" />
    </Button>
  </DropdownMenuTrigger>
  <DropdownMenuContent align="end">
    <DropdownMenuItem onSelect={() => setEditing(true)}>Edit</DropdownMenuItem>
    <DropdownMenuItem onSelect={() => handleDuplicate()}>Duplicate</DropdownMenuItem>
    <DropdownMenuSeparator />
    <DropdownMenuItem onSelect={() => handleDelete()} className="text-destructive">
      Delete
    </DropdownMenuItem>
  </DropdownMenuContent>
</DropdownMenu>
```

---

## State Management Patterns

### Server Data (RSC → Server Action → revalidate)

```typescript
// lib/queries/issues.ts — used in RSC
import { db } from "@/lib/db";
import { auth } from "@/lib/auth";

export async function getIssuesByBoard(boardId: string) {
  const session = await auth();
  if (!session?.user) return [];

  return db.issue.findMany({
    where: {
      boardId,
      teamId: session.user.teamId,
      deletedAt: null,
    },
    orderBy: [{ status: "asc" }, { sortOrder: "asc" }],
    include: { assignee: { select: { id: true, name: true, image: true } } },
  });
}
```

### Optimistic Updates (useOptimistic)

```typescript
// components/board/column.tsx
"use client";

import { useOptimistic } from "react";
import { updateIssueStatus } from "@/lib/actions/issues";
import { type Issue, Status } from "@prisma/client";

export function Column({ issues: serverIssues, status }: { issues: Issue[]; status: Status }) {
  const [optimisticIssues, addOptimistic] = useOptimistic(
    serverIssues,
    (state, newIssue: Issue) => [...state.filter((i) => i.id !== newIssue.id), newIssue]
  );

  async function handleStatusChange(issueId: string, newStatus: Status) {
    // Optimistic update — immediate UI feedback
    const issue = optimisticIssues.find((i) => i.id === issueId)!;
    addOptimistic({ ...issue, status: newStatus });

    // Server Action — reconciles after
    await updateIssueStatus(issueId, newStatus);
  }

  return (
    <div>
      {optimisticIssues.map((issue) => (
        <IssueCard key={issue.id} issue={issue} onStatusChange={handleStatusChange} />
      ))}
    </div>
  );
}
```

### Zustand Store (board drag state)

```typescript
// lib/stores/board.ts
import { create } from "zustand";
import { type Issue } from "@prisma/client";

interface BoardState {
  activeIssue: Issue | null;
  overColumnId: string | null;
  isDragging: boolean;
  setActiveIssue: (issue: Issue | null) => void;
  setOverColumnId: (id: string | null) => void;
}

export const useBoardStore = create<BoardState>((set) => ({
  activeIssue: null,
  overColumnId: null,
  isDragging: false,
  setActiveIssue: (issue) => set({ activeIssue: issue, isDragging: issue !== null }),
  setOverColumnId: (id) => set({ overColumnId: id }),
}));
```

---

## Server Action Patterns

### Standard Server Action with Zod

```typescript
// lib/actions/issues.ts
"use server";

import { z } from "zod";
import { auth } from "@/lib/auth";
import { db } from "@/lib/db";
import { revalidatePath } from "next/cache";

const UpdateIssueStatusSchema = z.object({
  issueId: z.string().min(1),
  status: z.enum(["BACKLOG", "TODO", "IN_PROGRESS", "DONE", "CANCELLED"]),
});

export async function updateIssueStatus(issueId: string, status: string) {
  const session = await auth();
  if (!session?.user) return { error: "Unauthorized" };

  const parsed = UpdateIssueStatusSchema.safeParse({ issueId, status });
  if (!parsed.success) return { error: "Invalid input" };

  const issue = await db.issue.findFirst({
    where: { id: parsed.data.issueId, teamId: session.user.teamId },
  });
  if (!issue) return { error: "Issue not found" };

  await db.issue.update({
    where: { id: parsed.data.issueId },
    data: { status: parsed.data.status, updatedAt: new Date() },
  });

  revalidatePath(`/board/${issue.boardId}`);
  return { success: true };
}
```

### Server Action for file-based formData

```typescript
// lib/actions/boards.ts
"use server";

export async function createBoard(prevState: unknown, formData: FormData) {
  // useActionState signature: (prevState, formData) => newState
  const session = await auth();
  if (!session?.user) return { error: "Unauthorized" };

  const raw = {
    name: formData.get("name"),
    description: formData.get("description"),
  };

  const parsed = CreateBoardSchema.safeParse(raw);
  if (!parsed.success) {
    return { error: parsed.error.flatten().fieldErrors };
  }

  const board = await db.board.create({
    data: { ...parsed.data, teamId: session.user.teamId },
  });

  revalidatePath("/board");
  return { success: true, boardId: board.id };
}
```

---

## Auth & Session Patterns

### Session check in RSC (page or layout)

```typescript
// app/(dashboard)/layout.tsx
import { auth } from "@/lib/auth";
import { redirect } from "next/navigation";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await auth();
  if (!session?.user) redirect("/login");

  return (
    <div className="flex h-screen">
      <Sidebar user={session.user} />
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
```

### Session check in Client Component

```typescript
"use client";

import { useSession } from "next-auth/react";
import { redirect } from "next/navigation";

export function UserMenu() {
  const { data: session, status } = useSession();

  if (status === "loading") return <Skeleton className="h-8 w-8 rounded-full" />;
  if (!session) return null;  // Layout already redirected; this is just defensive

  return (
    <DropdownMenu>
      <DropdownMenuTrigger>
        <Avatar src={session.user.image} fallback={session.user.name?.[0]} />
      </DropdownMenuTrigger>
      {/* ... */}
    </DropdownMenu>
  );
}
```

### Auth Middleware (protects all dashboard routes)

```typescript
// middleware.ts
export { auth as middleware } from "@/lib/auth";

export const config = {
  matcher: ["/(dashboard)/:path*"],
};
```

---

## Routing Conventions

### Route Groups

- `(auth)/` — public auth pages; no auth middleware
- `(dashboard)/` — protected; wrapped in auth check in layout

### Parallel Routes (side panels)

```
app/(dashboard)/
├── board/[boardId]/
│   └── page.tsx              # Board view
├── @panel/                   # Parallel slot for side panel
│   └── issues/[issueId]/
│       └── page.tsx          # Issue detail — renders alongside board
└── layout.tsx                # Renders both {children} and {panel}
```

### Dynamic Segment Conventions

- `[boardId]` — always a `cuid()` string
- `[issueId]` — always a `cuid()` string
- Never use user-facing strings (titles, names) as URL segments — they break on rename

---

## Board / Drag-and-Drop Patterns (dnd-kit)

```typescript
// components/board/board-view.tsx
"use client";

import {
  DndContext,
  DragOverlay,
  closestCenter,
  PointerSensor,
  useSensor,
  useSensors,
  type DragStartEvent,
  type DragEndEvent,
} from "@dnd-kit/core";
import { useBoardStore } from "@/lib/stores/board";
import { moveIssue } from "@/lib/actions/issues";

export function BoardView({ board, initialIssues }: BoardViewProps) {
  const { setActiveIssue, activeIssue } = useBoardStore();

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 8 },  // 8px drag before activation
    })
  );

  async function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    setActiveIssue(null);
    await moveIssue(String(active.id), String(over.id));  // Server Action
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={(e: DragStartEvent) => {
        const issue = initialIssues.find((i) => i.id === e.active.id);
        if (issue) setActiveIssue(issue);
      }}
      onDragEnd={handleDragEnd}
    >
      <div className="flex gap-4 overflow-x-auto p-4">
        {board.columns.map((column) => (
          <Column key={column.id} column={column} issues={getColumnIssues(column.id)} />
        ))}
      </div>

      <DragOverlay>
        {activeIssue && <IssueCard issue={activeIssue} isDragOverlay />}
      </DragOverlay>
    </DndContext>
  );
}
```

---

## Anti-Pattern Reference

| ❌ Forbidden | ✅ Correct |
|-------------|-----------|
| `"use client"` on every component | RSC by default; `"use client"` only for interactivity |
| `useEffect(() => fetch('/api/issues'), [])` | RSC async component with `lib/queries/` |
| `fetch('/api/issues', { method: 'POST' })` in Server Action | Direct DB via `lib/actions/` + Prisma |
| `const prisma = new PrismaClient()` in a component | `import { db } from "@/lib/db"` singleton |
| Prisma query in Client Component | Move to RSC or Server Action |
| `background: #ffffff` | `bg-background` (CSS variable) |
| `color: #6b7280` | `text-muted-foreground` |
| `process.env.DATABASE_URL` in Client Component | Only `NEXT_PUBLIC_*` in client code |
| `any` type on Server Action return | `Promise<{ success: true; data: T } \| { error: string }>` |
| No Zod validation in Server Action | `const parsed = Schema.safeParse(formData); if (!parsed.success) return { error }` |
| `router.refresh()` after mutation | `revalidatePath()` inside the Server Action |
| 500-line component file | Split into sub-components under 300 lines each |
| `console.log(session)` | Remove; never log session data |
