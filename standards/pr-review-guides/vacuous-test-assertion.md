---
class: vacuous-test-assertion
severity: P2
---

# Vacuous Test Assertion

## What it is

A test asserts a property that the test setup or mock never actually causes to vary — so the assertion passes whether or not the behavior under test exists. The test is green, but it isn't testing anything.

## Why it matters

A vacuous assertion gives false confidence. It shows up as coverage in a report, but a regression in the guarded behavior will not fail it — the test would still pass even if the code under test were deleted. This is worse than no test at all, because it hides the gap: nobody adds real coverage for a code path that already "has a test."

## How to spot it

- The assertion checks a value that the mock or fixture sets unconditionally, regardless of the code path exercised (e.g. asserting a flag that only the *test double* sets, not the code under test).
- The test never exercises a failure or edge branch — only the happy path has any assertion at all, so a broken error path is simply invisible.
- Deleting the implementation under test (mentally, or as a quick experiment) would still leave the test green.
- An assertion on a mock call count or argument that's identical no matter what the function under test actually does with the result.

## How to fix it

Assert against state the code under test actually drives, so the test fails if that behavior regresses. For every new error or edge branch added to the implementation, add a test that exercises that branch specifically — not just the success path.

```ts
// Bad — `cancelled` is set by the mock's default response, not by the
// component's abort logic. This passes even if the abort call is removed.
it("cancels the request on unmount", () => {
  const { unmount } = render(<IssueList boardId="b1" />)
  unmount()
  expect(mockFetch.mock.calls[0][1]?.signal?.aborted).toBe(true) // trivially true — fetch mock always resolves this
})

// Good — asserts the actual effect: the abort controller the component
// created was signaled, and no state update happens after unmount.
it("cancels the request on unmount", async () => {
  const abortSpy = vi.spyOn(AbortController.prototype, "abort")
  const { unmount } = render(<IssueList boardId="b1" />)
  unmount()
  expect(abortSpy).toHaveBeenCalledOnce()
})
```
