# Workstream PRD: FeatureLead-ExampleBackend

_Example workstream. Edit or replace with your own._

## Goal

Add a minimal backend capability (e.g. one API route or service) and tests.

## Context

Reference existing APIs and conventions. List guides by path only.

**Guides:** `{project-guides}/api-conventions.md`, `{project-guides}/testing-patterns.md`

## Acceptance Criteria

- [ ] New route or service implemented per PRD
- [ ] Build/typecheck passes
- [ ] Tests added or updated as specified

## File Manifest

**Read:** path/to/existing-api.ts, path/to/types.ts  
**Write:** path/to/new-endpoint.ts, path/to/new-endpoint.spec.ts

## Session Protocol

1. Read read-manifest files first
2. Implement; run build gate
3. /pulse if > 30 min or blocked; /handoff on completion
