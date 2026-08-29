---
class: missing-authorization-check
severity: P0
---

# Missing Authorization Check

## What it is

A handler, service function, or query that reads or mutates a specific resource without verifying that the requesting user is actually permitted to act on *that* resource — as distinct from being merely authenticated. The request passes a session/auth check at the boundary, then the resource-level check is missing entirely at the point the resource is loaded or written.

## Why it matters

Authentication answers "who is this?"; authorization answers "is this user allowed to touch this specific record?" A boundary check (middleware, a route guard) only ever answers the first question. Without an explicit resource-level check, any authenticated user can read or modify any record simply by supplying its ID — a classic IDOR (Insecure Direct Object Reference) defect. This is `standards/engineering-principles.md` §2 (Authorization at Every Layer) — the highest-severity class in this guide set because it's a direct data-exposure or data-corruption path, not a code-quality concern.

## How to spot it

- A Route Handler or Server Action that takes a resource ID from the request and loads it (`db.board.findUnique({ where: { id } })`) with no subsequent check that the session's user belongs to that resource's team/owner.
- A service function whose signature takes only the resource ID and the new data — no `userId` or `teamId` parameter at all — making a resource-scoped check structurally impossible without a broader refactor.
- A check that verifies the user is authenticated and *a* team member, but not a member of *the specific team that owns this resource* (checking the wrong scope).
- An admin-only mutation (delete, role change) gated only by a client-side UI condition (hiding the button) with no corresponding server-side check.

## How to fix it

Load the resource together with what's needed to check ownership, and reject before performing the mutation or returning the data — in the service layer, not only at the routing boundary.

```ts
// Bad — any authenticated user can delete any board by ID; no ownership check.
export async function DELETE(req: Request, { params }: { params: { boardId: string } }) {
  await db.board.delete({ where: { id: params.boardId } })
  return new Response(null, { status: 204 })
}

// Good — resource-level check happens before the mutation, in the service.
export async function DELETE(req: Request, { params }: { params: { boardId: string } }) {
  const session = await auth()
  if (!session?.user) return new Response(null, { status: 401 })
  await boardService.deleteBoard(params.boardId, session.user.id)
  return new Response(null, { status: 204 })
}

async function deleteBoard(boardId: string, userId: string) {
  const board = await db.board.findUniqueOrThrow({
    where: { id: boardId },
    include: { team: { include: { members: true } } },
  })
  const membership = board.team.members.find((m) => m.userId === userId)
  if (!membership || membership.role !== "ADMIN") {
    throw new ForbiddenError("not authorized to delete this board")
  }
  await db.board.delete({ where: { id: boardId } })
}
```

Add a test for the specific rejection case — an authenticated user who is *not* a member of the resource's team — not just the happy path and the unauthenticated case (see `standards/engineering-principles.md` §7).
