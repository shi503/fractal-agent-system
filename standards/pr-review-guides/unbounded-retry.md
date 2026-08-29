---
class: unbounded-retry
severity: P1
---

# Unbounded Retry

## What it is

A retry loop with no cap on attempt count, no maximum elapsed time, and no backoff — or a cap so high it's effectively unbounded (e.g. `maxRetries: 1000`). On a sustained failure (an upstream outage, a permanently invalid request), the caller retries forever, or long enough to be indistinguishable from forever.

## Why it matters

An unbounded retry against a failing dependency turns a single failure into sustained load against that dependency, delaying its recovery and potentially triggering cascading failures elsewhere (thread/connection pool exhaustion, request queuing that starves other callers). It also silently hangs whatever was waiting on the result — a user-facing request that "just never comes back" is worse than one that fails fast with a clear error.

## How to spot it

- A `while (true)` or `for (;;)` loop around a network call with a `continue` on failure and no counter.
- A retry count that exists but is unreasonably large relative to the operation's timeout budget, with no corresponding maximum elapsed-time check.
- No backoff between attempts — retrying in a tight loop multiplies load on the failing dependency instead of giving it room to recover.
- A retry wrapper applied to a call without checking whether the failure is retryable at all (retrying a `400 Bad Request` or a `403 Forbidden` gains nothing and just adds load).

## How to fix it

Cap both the attempt count and the total elapsed time, use exponential backoff with jitter, and only retry errors that are actually transient.

```ts
// Bad — no cap, no backoff, retries even non-retryable errors.
async function fetchWithRetry(url: string) {
  while (true) {
    try {
      return await fetch(url)
    } catch {
      continue
    }
  }
}

// Good — bounded attempts, exponential backoff with jitter, retryable-only.
async function fetchWithRetry(url: string, maxAttempts = 4) {
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      const res = await fetch(url)
      if (!res.ok && isRetryableStatus(res.status) && attempt < maxAttempts) {
        await sleep(backoffWithJitter(attempt))
        continue
      }
      return res
    } catch (err) {
      if (attempt === maxAttempts) throw err
      await sleep(backoffWithJitter(attempt))
    }
  }
  throw new Error("unreachable")
}

function isRetryableStatus(status: number) {
  return status === 429 || status >= 500
}
```

Surface the terminal failure (after the cap is hit) to the caller explicitly — do not swallow it (see `standards/pr-review-guides/silent-exception-swallow.md`).
