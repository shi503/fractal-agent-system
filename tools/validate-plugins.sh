#!/usr/bin/env bash
# validate-plugins.sh — deterministic gate for the FRACTAL plugin+marketplace layer.
#
# Checks:
#   1. .claude-plugin/marketplace.json parses as JSON
#   2. exactly 6 plugins registered in the marketplace
#   3. every plugin's "source" is "./"-prefixed and the directory exists
#   4. every plugin.json parses and has name/version/description/author,
#      with version exactly "2.0.0"
#   5. every SKILL.md's frontmatter "name:" matches its containing directory name
#   6. no "trigger-phrases", "model", or "tools" keys appear in any SKILL.md
#      frontmatter
#
# Usage: bash tools/validate-plugins.sh
# Exit code: 0 = all checks pass, 1 = at least one failure.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

python3 - "$REPO_ROOT" <<'PYEOF'
import json
import re
import sys
from pathlib import Path

repo_root = Path(sys.argv[1])
failures = []
checks_passed = 0


def fail(msg):
    failures.append(msg)


def ok():
    global checks_passed
    checks_passed += 1


# --- Check 1 + 2: marketplace.json parses, exactly 6 plugins ---
marketplace_path = repo_root / ".claude-plugin" / "marketplace.json"
if not marketplace_path.is_file():
    fail(f"marketplace.json not found at {marketplace_path}")
    marketplace = None
else:
    try:
        marketplace = json.loads(marketplace_path.read_text())
        ok()
    except json.JSONDecodeError as e:
        fail(f"marketplace.json does not parse: {e}")
        marketplace = None

plugins = []
if marketplace is not None:
    plugins = marketplace.get("plugins", [])
    if len(plugins) == 6:
        ok()
    else:
        fail(f"expected exactly 6 plugins in marketplace.json, found {len(plugins)}")

# --- Check 3: every source path is "./"-prefixed and exists ---
for p in plugins:
    name = p.get("name", "<unnamed>")
    source = p.get("source", "")
    if not source.startswith("./"):
        fail(f"plugin '{name}': source '{source}' is not './'-prefixed")
        continue
    source_dir = repo_root / source[2:]
    if not source_dir.is_dir():
        fail(f"plugin '{name}': source dir does not exist: {source_dir}")
    else:
        ok()

# --- Check 4: every plugin.json parses, has required fields, version 2.0.0 ---
plugin_json_paths = sorted(repo_root.glob(".claude/plugins/*/.claude-plugin/plugin.json"))
if not plugin_json_paths:
    fail("no plugin.json files found under .claude/plugins/*/.claude-plugin/")

required_fields = ["name", "version", "description", "author"]
for pj_path in plugin_json_paths:
    try:
        data = json.loads(pj_path.read_text())
    except json.JSONDecodeError as e:
        fail(f"{pj_path}: does not parse: {e}")
        continue

    missing = [f for f in required_fields if f not in data]
    if missing:
        fail(f"{pj_path}: missing required field(s): {', '.join(missing)}")
    else:
        ok()

    version = data.get("version")
    if version != "2.0.0":
        fail(f"{pj_path}: version is '{version}', expected exactly '2.0.0'")
    else:
        ok()

# --- Checks 5 + 6: SKILL.md frontmatter ---
skill_md_paths = sorted(repo_root.glob(".claude/plugins/*/skills/*/SKILL.md"))
if not skill_md_paths:
    fail("no SKILL.md files found under .claude/plugins/*/skills/*/")

frontmatter_re = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
forbidden_keys = ("trigger-phrases", "model", "tools")

for skill_path in skill_md_paths:
    text = skill_path.read_text()
    m = frontmatter_re.match(text)
    if not m:
        fail(f"{skill_path}: no YAML frontmatter block found")
        continue
    frontmatter = m.group(1)

    dir_name = skill_path.parent.name
    name_match = re.search(r"(?m)^name:\s*['\"]?([A-Za-z0-9_-]+)['\"]?\s*$", frontmatter)
    if not name_match:
        fail(f"{skill_path}: frontmatter has no 'name:' key")
    elif name_match.group(1) != dir_name:
        fail(f"{skill_path}: name '{name_match.group(1)}' != directory '{dir_name}'")
    else:
        ok()

    hit_keys = [
        key for key in forbidden_keys
        if re.search(rf"(?m)^{re.escape(key)}\s*:", frontmatter)
    ]
    if hit_keys:
        fail(f"{skill_path}: forbidden frontmatter key(s) present: {', '.join(hit_keys)}")
    else:
        ok()

# --- Report ---
if failures:
    print(f"validate-plugins: FAIL ({len(failures)} issue(s), {checks_passed} check(s) passed)")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
else:
    print(f"validate-plugins: PASS ({checks_passed} check(s) passed)")
    sys.exit(0)
PYEOF
