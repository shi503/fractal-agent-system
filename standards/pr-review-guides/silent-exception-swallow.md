---
class: silent-exception-swallow
severity: P1
---

# Silent Exception Swallow

## What it is

A caught exception with no log and no rethrow: an empty `catch` block, a `catch` that returns a default value with no logging, or a promise `.catch()` with no handler at all. The code appears to run successfully while a real failure is discarded.

## Why it matters

Swallowing an exception removes observability and makes production failures invisible — the worst possible failure mode, because the system looks healthy in every dashboard while it's actually failing. This enforces `standards/engineering-principles.md` §5 (Explicit Exception Handling). It applies to two near-miss variants as well as the obvious empty catch:

- Logging the error but **losing the stack trace** — passing only `err.message` to the logger instead of the error object, so root-causing from production logs later is impossible.
- A module with **no logger configured at all**, so an exception thrown deep in a call chain propagates with no log at the layer that actually had the context to explain it.

Both look "handled" in review but lose the diagnostic the log call was supposed to provide.

## How to spot it

- `catch {}` or `catch (e) {}` with no body, or a body that only sets a UI flag with no logging.
- `.catch(() => {})` or `.catch(() => defaultValue)` on a promise, with nothing logged.
- `logger.error(err.message)` instead of `logger.error("context", { err })` — the stack trace is discarded.
- A `try/catch` around a call into a module with no `logger` import anywhere in that module.
- A broad `catch (err) { return null }` in a service function, where the caller can't distinguish "not found" from "the database call threw."

## How to fix it

Log (or rethrow, or both) every caught exception before any fallback runs. Pass the error object itself to the logger, not just its message, so the stack trace survives. If a module handles errors, it needs its own logger — don't rely on a caller three layers up to notice.

```ts
// Bad — the failure is invisible; callers can't tell "empty" from "broken".
async function getBoardSettings(boardId: string) {
  try {
    return await db.boardSettings.findUniqueOrThrow({ where: { boardId } })
  } catch {
    return null
  }
}

// Good — logged with the full error, and the caller decides how to handle absence.
async function getBoardSettings(boardId: string) {
  try {
    return await db.boardSettings.findUniqueOrThrow({ where: { boardId } })
  } catch (err) {
    logger.error("board_settings.lookup_failed", { boardId, err })
    throw err
  }
}
```
