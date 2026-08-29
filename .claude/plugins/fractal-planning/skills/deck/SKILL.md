---
name: deck
description: "Generate a gold-standard 10-slide HTML presentation as a single self-contained file. Enforces the 80:20 format gate (1 title + ≤8 content + 1 next-steps), offers file or interview intake modes, and follows upstream frontend-slides visual standards — no generic AI aesthetics. Use when the user asks to make a deck, build a slide deck, create a presentation, make slides, generate slides, or make a slideshow."
user-invocable: true
argument-hint: "[topic-slug] — e.g., 'platform-launch', 'q3-roadmap', or leave blank to enter interview mode"
disable-model-invocation: false
attribution: "Vendored from https://github.com/zarazhangrui/frontend-slides (MIT, Copyright 2025 Zara Zhang). See references/ATTRIBUTION.md."
future-work: "PPT/PPTX export mode (upstream Phase 4) — deferred. Video/ffmpeg explainer lane — separate spike."
---

# Deck Skill — Gold-Standard Slide Generation

You generate **gold-standard 10-slide HTML presentations** as single self-contained files.
Every deck enforces the 80:20 principle: one idea per slide, detail in speaker notes.

**Attribution:** Templates and CSS vendored from
[frontend-slides](https://github.com/zarazhangrui/frontend-slides) by Zara Zhang (MIT).
See `${CLAUDE_PLUGIN_ROOT}/skills/deck/references/ATTRIBUTION.md`.

---

## Hard Constraint — The Gold-Standard Format Gate

Every deck you generate MUST conform to exactly:

```
1 title slide
+
≤8 content slides   ← HARD MAXIMUM
+
1 next-steps slide
= 10 slides total (minimum 4, maximum 10)
```

**If the user's content would require more than 8 content slides:**
1. Stop. Do not generate an oversized deck.
2. Present the excess slides as a list and propose specific cuts:
   - Merge related slides (combine "problem" + "current state" into one)
   - Move detail to speaker notes
   - Defer less-critical slides to an appendix doc (not a slide)
3. Ask the user to confirm which slides to cut before proceeding.

**Never** generate an 11+ content slide deck under any circumstance. The format gate is a
product quality guarantee, not a preference.

---

## Intake Mode A — File Mode

When the user provides source files (markdown docs, meeting notes, wiki pages):

### Step 1 — Ingest sources

Read all provided files completely. Build an internal model of:
- The core argument or announcement
- The key evidence, data, or decisions
- The audience and their context
- What action is being requested

### Step 2 — Distill the outline

Apply the gold-standard format gate immediately during outline construction.
Map the source material to ≤10 slide slots. Anything that doesn't fit into
8 content slides goes to speaker notes or an appendix.

Announce the outline to the user before generating HTML:

```
Here's the 10-slide structure I'm generating:
1. [Title] — <headline>
2. [Content] — <one idea>
...
10. [Next Steps] — <action items>

Cuts made: [list what was moved to speaker notes or appendix]
Proceed? (yes / adjust / cancel)
```

### Step 3 — Style discovery (show, don't tell)

Before generating the full deck, run the style discovery flow (see §Style Discovery below).

### Step 4 — Generate the deck

Generate the single-file HTML. See §Generation Invariants for hard technical requirements.

---

## Intake Mode B — Interview Mode

When the user has no source files, run a structured discovery interview in the persona
of a professional product designer and keynote presenter. Your job is to draw out the
story, not collect content — you are a collaborator with craft opinion, not a transcription service.

**Persona:** You are an experienced product designer who has coached hundreds of
executive presentations. You ask questions that reveal narrative and visual opportunity.
You push back on content that doesn't serve the story. You have taste.

### Interview Batch 1 — Audience and Takeaway (≤4 questions)

Present as a single `AskUserQuestion` with these concrete options where applicable:

```
I need four things to build your outline. Answer briefly — I'll handle structure.

1. Who is the audience?
   a) Executive / board (strategic, business outcomes)
   b) Engineering team (technical, implementation focus)
   c) Customer / external (trust-building, product demo)
   d) Internal team (operational, alignment)
   e) Other — describe in one sentence

2. What is the ONE sentence they should walk away remembering?
   (Not a topic. A claim. "By Q3 we will..." or "The reason X failed is...")

3. What's the occasion?
   a) Product launch / announcement
   b) Quarterly review / status update
   c) Strategy / planning alignment
   d) Customer pitch / proposal
   e) Team onboarding / kickoff
   f) Research / data readout
   g) Other

4. Do you have any existing content to pull from?
   (Docs, notes, a previous deck, data exports — paste or link)
```

### Interview Batch 2 — Narrative Arc (≤4 questions)

After receiving Batch 1 answers, present Batch 2:

```
Good. Now let's find the story.

1. What's the problem or tension your audience feels?
   (The thing that makes this presentation necessary — why are we all here?)

2. What's the resolution you're offering?
   (The thing that changes after they hear you — decision made, action taken, belief shifted)

3. What's the one thing that could derail your message?
   (The objection, the counter-narrative, the "but what about..." you need to address)

4. What should NOT be in this deck?
   (Topics that feel relevant but would dilute the message or belong in a separate conversation)
```

### Interview Batch 3 — Visual Mood (≤4 questions)

After receiving Batch 2 answers, present Batch 3:

```
Last batch — visual direction.

1. What feeling should the deck create in the room?
   a) Authoritative / institutional (navy, serif, restrained)
   b) Modern / professional (clean, single accent, data-forward)
   c) Bold / editorial (high contrast, display type, confident)
   d) Warm / approachable (light backgrounds, friendly type)
   e) Creative / design-led (expressive, graphic, distinctive)

2. Is there a brand color or palette I should anchor to?
   (Hex codes, brand name, or "no preference — pick for me")

3. What's the formality level?
   a) Board / investor — maximum polish
   b) Executive team — polished but human
   c) Internal team — clean but approachable
   d) Informal — personality over polish

4. Any decks or brands whose visual style you admire?
   (References help me avoid generic and aim for specific)
```

### After Interview — Build outline

Synthesize all three batches into a 10-slide narrative outline. Present for confirmation
before style discovery and generation (same outline format as File Mode Step 2).

---

## Style Discovery — Show, Don't Tell

Before generating the full deck, generate **3 single-slide HTML previews** representing
three distinct visual directions. Each preview is a complete, standalone HTML file
showing only the title slide at 1920×1080.

Present them as:

```
Here are three visual directions for <topic>. Open each in your browser and tell me
which one to develop — or describe what you'd change.

Option A: <preset name> — <one-sentence mood description>
→ [path-to-preview-A.html]

Option B: <preset name> — <one-sentence mood description>
→ [path-to-preview-B.html]

Option C: <preset name> — <one-sentence mood description>
→ [path-to-preview-C.html]
```

Select the three presets from `references/STYLE_PRESETS.md` and `references/selection-index.json`
based on the user's stated mood and audience. Do NOT offer Inter/Roboto/generic-gradient options.
The three options should be meaningfully distinct — not three variations of the same mood.

Wait for the user's selection before generating the full deck. If they describe changes,
incorporate them. If they pick a direction and ask for modifications, apply them before
proceeding.

---

## Generation Invariants

These rules are non-negotiable for every deck generated by this skill.

### Structure

- Single self-contained HTML file. Zero external dependencies (CSS/JS are inline).
- Fonts loaded from Fontshare or Google Fonts CDN only. Never system fonts, never Inter,
  never Roboto for display/headline roles.
- Slides are `<section class="slide">` elements inside `.deck-stage`.
- First slide has class `active` and `visible`. All others start hidden.

### Fixed 1920×1080 Stage

Include `viewport-base.css` verbatim (from `references/viewport-base.css`) as the base
CSS layer. Do not modify it. The stage is always 1920×1080. Slides do not reflow for
mobile — they letterbox/pillarbox.

JavaScript stage scaler (required, inline in every deck):

```javascript
class SlidePresentation {
    constructor() {
        this.slides = document.querySelectorAll('.slide');
        this.currentSlide = 0;
        this.stage = document.getElementById('deckStage');
        this.setupStageScale();
        this.setupKeyboardNav();
        this.setupTouchNav();
        this.showSlide(0);
    }

    setupStageScale() {
        const scale = () => {
            const factor = Math.min(window.innerWidth / 1920, window.innerHeight / 1080);
            const x = (window.innerWidth - 1920 * factor) / 2;
            const y = (window.innerHeight - 1080 * factor) / 2;
            this.stage.style.transform = `translate(${x}px, ${y}px) scale(${factor})`;
        };
        scale();
        window.addEventListener('resize', scale);
    }

    setupKeyboardNav() {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowRight' || e.key === 'ArrowDown' || e.key === ' ' || e.key === 'PageDown') {
                e.preventDefault();
                this.showSlide(this.currentSlide + 1);
            } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp' || e.key === 'PageUp') {
                e.preventDefault();
                this.showSlide(this.currentSlide - 1);
            }
        });
    }

    setupTouchNav() {
        let touchStartX = 0;
        document.addEventListener('touchstart', (e) => { touchStartX = e.touches[0].clientX; });
        document.addEventListener('touchend', (e) => {
            const delta = touchStartX - e.changedTouches[0].clientX;
            if (Math.abs(delta) > 50) this.showSlide(this.currentSlide + (delta > 0 ? 1 : -1));
        });
    }

    showSlide(index) {
        this.currentSlide = Math.max(0, Math.min(index, this.slides.length - 1));
        this.slides.forEach((slide, i) => {
            slide.classList.toggle('active', i === this.currentSlide);
            slide.classList.toggle('visible', i === this.currentSlide);
        });
    }
}

const presentation = new SlidePresentation();
```

### Slide Switching

Use `.active` / `.visible` class toggling **only**. Never use `display: none` to hide slides.
The `viewport-base.css` uses `visibility: hidden; opacity: 0` for non-active slides.

### CSS Negation Rule

When negating CSS function values, always use `calc(-1 * ...)`:

```css
/* WRONG — silently ignored: */
right: -clamp(28px, 3.5vw, 44px);

/* CORRECT: */
right: calc(-1 * clamp(28px, 3.5vw, 44px));
```

### Speaker Notes

Every content slide must have a speaker notes section rendered as an HTML comment
immediately after the slide's closing `</section>` tag:

```html
<!-- SPEAKER NOTES: Slide 2
  [3-5 sentences of context, evidence, and talking points that do NOT appear on the slide.
   This is where the 80% detail lives.]
-->
```

### No Generic AI Aesthetics

Forbidden patterns (never use):
- Fonts: Inter, Roboto, Arial, system fonts as headline/display
- Colors: `#6366f1` (generic indigo), purple gradients on white
- Layouts: everything centered, generic hero sections, identical card grids
- Decorations: realistic illustrations, gratuitous glassmorphism, drop shadows without purpose

Mandatory distinctiveness: choose from `references/STYLE_PRESETS.md` or `references/selection-index.json`.
The 34 bold-template-pack designs provide concrete starting points. Read the relevant
`design-*.md` file in `references/` before generating for a premium template.

### Inline Editing (default: on)

Include the inline editing affordance by default (see `references/html-template.md`
§Inline Editing Implementation). Use JS-based hover with 400ms delay timeout.
Do NOT use the CSS `~` sibling selector approach.

---

## Output Location

Default output: `decks/<topic-slug>/<topic-slug>.html` at the repo root.

Examples:
- `decks/platform-launch/platform-launch.html`
- `decks/q3-roadmap/q3-roadmap.html`

The caller may override with an explicit path. Create the directory if it doesn't exist.

---

## PDF Export

After generating a deck, offer PDF export:

```
Deck saved to decks/<topic-slug>/<topic-slug>.html

To export as PDF (preserves colors and fonts, no animations):
  bash "${CLAUDE_PLUGIN_ROOT}/skills/deck/scripts/export-pdf.sh" decks/<topic-slug>/<topic-slug>.html

Requires Node.js. Playwright installs automatically on first run.
```

---

## Style Reference Quick-Pick

When selecting a preset without knowing all context, use this guide:

| Audience / Occasion | Recommended preset |
|---------------------|--------------------|
| Investor / board | Signal, Vellum, Cartesian |
| Engineering all-hands | Blue Professional, Neo-Grid Bold, Cobalt Grid |
| Product launch | Emerald Editorial, Bold Poster, Studio |
| Customer pitch | Blue Professional, Signal, Emerald Editorial |
| Strategy / planning | Signal, Vellum, Editorial Forest |
| Creative / agency | Emerald Editorial, Neo-Grid Bold, Creative Mode |
| Internal team update | Blue Professional, Editorial Forest, Monochrome |

Read the relevant `design-*.md` file in `references/` for the 5 deep-craft templates
that are vendored (Signal, Emerald Editorial, Blue Professional, Neo-Grid Bold, Vellum).
For the other 29 templates, use `references/selection-index.json` for metadata and mood tags.

---

## What This Skill Does NOT Do

- Generate PPT/PPTX — deferred (upstream Phase 4, not yet implemented)
- Deploy to Vercel or any hosting — out of scope (team has no Vercel account)
- Produce explainer videos — separate ffmpeg spike
- Generate more than 10 slides — hard format gate, see above
