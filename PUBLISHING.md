# Publishing FRACTAL to GitHub

This guide explains how to publish the `fractal-agents-system` directory as a standalone GitHub repository.

## Option A: New repo from the `fractal-agents-system` folder only

Use this when you want a **new** GitHub repo that contains only the FRACTAL system (no parent project).

### 1. Create the new repo on GitHub

- Go to [github.com/new](https://github.com/new).
- **Repository name:** e.g. `fractal-agents-system` or `fractal-multi-agent-system`.
- **Description:** e.g. `Hierarchical framework for orchestrating AI agent teams on software development tasks. Deterministic routing, hard context resets, tool trace as truth.`
- **Visibility:** Public (or Private if you prefer).
- **Do not** initialize with a README, .gitignore, or license (we already have them in the folder).

Click **Create repository**.

### 2. Initialize git in `fractal-agents-system` and push

From your **project root** (the parent of `fractal-agents-system`):

```bash
cd fractal-agents-system
git init
git add .
git commit -m "chore: initial FRACTAL multi-agent system release"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/fractal-agents-system.git
git push -u origin main
```

Replace `YOUR_USERNAME` and the repo URL with your GitHub username and the URL GitHub shows for the new repo.

### 3. Using GitHub CLI (`gh`) instead

If you have [GitHub CLI](https://cli.github.com/) installed:

```bash
cd fractal-agents-system
git init
git add .
git commit -m "chore: initial FRACTAL multi-agent system release"
gh repo create fractal-agents-system --public --source=. --remote=origin --push
```

This creates the repo, adds the remote, and pushes in one step.

---

## Option B: New branch in the existing (parent) repo

Use this when you want to keep FRACTAL inside your current repo but publish it on a **dedicated branch** (e.g. for a release or a clean copy).

### 1. Create and switch to a new branch

From your project root:

```bash
git checkout -b fractal-agents-system-release
```

### 2. Ensure only FRACTAL content is committed (optional)

If you want this branch to contain **only** the `fractal-agents-system/` tree (so you could later push it to a separate repo or use it as a submodule):

- You can keep the rest of the repo as-is and just commit the FRACTAL changes on this branch, or
- Use `git subtree split` to create a new history containing only `fractal-agents-system/` (advanced; see `git help subtree`).

For most cases, simply committing your current changes on the new branch is enough:

```bash
git add fractal-agents-system/
git status   # review
git commit -m "chore: FRACTAL public release prep — generalize agents, add Cursor, README, LICENSE"
git push -u origin fractal-agents-system-release
```

### 3. Publish that branch as a separate repo (optional)

To turn the `fractal-agents-system/` subfolder into its own repo later:

```bash
git subtree split -P fractal-agents-system -b fractal-only
# Then create a new GitHub repo and push the fractal-only branch:
# git push https://github.com/YOUR_USERNAME/fractal-agents-system.git fractal-only:main
```

---

## Recommended repo settings (GitHub)

- **Topics:** `ai-agents`, `multi-agent`, `orchestration`, `claude`, `cursor`, `llm`, `software-development`, `fractal`
- **Website:** Leave blank or add a docs link if you add one.
- **Description:** Use the one-line description from the README (e.g. hierarchical framework for orchestrating AI agent teams).

---

## After publishing

- Clone the new repo elsewhere to confirm it builds a clean copy:  
  `git clone https://github.com/YOUR_USERNAME/fractal-agents-system.git`
- Add a **.gitignore** in `fractal-agents-system/` if you want to ignore `ROUTING_LOGIC/.state.json` or other local artifacts when people copy the router into their projects (the README already documents what to gitignore in the consuming project).
