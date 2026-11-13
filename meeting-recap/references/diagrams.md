# Light-theme figures

Figures re-draw what was shown in the meeting (slides, whiteboard photos, org charts) or make a structure in the discussion visible. They're readable on screen and in print, and they never claim more than the source shows.

## Rules

- **Light theme, 12px minimum.** Ground `#FDFCFD`, ink `#1F2126`, secondary text `#5B5E66`, accent `#6E3F72`. No text under 12px anywhere, including arrow labels, legends and annotations. Title 20px/700, box names 13-16px/700, body 12px.
- **Solid means on the source, dashed means from the transcript.** Anything you add from what was said (a name, an arrow, a box) is dashed. The legend says so: "on the whiteboard" (solid) and "from the transcript" (dashed). Amber text marks open or unfilled items.
- **Don't read more into the source than it shows.** One set of figures had to be redrawn because it led with our naming and drew a "settled" arrow the whiteboard didn't have. When a word on a photo is unreadable, ask the user, one question at a time, and record "not sure" answers as such. Don't guess.
- **Canonical terms in labels.** Figure labels follow the glossary like the prose does.
- **Every figure ships twice**: `diagram/F<n>_<kebab-slug>.svg` and `diagram/F<n>_<kebab-slug>@2x.png`. Numbered in the order the recap mentions them.

## Workflow

1. **Capture the raw sources** into `captured-image/` beside `diagram/`, with descriptive names (`Whiteboard-p1_priorities.png`, `Org-chart.png`). PDF pages: `pdftoppm -r 200 -png in.pdf captured-image/Whiteboard-p`, then `sips -Z 1800 <png>` (macOS) or any resize to 1800px wide. HEIC photos: `sips -s format png in.HEIC --out captured-image/x.png`. The originals stay where the user put them.
2. **Look at each image** and list what's on it, region by region. Ask the user about anything unreadable before drawing.
3. **Copy the helpers**: `cp <skill>/scripts/svgkit.py diagram/_src/`. Write `diagram/_src/_figs.py` with one function per figure, importing from the local `svgkit`. A copied file keeps the figures regenerable after the skill moves. Three meetings' figures stopped building because their generators imported a shared style file that was later renamed.
4. **Generate and render**:
   ```sh
   cd diagram/_src && python3 _figs.py && cd ..
   for f in F*.svg; do rsvg-convert -z 2 -o "${f%.svg}@2x.png" "$f"; done
   ```
   `rsvg-convert` comes from librsvg (`brew install librsvg`). Install JetBrains Mono locally, or the renderer falls back to another font and the widths shift.
5. **Look at every PNG.** Check for text running out of its box (SVG text never wraps; `chip()` asserts the fit but `t()` can't), overlapping labels, and arrows pointing at the wrong box. Re-render after any SVG edit and compare. Don't trust file modification times.
6. **Write `diagram/_src/README.md`**: one line on the style, a `Figure | Re-drawn from` table pointing at each source file, the solid/dashed rule, and the exact regeneration commands.

## svgkit in brief

| Helper | Use |
|---|---|
| `head(w, h, title, subtitle)` | Opens the SVG: ground, 40px grid, arrow markers per category, title and subtitle. The subtitle says what it was re-drawn from |
| `t(x, y, text, size=12, fill, weight, anchor)` | All text. Fails on anything under 12px |
| `box(x, y, w, h, cat, dashed)` | Card with a ground-coloured mask under it |
| `chip(x, y, w, h, "line1\nline2", cat)` | Centred label in a box. Fails if a line overflows |
| `region(x, y, w, h, cat, label)` | Dashed grouping boundary with a label |
| `line([(x1, y1), (x2, y2), ...], cat, arrow, dashed)` | Connector with a marker in the category colour |
| `legend_item(x, y, cat, label, dashed)` | Legend swatch. Always include the solid/dashed pair |
| `text_w(text, size)` | Width estimate: 0.6em per char in JetBrains Mono, to size boxes |
| `save(OUT / "F1_slug", svg)` | Closes and writes `F1_slug.svg` |

Categories (fill / stroke): `primary` teal, `secondary` green, `tertiary` aubergine (our own area), `accent` amber (contracted, transcript-only), `alert` rose (risks), `connector` orange, `neutral` grey (containers, generic), `highlight` blue (root nodes, role chips).

Layout habits that worked: title at (30,44), content from y≈100-140, 40px grid spacing between boxes, the legend about 70px above the bottom, widths of 1000-1660px. Org charts read best as rows of bands; whiteboard flows keep the board's left-to-right order.

## With baoyu-diagram

If the user asks for `/baoyu-diagram`, use its layout rules: layering order, the mask rect under each box, spacing, legend outside the content, one arrow marker per colour. Then override its look. Its SKILL.md fixes a dark `#0f172a` ground with white text and 7-9px labels, and every meeting so far has had to undo that. Hand it this instead:

> Light theme, not dark. Ground `#FDFCFD` with a 40px grid stroked `#EFEAF0` 0.5. The mask rect under each box uses the ground colour, not `#0f172a`. Text ink `#1F2126`, sublabels `#5B5E66`, never white. Use the svgkit category fill/stroke pairs instead of the rgba dark fills. Minimum font-size 12px for every element, including arrow labels and annotations; the title is 20px/700. Solid = on the source image, dashed = from the transcript, and the legend says so.

Writing the figure through `svgkit` gets the same result with the floor enforced in code, which is why the newest meetings did that.

## In the HTML companion

`build_html.py` inlines each `diagram/F<n>_<slug>.svg` into its `<div class="fig-frame" data-fig="F<n>_<slug>">`, prefixing ids per figure and renaming `.mono` so the page CSS can't shrink figure text. Figures stay on a light card in every page theme because their colours are baked in.
