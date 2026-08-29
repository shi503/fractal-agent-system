# Attribution — Vendored Assets from frontend-slides

**Source repository:** https://github.com/zarazhangrui/frontend-slides  
**Author:** Zara Zhang (zarazhangrui)  
**License:** MIT  
**Vendored:** 2026-06-04 (WS-A1 DeckSkillGoldStandard)

## License Text

```
MIT License

Copyright (c) 2025 Zara Zhang

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## What was vendored

| File | Source path | Purpose |
|------|-------------|---------|
| `STYLE_PRESETS.md` | `STYLE_PRESETS.md` | 12 curated visual presets |
| `viewport-base.css` | `viewport-base.css` | Mandatory fixed-stage base CSS |
| `html-template.md` | `html-template.md` | HTML generation architecture reference |
| `animation-patterns.md` | `animation-patterns.md` | Animation recipes by mood |
| `selection-index.json` | `bold-template-pack/selection-index.json` | 34-template index for style discovery |
| `design-signal.md` | `bold-template-pack/templates/signal/design.md` | Representative deep-craft editorial template |
| `design-emerald-editorial.md` | `bold-template-pack/templates/emerald-editorial/design.md` | Representative bold display template |
| `design-blue-professional.md` | `bold-template-pack/templates/blue-professional/design.md` | Representative professional/B2B template |
| `design-neo-grid-bold.md` | `bold-template-pack/templates/neo-grid-bold/design.md` | Representative brutalist editorial template |
| `design-vellum.md` | `bold-template-pack/templates/vellum/design.md` | Representative monochromatic scholarly template |
| `scripts/export-pdf.sh` | `scripts/export-pdf.sh` | Playwright PDF export script |

## What was NOT vendored

- `bold-template-pack/templates/*/template.html` — raw HTML files (not needed; design.md is sufficient)
- All template preview.md files (not needed for generation)
- `scripts/deploy.sh` — out of scope per PRD §6
- `scripts/extract-pptx.py` — out of scope per PRD §6
- `bold-template-pack/deck-stage.js` — inline in generated output; not vendored separately

## Modifications

The vendored `export-pdf.sh` was modified to use `${CLAUDE_PLUGIN_ROOT}` for its
own self-reference comment and output path convention, per plugin-authoring.md
`${CLAUDE_PLUGIN_ROOT}` conventions. Functional logic is unchanged.
