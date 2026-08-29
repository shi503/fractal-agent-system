---
class: mutable-default-argument
severity: P2
---

# Mutable Default Argument

## What it is

A function default value, module-level constant, or object/array literal used as a shared "empty" placeholder that the function (or a caller) then mutates in place. The default is created once — at module load or at function-definition time — and every call that relies on it shares the same underlying reference.

## Why it matters

A default that's supposed to represent "nothing was passed" silently accumulates state across unrelated calls once anything mutates it. The bug is invisible in a single-call test and only appears after the function has been called more than once in a session — a classic "works in my test, fails in production under load" defect, and one that's easy to introduce again after a refactor because nothing about the type system flags it.

## How to spot it

- A function parameter default that's an array or object literal (`function f(opts = { tags: [] })`), where the function body ever does `.push()`, `.set()`, or a property assignment onto that default.
- A module-level `const DEFAULT_FILTERS = {}` (or `[]`) that's exported and then mutated by more than one call site instead of being read-only.
- A memoization or cache map created once at module scope with no key-eviction or scoping per call, used as if it were request-scoped state.
- React: a default prop value (an inline object/array literal, or a module-level constant) that a `useEffect` or event handler mutates directly instead of creating a new value.

## How to fix it

Never mutate a default value. If the function needs to build on the default, clone it first, or construct a fresh value inside the function body rather than relying on a shared default.

```ts
// Bad — every caller that omits `tags` shares and mutates the same array.
const DEFAULT_TAGS: string[] = []
function createIssue(input: { title: string; tags?: string[] }) {
  const tags = input.tags ?? DEFAULT_TAGS
  tags.push("untriaged") // mutates the shared default on every call that omits tags
  return db.issue.create({ data: { title: input.title, tags } })
}

// Good — a fresh array per call; the default is never mutated.
function createIssue(input: { title: string; tags?: string[] }) {
  const tags = [...(input.tags ?? []), "untriaged"]
  return db.issue.create({ data: { title: input.title, tags } })
}
```

If the default genuinely needs to be shared and read-only, freeze it (`Object.freeze(DEFAULT_TAGS)`) so an accidental mutation throws in development instead of silently corrupting shared state.
