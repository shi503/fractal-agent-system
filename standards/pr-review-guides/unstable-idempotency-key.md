---
class: unstable-idempotency-key
severity: P1
---

# Unstable Idempotency Key

## What it is

An idempotency key generated fresh **per physical request** instead of once per logical operation. The most common shape: a client interceptor that calls `crypto.randomUUID()` on every `POST`/`PUT`/`PATCH` and attaches it as an `Idempotency-Key` header. It also appears server-side, when a retry path mints a new key instead of reusing the original one.

## Why it matters

The entire point of an idempotency key is that the **same logical action carries the same key across retries**, so the server can deduplicate. A per-request UUID gives two submissions of the same logical action — a double-click, a slow-network client-side retry — two *different* keys, so both execute and the duplicate write the key was meant to prevent happens anyway. It looks correct in review and passes a single-shot test; it only fails under the exact concurrency it was supposed to guard against.

## How to spot it

- A `fetch`/HTTP-client interceptor or wrapper that generates a new UUID unconditionally on every call, rather than accepting a key from the caller.
- A key derived from `Date.now()` or a fixed-size time bucket (`Math.floor(timestamp / windowSeconds)`) — stable *within* one bucket, but two retries straddling a bucket boundary still get different keys, so the same failure mode reappears at the edge.
- A retry loop or a queue consumer's redelivery path that calls the key-generation function again instead of reusing the key attached to the original attempt.
- Citing a payment provider's idempotency-key requirement in a design doc while the actual implementation mints a new key per attempt — the two are contradictory.

## How to fix it

Derive the key from the logical operation, and keep it stable across every retry of that operation:

- **Client-side action:** generate the key once, at the user-action boundary (the submit handler, the command object) — not inside a blanket request interceptor — and reuse it for every retry of that specific action.
- **Server-to-server or a background job:** use a deterministic key derived from stable identifiers, e.g. `` `${workflowId}:${stepName}` `` — stable across a retry or a resume.
- If a blanket interceptor is still used for transport-level retries, scope it explicitly to retries of the *same* request object, and handle user-triggered double-submit separately (disable-on-submit, an in-flight guard) rather than folding both concerns into one key.

```ts
// Bad — every call gets a fresh key, so a client retry executes twice.
async function createIssue(input: CreateIssueInput) {
  return apiClient.post("/api/issues", input, {
    headers: { "Idempotency-Key": crypto.randomUUID() },
  })
}

// Good — the key is minted once at the action boundary and reused on retry.
async function createIssue(input: CreateIssueInput, idempotencyKey: string) {
  return apiClient.post("/api/issues", input, {
    headers: { "Idempotency-Key": idempotencyKey },
  })
}

// Caller mints the key once, before any retry attempt:
const idempotencyKey = crypto.randomUUID()
await retry(() => createIssue(input, idempotencyKey))
```
