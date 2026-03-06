# Deterministic Eval — [WorkstreamName] | [Date]

_Completed by Architect after Feature Lead HANDOFF. All items must pass before marking COMPLETE._

---

## 1. Lint Gate

- [ ] `[your lint command]` passes with no errors  
  _Examples: `ng lint`, `npm run lint`, `ruff check .`_

## 2. Build Gate

- [ ] `[your build command]` passes with no errors  
  _Examples: `npm run build`, `ng build --configuration development`, `cargo build`_

## 3. Type-Check Gate

- [ ] No type errors (e.g. `npx tsc --noEmit`, `pyright`, `mypy`)  
  _Customize for your stack._

## 4. Test Gate _(skip if workstream has no tests)_

- [ ] Test suite passes — no failing specs  
  _Examples: `npm test`, `ng test --run-once`, `pytest`_

## 5. Security / Compliance

- [ ] Dependency audit — no new high/critical vulnerabilities  
  _Examples: `npm audit --audit-level=high`, `cargo audit`_
- [ ] No credentials, secrets, or sensitive data in diff (adjust patterns for your domain)

## 6. Diff Scope Verification

- [ ] Changes confined to files in workstream write manifest: `git diff --name-only main...HEAD`
- [ ] No unintended files modified
- [ ] No forbidden patterns introduced (e.g. `any` in typed code, hardcoded secrets)

---

## 7. Final Result

- [ ] **PASS** — proceed to LLM judgment eval (non-mechanical workstreams) or mark COMPLETE directly (mechanical work)
- [ ] **FAIL** — return to Feature Lead with specific failing items listed below

### Failures (if any)

_List specific failing checks with output snippets._
