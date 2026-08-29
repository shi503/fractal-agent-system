# Changelog

All notable changes to the FRACTAL router are recorded here.

## 2.0.0

Blueprint shape normalization (accepts both phased and flat shapes), a `--blueprint` override with a cwd → script-dir → repo-root path resolver, and a repo-root-relative default `BLUEPRINT_PATH`. **Breaking** for any downstream vendor pinning `ROUTING_LOGIC/router.py` by hash — the normalization pass rewrites `dependencies`/`depends_on` and derives `feature_lead` on load, so a consumer relying on the raw parsed blueprint shape must re-baseline deliberately.

- `_normalize_blueprint()` coerces a top-level phased list (`- name: ... workstreams: [...]`) and a flat single-mapping shape (`name: ... workstreams: [...]` with `id`/`depends_on`) into one canonical form before `init`/`next`/`update` ever see it.
- `--blueprint <path>` resolves a relative path against the current working directory first, then the script's own directory, then the repo root — no more hand-editing `BLUEPRINT_PATH` to switch epics.
- Default `BLUEPRINT_PATH` now points at `fixtures/taskflow/blueprints/BLUEPRINT-NOVA-P1-NotificationCore.yaml`, resolved from the repo root regardless of which of the two router.py copies is invoked.
- `ROUTING_LOGIC/router.py` is canonical; `.claude/fractal/router.py` is a synced copy. `tools/check-router-identity.sh` verifies the two never drift.
- `tools/router-smoke.sh` added — exercises `init`/`next`/`update`/`status`/`pulse` end-to-end, including the dependency-edge assertion (a workstream's dependents do not surface from `next` until it is marked `COMPLETE`), against a throwaway state file.

## 1.0.0

Initial router: single blueprint shape (phased list), `init`/`next`/`update`/`status`/`pulse` commands, `--blueprint` override with script-directory-relative resolution.
