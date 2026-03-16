# Deterministic Evaluation Template

_This template is used by the Architect to perform a deterministic evaluation of a completed workstream. It is a checklist of objective, verifiable criteria. **Customize the commands for your project's toolchain.**_

---

## Feature: [Feature Name]

### 1. Build Gate

_Replace these commands with your project's actual build/compile commands._

- [ ] **Primary build:** `[your build command]` passes with no errors.
  - Examples: `ng build`, `npm run build`, `cargo build`, `go build`
- [ ] **Type checking:** `[your typecheck command]` passes with zero errors.
  - Examples: `npx tsc --noEmit`, `pyright`, `mypy`

### 2. Linting

- [ ] **Linter:** `[your lint command]` passes with no errors.
  - Examples: `ng lint`, `npm run lint`, `ruff check .`, `golangci-lint run`

### 3. Security Audit

- [ ] **Dependency audit:** `[your audit command]` — no HIGH or CRITICAL vulnerabilities in production dependencies.
  - Examples: `npm audit --audit-level=high`, `cargo audit`, `pip-audit`

### 4. Diff Scope Verification

- [ ] Changes are confined to files in the workstream's **write manifest** (per the PRD).
- [ ] No unintended side effects to files outside the manifest.
- [ ] No new instances of forbidden patterns (e.g., hardcoded secrets, PHI in logs, `any` types in typed languages).

### 5. Final Result

- [ ] **PASS** — All checks above passed. Proceed to LLM Judgment eval (Layer 2).
- [ ] **FAIL** — One or more checks failed. Return to Feature Lead with specific errors.

---

## Project-Specific Customization Notes

*Document your project's specific checks here after your first epic.*

**Example (Angular / Node.js project):**
- Build: `ng build --configuration development`
- Typecheck: `cd server && npx tsc --noEmit`
- Lint: `ng lint` *(if configured)*
- Audit: `npm audit --audit-level=high`
- PHI check: `grep -r "patient_name\|mrn\|ssn" src/ --include="*.ts"` → must return 0 matches in non-test files
