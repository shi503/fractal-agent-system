# Deterministic Eval — [WorkstreamName] | [Date]

_Completed by Architect after Feature Lead HANDOFF. All items must pass before marking COMPLETE._

---

## 1. Lint Gate

- [ ] Lint passes with no errors

**Common commands by stack:**
| Stack | Command |
|-------|---------|
| Next.js / React | `npm run lint` or `npx eslint .` |
| Python | `ruff check .` or `flake8` |
| Go | `golangci-lint run` |
| Rust | `cargo clippy` |

---

## 2. Build Gate

- [ ] Production build passes with no errors

**Common commands by stack:**
| Stack | Command |
|-------|---------|
| Next.js | `npm run build` |
| Python | `python -m py_compile <files>` or build step |
| Go | `go build ./...` |
| Rust | `cargo build` |

---

## 3. Type-Check Gate

- [ ] No type errors

**Common commands by stack:**
| Stack | Command |
|-------|---------|
| TypeScript (any) | `npx tsc --noEmit` |
| Python (mypy) | `mypy .` |
| Python (pyright) | `pyright` |
| Go | `go vet ./...` |

---

## 4. Test Gate _(skip if workstream has no tests)_

- [ ] Test suite passes — no failing specs

**Common commands by stack:**
| Stack | Command |
|-------|---------|
| Next.js / React | `npm test` or `npx vitest run` |
| Python | `pytest` |
| Go | `go test ./...` |
| Rust | `cargo test` |

---

## 5. Security / Compliance

- [ ] Dependency audit — no new high/critical vulnerabilities
  - `npm audit --audit-level=high` (Node)
  - `cargo audit` (Rust)
  - `pip audit` (Python)
  - `govulncheck ./...` (Go)
- [ ] No credentials, secrets, or sensitive data in diff
- [ ] No `// @ts-ignore` or equivalent type-safety bypasses introduced

### Secrets & Sensitive Data Scan

Run against changed files (`git diff --name-only main...HEAD`):

| Scan | Command | Expected |
|------|---------|----------|
| Credentials | `grep -rn 'password\|secret\|api_key\|token\|credential\|connection_string' --include='*.ts' --include='*.py' --include='*.go' --include='*.rs' <changed-files> \| grep -iv 'test\|mock\|example\|\.env\.example\|type\|interface'` | No matches |
| Hardcoded config | `grep -rn 'localhost:\|127\.0\.0\.1\|0\.0\.0\.0' --include='*.ts' --include='*.py' --include='*.go' <changed-files> \| grep -iv 'test\|\.env\|config\.example\|README'` | No matches |
| Type-safety bypasses | `grep -rn '@ts-ignore\|@ts-expect-error\|# type: ignore\|#nosec\|nolint' <changed-files>` | No new instances |

<!--
### Enterprise / Compliance Guardrails (Optional)

Uncomment this section for projects with regulatory, contractual, or enterprise
compliance requirements (adapt the sensitive-field list to your domain).

- [ ] **Supply chain:** Container base images are from approved sources. No ad-hoc bases.
- [ ] **No sensitive personal data in logs, traces, or error messages:**
  `grep -rn 'ssn\|date_of_birth\|social_security\|<your-domain-specific-fields>' --include='*.ts' --include='*.py' --include='*.go' <changed-files> | grep -iv 'test\|mock\|type\|interface\|schema'`
- [ ] **Observability preserved:** Structured logs include request/transaction IDs. Health check endpoints exist and verify downstream reachability.
- [ ] **Config externalized:** All environment-specific values come from env vars or approved secret managers. No hardcoded URLs, ports, or connection strings.
- [ ] **Deployability:** Startup runs idempotent DB migrations. Fails fast on migration failure. Downgrades possible without destroying state.
- [ ] **Version tags:** Follow SemVer or date-hash format.
-->

---

## 6. Diff Scope Verification

- [ ] Changes confined to files in workstream write manifest: `git diff --name-only main...HEAD`
- [ ] No unintended files modified
- [ ] No forbidden patterns introduced (check your CLAUDE.md forbidden patterns table)

---

## 7. HANDOFF Structure Gate _(repos carrying `tools/contracts/`)_

The HANDOFF is the artifact this whole eval is run against, so it gets checked mechanically before anyone reads it for judgment. This step extracts the HANDOFF's structured sections to JSON and validates that JSON against `tools/contracts/schemas/handoff.schema.json`.

- [ ] The HANDOFF extracts to a schema-valid instance

```bash
OUT="$(mktemp -d)"
node tools/contracts/scripts/handoff-extract.cjs <workstream-dir>/HANDOFF.md --out "$OUT"
node tools/contracts/scripts/validate-contracts.cjs "$OUT"
```

Exit 0 means the document carries every field the schema requires: a parseable completion date, a summary, and — the one that catches the common failure — at least one row in the §5 eval table, so a HANDOFF cannot assert the work is done while recording no gate evidence. Non-zero prints the exact missing or malformed property; fix the markdown and re-run.

Negative fixture, for confirming the step is actually wired rather than silently passing:

```bash
node tools/contracts/scripts/handoff-extract.cjs \
  tools/contracts/examples/invalid/handoff-no-eval-table/HANDOFF.md --out "$OUT"
node tools/contracts/scripts/validate-contracts.cjs "$OUT"   # expect non-zero
```

**What this does not check.** Structure only. It cannot tell whether a **PASS** in the eval table was ever really run, whether the summary describes the diff, or whether the technical-debt entries are honest. Those are Layer 2 questions. Green here means the HANDOFF is worth reading, not that it is true.

Mark N/A in repos without `tools/contracts/`.

---

## 8. Final Result

- [ ] **PASS** — proceed to LLM judgment eval (non-mechanical workstreams) or mark COMPLETE directly (mechanical work)
- [ ] **FAIL** — return to Feature Lead with specific failing items listed below

### Failures (if any)

_List specific failing checks with output snippets._
