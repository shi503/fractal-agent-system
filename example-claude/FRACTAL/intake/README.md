# Strategist Intake Folder

Drop reference material here before starting a Strategist interview. The Strategist reads everything in this folder at session start.

This folder is gitignored. Safe to put anything here — competitor analyses, internal strategy docs, product screenshots described in text.

---

## Token Budget

The Strategist reads all files at session start. Budget accordingly.

```
Context budget for intake files: ~50,000 tokens total across all files.

Rules of thumb:
- 1 page of dense text ≈ 600 tokens
- 1 typical web article ≈ 2,000–4,000 tokens
- Budget allows ~10–15 pages of reference material per session
- No single file should exceed ~5,000 tokens (~25 pages / 4,000 words)
- Prefer excerpts over full documents — paste only the sections that matter

Practical limits:
  - Max files:     5–8 files in this folder at session start
  - Max per file:  200–300 lines of text (~3,000–4,500 tokens)
  - Total:         keep the entire folder under 50K tokens
```

---

## How to Handle URLs and Links

You have three options, in priority order:

### Option 1 — Extract and save (best)

Copy-paste only the relevant section from the URL into a `.md` file. Name it clearly.

```
competitor-api-ux-excerpt.md
reference-product-feature-excerpt.md
```

Include the source URL as the first line. Keep to <200 lines.

### Option 2 — Annotated link list (good)

Create a `links.md` file with URL + 3–5 bullets on what's relevant and why. The Strategist will NOT fetch URLs during the interview — it uses your bullets as context.

```markdown
## Competitor A — Key Feature
URL: https://example.com/...
- Bullet on what they do well
- What to emulate
- What NOT to copy

## Reference Product B
URL: https://...
- Relevance to your project
```

### Option 3 — Raw URL list (avoid)

A plain list of links with no context. The Strategist can't fetch these and will skip them.

---

## What to Include

- Competitor screenshots or product write-ups (save as `.md` with description)
- Existing strategy docs or briefs (paste the relevant sections)
- Prior art or reference implementations (file path in project, or excerpt)
- A `notes.md` with anything you want to say before the interview starts

## What NOT to Include

- Full web pages or articles — extract the relevant 1–2 sections instead
- Binary files — PDFs not recommended; convert to text excerpt if needed
- Code files — reference by path in the project, don't copy here

---

## Example File Structure

```
intake/
├── README.md                    (this file — committed)
├── notes.md                     (pre-interview notes)
├── links.md                     (annotated URL list)
├── competitor-feature-excerpt.md
└── strategy-brief-excerpt.md
```
