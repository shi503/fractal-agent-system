# Workstream PRD: FeatureLead-ExampleIntegration

_Example workstream. Depends on ExampleBackend and ExampleFrontend._

## Goal

Wire the frontend to the backend (e.g. API client, state, error handling).

## Context

Both ExampleBackend and ExampleFrontend must be complete. Reference their outputs and project integration patterns.

**Guides:** `{project-guides}/api-conventions.md`, `{project-guides}/frontend-dev-guide.md`

## Acceptance Criteria

- [ ] Frontend calls backend endpoint; errors handled
- [ ] Build/typecheck and tests pass

## File Manifest

**Read:** path/to/new-endpoint.ts, path/to/new-component.ts  
**Write:** path/to/api-client.ts, path/to/new-component.ts (wire-up)

## Session Protocol

1. Read read-manifest files first
2. Implement; run build gate
3. /pulse if > 30 min or blocked; /handoff on completion
