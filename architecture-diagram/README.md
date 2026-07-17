# Architecture Diagram

Generate layered system architecture diagrams as self-contained HTML/CSS embedded directly in Markdown. Color-coded tiers, grid layouts, and copy-ready templates for technology stacks, microservice topologies, and multi-tier applications.

## What it produces

A diagram built from horizontal layers (User, Application, AI/Logic, Data, Infrastructure, External Services), each with consistent semantic color coding and a grid of component panels. The output is plain HTML — no build step, no diagramming tool, no image export. It renders wherever Markdown renders HTML.

## How it works

The skill separates two concerns so you can mix them freely:

- **Style** — the visual skin: palette, borders, typography. Pick one that matches your audience (a banking RFP and a gaming dashboard want opposite tones).
- **Layout** — the structural skeleton: how many columns, where the sidebars sit, whether the flow is a stack or a pipeline. Layouts are wireframes with no color, so any layout combines with any style.

You choose a style and a layout, copy the template, then fill in your components layer by layer.

## Usage

Ask for an architecture diagram — the skill triggers on requests to draw a system architecture, technology stack, or multi-tier design. Point it at a system description and it selects a style and layout, or you can name them:

```
Draw the architecture for this system in the Steel Blue style, three-column layout.
```

## Structure

```
architecture-diagram/
├── SKILL.md                 # The workflow: rules, style/layout catalogs, advanced components
├── README.md
├── gallery.html             # All 12 styles rendered side by side — open in a browser
├── styles/                  # 12 visual styles — complete copy-ready HTML templates
│   ├── steel-blue.md        #   Consulting, finance, government, RFPs
│   ├── neon-dark.md         #   Tech talks, dev conferences, cybersecurity
│   └── ...                  #   ember-warm, ocean-teal, sage-forest, and more
├── layouts/                 # 13 structural layouts — wireframe skeletons
│   ├── three-column.md      #   Complex systems with cross-cutting sidebars
│   ├── pipeline.md          #   Data pipelines, CI/CD, ETL, stage-based flows
│   ├── connectors.md        #   SVG overlay lines and arrows between components
│   └── ...                  #   dashboard, grid-catalog, nested-containers, and more
└── scripts/
    ├── build_gallery.py     # Regenerates gallery.html from styles/*.md
    └── html_to_png.py       # Renders a diagram / style / gallery to PNG (headless browser)
```

## Preview

Open [gallery.html](gallery.html) in a browser to see all 12 styles rendered at once, each in its own isolated frame. It's a generated file — after editing any `styles/*.md`, regenerate it:

```
python3 scripts/build_gallery.py
```

## Export to PNG

Render any diagram to a PNG with a headless browser. Input can be a full `.html` file, a `styles/*.md` file (the template block is extracted), or a bare HTML fragment (wrapped automatically). Output is cropped tight to the diagram at 2x.

```
python3 scripts/html_to_png.py styles/steel-blue.md -o steel-blue.png
python3 scripts/html_to_png.py my-diagram.html            # -> my-diagram.png
python3 scripts/html_to_png.py gallery.html --full-page --max-height 12000
```

Backends, auto-selected in this order (override with `--backend`):

1. **`playwright`** — the Playwright Python package + Chromium. `pip install playwright && playwright install chromium`.
2. **`playwright-cli`** — the Homebrew tool. `brew install playwright-cli && playwright-cli install-browser`. Served over a short-lived local HTTP server (it blocks `file://`), 2x via CSS zoom, element-cropped.
3. **`browser`** — an installed Chrome / Chromium / Edge / Brave. No extra install; uses Pillow for the tight crop.

Run on macOS or Windows so the OS fonts render the serif / monospace / Helvetica voices.

See [SKILL.md](SKILL.md) for the full style and layout tables and the critical rules on HTML embedding.

## Attribution

Forked from [markdown-viewer/skills](https://github.com/markdown-viewer/skills) — `architecture`.
