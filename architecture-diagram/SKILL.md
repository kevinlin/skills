---
name: architecture-diagram
description: 'Use when the user needs an architecture or system diagram, a CI/CD, build, or release pipeline, an ETL or data pipeline, a deployment flow, a left-to-right component or stage flow, or any diagram inline in a Markdown wiki or page. This skill applies even when Mermaid or ASCII seems more compatible.'
allowed-tools: Read, Write, Edit, Glob, Bash
permissions:
  - env
metadata:
  version: 1.2.2
---

# Architecture Diagram Generator

## Required Workflow

Every diagram request, however small, goes through these steps in order:

1. **Pick a style** from the Style Examples table and **read that file**. It holds the complete CSS block.
2. **Pick a layout** from the Layout Examples table by the shape of the system, and **read that file** too. Stacked tiers → a layer layout; a left-to-right stage flow (CI/CD, ETL, data pipeline) → [layouts/pipeline.md](layouts/pipeline.md); arrows between components → [layouts/connectors.md](layouts/connectors.md).
3. **Copy the template's CSS and class names verbatim** and fill in the user's components. Do not hand-roll inline styles, do not rename or re-prefix the `arch-*` classes, and do not invent a shorter class set.
4. **For every diagram or recommendation, state its selections together as one literal repository-relative `styles/<style>.md` path and one literal repository-relative `layouts/<layout>.md` path,** such as `styles/steel-blue.md` with `layouts/pipeline.md`. For a recommendation-only response covering multiple diagrams, group each diagram with its own style-and-layout pair. Do not include an alternative diagram tool.
5. **For a diagram-generation response, use this exact shape:** one short selection sentence naming the literal style and layout paths, followed immediately by the raw, unfenced HTML block copied from the chosen templates and using their `arch-*` class vocabulary. The diagram's final closing `</div>` is the response's final content. For multiple generated diagrams, repeat the selection-sentence-and-HTML pair for each diagram, with the final diagram's closing `</div>` as the response's final content.

### Minimum skeletons

If you answer without opening a style or layout file, these are the shapes to expand — never anything else. Colors come from the chosen style file.

**Stacked layers** (default shape):

<div style="width: 900px; box-sizing: border-box; position: relative;">
  <style scoped>
    .arch-title { text-align: center; font-size: 20px; font-weight: 600; color: #333; margin-bottom: 16px; }
    .arch-wrapper { display: flex; gap: 12px; }.arch-main { flex: 1; min-width: 0; }
    .arch-layer { margin: 8px 0; padding: 14px; border-radius: 6px; border: 1px solid #ccc; background: #fafafa; }
    .arch-layer-title { font-size: 13px; font-weight: bold; margin-bottom: 10px; text-align: center; }
    .arch-grid { display: grid; gap: 8px; }.arch-grid-2 { grid-template-columns: repeat(2, 1fr); }.arch-grid-3 { grid-template-columns: repeat(3, 1fr); }
    .arch-box { border-radius: 4px; padding: 8px; text-align: center; font-size: 11px; font-weight: 600; color: #333; background: #fff; border: 1px solid #ddd; }
  </style>
  <div class="arch-title">System Architecture</div>
  <div class="arch-wrapper"><div class="arch-main">
    <div class="arch-layer user"><div class="arch-layer-title">User Layer</div><div class="arch-grid arch-grid-2"><div class="arch-box">Web UI</div><div class="arch-box">Public API</div></div></div>
    <div class="arch-layer application"><div class="arch-layer-title">Application Layer</div><div class="arch-grid arch-grid-2"><div class="arch-box">Service A</div><div class="arch-box">Service B</div></div></div>
    <div class="arch-layer data"><div class="arch-layer-title">Data Layer</div><div class="arch-grid arch-grid-2"><div class="arch-box tech">PostgreSQL</div><div class="arch-box tech">Redis</div></div></div>
  </div></div>
</div>

**Stage flow** (left-to-right pipelines — see [layouts/pipeline.md](layouts/pipeline.md)):

<div style="width: 1100px; box-sizing: border-box; position: relative;">
  <style scoped>
    .arch-pipeline { display: flex; gap: 0; align-items: stretch; }
    .arch-stage { flex: 1; padding: 14px; border: 1px solid #ccc; border-radius: 4px; background: #fafafa; display: flex; flex-direction: column; }
    .arch-stage-title { font-size: 12px; font-weight: 600; color: #555; text-align: center; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 10px; }
    .arch-arrow { display: flex; align-items: center; justify-content: center; width: 36px; flex-shrink: 0; font-size: 20px; color: #999; }
  </style>
  <div class="arch-title">Pipeline</div>
  <div class="arch-pipeline">
    <div class="arch-stage"><div class="arch-stage-title">Stage One</div><div class="arch-box">Tool</div></div>
    <div class="arch-arrow">→</div>
    <div class="arch-stage"><div class="arch-stage-title">Stage Two</div><div class="arch-box">Tool</div></div>
  </div>
</div>

**Arrows between components** (SVG overlay, orthogonal `arch-conn` paths — full reference in [layouts/connectors.md](layouts/connectors.md)):

<div style="position: relative;">
  <style scoped>
    .arch-conn { stroke: #94a3b8; stroke-width: 1.5; fill: none; }
    .arch-conn-dashed { stroke: #94a3b8; stroke-width: 1.5; fill: none; stroke-dasharray: 6 4; }
    .arch-conn-label { font-size: 9px; fill: #64748b; font-family: sans-serif; }
  </style>
  <!-- positioned boxes here -->
  <svg style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; overflow: visible;">
    <defs><marker id="arrowhead" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#94a3b8" stroke-width="1"/></marker></defs>
    <path d="M 200,72 L 200,90 L 400,90 L 400,108" class="arch-conn" marker-end="url(#arrowhead)"/>
    <text x="420" y="86" class="arch-conn-label">sync</text>
  </svg>
</div>

### Do not substitute inline styles

Keep the `<style scoped>` block and the `arch-*` classes even when the target is GitHub, GitLab or another Markdown renderer. Scoped style blocks and class-based CSS render there; swapping them for per-element `style="..."` attributes throws away the chosen style's palette and the shared class vocabulary. Do not offer Mermaid, ASCII art or an image as an "in case your renderer strips this" fallback — the HTML block is the answer.

**Quick Start:** Create HTML structure with flexible layout (single/double/triple column) → Define CSS styles for layers and grids → Add content with categorized panels → Use semantic colors for different layers.

## Critical Rules

### Rule 0: Always the Skill's HTML Vocabulary
**NON-NEGOTIABLE**, whatever the request wording:

- Every diagram is HTML + CSS from this skill. Never substitute ASCII art, box-drawing characters, Mermaid, or an image — not even for a small or "quick" diagram, and not as an alternative offered alongside the HTML.
- Use the skill's own class names verbatim: `arch-wrapper`, `arch-main`, `arch-layer`, `arch-box`, `arch-grid-N`, `arch-sidebar*`, `arch-pipeline`, `arch-stage`, `arch-arrow`, `arch-conn*`. Never rename or re-prefix them, and never replace them with ad-hoc inline styles. Copy the template from the chosen style and layout file instead of inventing markup.
- Pick the layout from the Layout Examples table by the shape of the system, not by habit. A left-to-right, stage-based flow (CI/CD, ETL, data pipeline) uses [layouts/pipeline.md](layouts/pipeline.md) — `arch-pipeline` with `arch-stage` columns separated by `arch-arrow` — not stacked `arch-layer` blocks.

### Rule 1: Direct HTML Embedding
**IMPORTANT**: Write architecture diagrams as direct HTML in Markdown. **NEVER** use code blocks (` ```html `). The HTML should be embedded directly in the document without any fencing.

This holds when the user asks for "the HTML", asks for something to paste into Markdown, or asks for source. Markdown renders raw HTML; a fence would show the source instead of the diagram, so the raw block *is* the deliverable. Fence it only if the user explicitly says they want to see the code rather than the rendered diagram.

### Rule 2: No Empty Lines in HTML Structure
**CRITICAL**: Do NOT add any empty lines within the HTML architecture diagram structure. Keep the entire HTML block continuous to prevent parsing errors.

### Rule 3: Incremental Creation Approach
**RECOMMENDED**: Create architecture diagrams in multiple steps:
1. **First**: Create the overall framework (wrapper, sidebars, main structure) and define all CSS styles
2. **Second**: Add layer containers with titles
3. **Third**: Fill in components layer by layer
4. **Fourth**: Add detailed content and refinements

### Rule 4: Flexible Layout Structure
Architecture diagrams can use flexible layouts based on complexity:
- **Single Column**: Main content only (for simple architectures)
- **Two Column**: Main content + one sidebar (left or right)
- **Three Column**: Full layout with both sidebars (for complex systems)
  - **Left Sidebar**: Supporting systems (monitoring, operations, analytics)
  - **Main Content**: Core architecture layers (user, application, data, infrastructure)
  - **Right Sidebar**: Cross-cutting concerns (security, compliance, governance)

### Rule 5: Layer-Based Organization
Each layer should have:
- Clear semantic meaning (User, Application, AI/Logic, Data, Infrastructure)
- Consistent color coding
- Grid-based layout for components
- Appropriate nesting for sub-components

### Rule 6: Color Semantics
Use consistent semantic meaning for layers — the exact color palette varies by style (see examples). The standard semantic mapping:
- **User Layer** — user-facing interfaces and clients
- **Application Layer** — business logic and API services
- **AI/Logic Layer** — intelligence, rules, processing engines
- **Data Layer** — databases, caches, storage
- **Infrastructure Layer** — containers, networking, DevOps
- **External Services** — third-party APIs, cloud services (typically dashed border)

## Style Examples

Choose a visual style that matches your project's tone and audience. Each example contains a complete, copy-ready HTML template. **Voice** is the style's typographic personality (system fonts only — no web-font loading); **Context it serves** is the audience it fits best.

**See them all at once:** open [gallery.html](gallery.html) in a browser — every style rendered side by side in its own isolated frame. Regenerate after editing any style with `python3 scripts/build_gallery.py`.

**Export a diagram to PNG:** `python3 scripts/html_to_png.py <diagram.html | styles/name.md> -o out.png` — renders via a headless browser, cropped tight at 2x. Auto-detects a backend: the Playwright package, else `playwright-cli` (Homebrew), else an installed Chrome/Chromium/Edge. See [README.md](README.md#export-to-png).

| # | Style | File | Voice | Context it serves |
|---|---|---|---|---|
| 1 | **Steel Blue** | [styles/steel-blue.md](styles/steel-blue.md) | Georgia serif, blue-gray monochrome | Consulting reports, banking/finance, government projects, RFP proposals |
| 2 | **Ember Warm** | [styles/ember-warm.md](styles/ember-warm.md) | Palatino book-serif, warm editorial | Retail/e-commerce, education platforms, lifestyle brands, cultural institutions |
| 3 | **Neon Dark** | [styles/neon-dark.md](styles/neon-dark.md) | Monospace throughout, terminal / cyber | Tech talks, developer conferences, gaming platforms, cybersecurity dashboards |
| 4 | **Stark Block** | [styles/stark-block.md](styles/stark-block.md) | Arial Black uppercase, poster | Creative studios, education platforms, indie developers, tech blogs |
| 5 | **Ocean Teal** | [styles/ocean-teal.md](styles/ocean-teal.md) | Helvetica, airy coastal | Travel platforms, logistics/shipping, green tech, weather/ocean projects |
| 6 | **Dusk Glow** | [styles/dusk-glow.md](styles/dusk-glow.md) | Tight, heavy display sans | Social media, entertainment platforms, martech, content creation tools |
| 7 | **Rose Bloom** | [styles/rose-bloom.md](styles/rose-bloom.md) | Didot / Georgia italic, couture | Fashion/beauty, luxury brands, wedding platforms, premium memberships |
| 8 | **Sage Forest** | [styles/sage-forest.md](styles/sage-forest.md) | Humanist sans, calm | Healthcare, agritech, clean energy, sustainability, bioinformatics |
| 9 | **Frost Clean** | [styles/frost-clean.md](styles/frost-clean.md) | Sans titles + monospace data labels | Design tools, developer docs, API references, minimalist SaaS |
| 10 | **Indigo Deep** | [styles/indigo-deep.md](styles/indigo-deep.md) | Uppercase, wide-tracked sans | Brand-consistent systems, enterprise white papers, internal platforms |
| 11 | **Pastel Mix** | [styles/pastel-mix.md](styles/pastel-mix.md) | Rounded-friendly bold sans | SaaS products, startups, general tech architecture, product docs |
| 12 | **Slate Dark** | [styles/slate-dark.md](styles/slate-dark.md) | Neutral Helvetica, dark mode | Enterprise dark mode, internal tools, developer dashboards |
| 13 | **Zühlke** | [styles/zuhlke.md](styles/zuhlke.md) | AA Zuehlke + Lato two-font, flush left | Zühlke brand design |

## Layout Examples

Choose a layout structure that fits your architecture's complexity. Layouts use wireframe style (no colors) to focus on structural patterns. Combine any layout with any style above.

| # | Layout | File | Best For |
|---|---|---|---|
| 1 | **Three-Column** | [layouts/three-column.md](layouts/three-column.md) | Complex systems with cross-cutting concerns and monitoring sidebars |
| 2 | **Single Stack** | [layouts/single-stack.md](layouts/single-stack.md) | Simple services, microservice detail views, focused documentation |
| 3 | **Left Sidebar** | [layouts/left-sidebar.md](layouts/left-sidebar.md) | Systems with operations/monitoring emphasis, DevOps-centric views |
| 4 | **Right Sidebar** | [layouts/right-sidebar.md](layouts/right-sidebar.md) | Systems with security/compliance emphasis, governance-focused views |
| 5 | **Pipeline** | [layouts/pipeline.md](layouts/pipeline.md) | Data pipelines, CI/CD flows, ETL processes, horizontal stage-based flows |
| 6 | **Two-Column Split** | [layouts/two-column-split.md](layouts/two-column-split.md) | Before/after comparisons, dual-system views, migration architecture |
| 7 | **Dashboard** | [layouts/dashboard.md](layouts/dashboard.md) | System overviews with KPIs, monitoring dashboards, executive summaries |
| 8 | **Grid Catalog** | [layouts/grid-catalog.md](layouts/grid-catalog.md) | Service catalogs, component libraries, equal-weight microservices |
| 9 | **Banner + Center** | [layouts/banner-center.md](layouts/banner-center.md) | Gateway-centric architectures, user-facing systems with shared infrastructure |
| 10 | **Nested Containers** | [layouts/nested-containers.md](layouts/nested-containers.md) | Cloud deployments, VPC/network topology, environment isolation |
| 11 | **Layer Layouts** | [layouts/layer-layouts.md](layouts/layer-layouts.md) | Per-layer layout patterns: grid, sub-group, product group, KPI, vertical stack, zones, inline pipeline, mixed width |
| 12 | **Connectors** | [layouts/connectors.md](layouts/connectors.md) | SVG overlay connectors between components: solid/dashed lines, arrows, labels, curved & orthogonal paths |
| 13 | **Hub & Spoke** | [layouts/hub-spoke.md](layouts/hub-spoke.md) | Integration platforms, API hubs, event-driven architectures, ESB patterns |

## Advanced Features

**NOTE**: These advanced components require additional CSS styles. Add these to your `<style scoped>` section:

```css
.arch-product-group { display: flex; gap: 10px; }
.arch-product { flex: 1; border-radius: 8px; padding: 10px; background: rgba(255, 255, 255, 0.6); border: 1px dashed #d97706; }
.arch-product-title { font-size: 12px; font-weight: bold; color: #92400e; margin-bottom: 8px; text-align: center; }
.arch-subgroup { display: flex; gap: 8px; margin-top: 8px; }
.arch-subgroup-box { flex: 1; border-radius: 6px; padding: 8px; background: rgba(255, 255, 255, 0.5); border: 1px solid rgba(0, 0, 0, 0.08); }
.arch-subgroup-title { font-size: 10px; font-weight: bold; color: #374151; text-align: center; margin-bottom: 6px; }
.arch-user-types { display: flex; gap: 4px; justify-content: center; margin-top: 6px; }
.arch-user-tag { font-size: 9px; padding: 2px 6px; border-radius: 10px; background: rgba(59, 130, 246, 0.15); color: #1d4ed8; }
/* SVG connector lines between components */
.arch-conn { stroke: #94a3b8; stroke-width: 1.5; fill: none; }
.arch-conn-dashed { stroke: #94a3b8; stroke-width: 1.5; fill: none; stroke-dasharray: 6 4; }
.arch-conn-label { font-size: 9px; fill: #64748b; font-family: sans-serif; }
```

### Custom Product Groups
For complex applications with multiple products/modules:

```html
<div class="arch-product-group">
  <div class="arch-product">
    <div class="arch-product-title">🎯 Product A</div>
    <div class="arch-grid arch-grid-2">
      <div class="arch-box">Feature 1<br><small>Description</small></div>
      <div class="arch-box highlight">Feature 2<br><small>Key Feature</small></div>
    </div>
  </div>
  <div class="arch-product">
    <div class="arch-product-title">📊 Product B</div>
    <div class="arch-grid arch-grid-2">
      <div class="arch-box">Feature 3<br><small>Description</small></div>
      <div class="arch-box">Feature 4<br><small>Description</small></div>
    </div>
  </div>
</div>
```

### Sub-grouped Components
For detailed breakdowns within layers:

```html
<div class="arch-subgroup">
  <div class="arch-subgroup-box">
    <div class="arch-subgroup-title">Component Group A</div>
    <div class="arch-grid arch-grid-3">
      <div class="arch-box tech">Service 1<br><small>Details</small></div>
      <div class="arch-box tech">Service 2<br><small>Details</small></div>
      <div class="arch-box tech">Service 3<br><small>Details</small></div>
    </div>
  </div>
  <div class="arch-subgroup-box">
    <div class="arch-subgroup-title">Component Group B</div>
    <div class="arch-grid arch-grid-2">
      <div class="arch-box tech">Service 4<br><small>Details</small></div>
      <div class="arch-box tech">Service 5<br><small>Details</small></div>
    </div>
  </div>
</div>
```

### User Types/Tags

```html
<div class="arch-user-types">
  <span class="arch-user-tag">Admin Users</span>
  <span class="arch-user-tag">End Users</span>
  <span class="arch-user-tag">API Clients</span>
  <span class="arch-user-tag">Partners</span>
</div>
```

### Metrics and KPIs

```html
<div class="arch-sidebar-item metric">99.9% Uptime</div>
<div class="arch-sidebar-item metric">&lt;200ms Response</div>
<div class="arch-sidebar-item metric">1M+ Users</div>
```

### SVG Connectors Between Components
Use an SVG overlay to draw orthogonal (right-angle) connectors between components. **Always use `<path>` with `M`/`L` commands for strictly horizontal and vertical segments. Do NOT use `<line>`, Bézier curves, or diagonal lines.** See [layouts/connectors.md](layouts/connectors.md) for full reference.

```html
<!-- Wrap diagram content in a relative container -->
<div style="position: relative;">
  <!-- ...layers and components here... -->
  <!-- SVG overlay as last child -->
  <svg style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; overflow: visible;">
    <defs>
      <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
        <path d="M0,0 L8,3 L0,6" fill="none" stroke="#94a3b8" stroke-width="1"/>
      </marker>
    </defs>
    <!-- Orthogonal solid arrow (vertical → horizontal → vertical) -->
    <path d="M 200,72 L 200,90 L 400,90 L 400,108" class="arch-conn" marker-end="url(#arrowhead)"/>
    <!-- Orthogonal dashed line -->
    <path d="M 600,72 L 600,90 L 600,90 L 600,108" class="arch-conn-dashed" marker-end="url(#arrowhead)"/>
    <!-- Label -->
    <text x="420" y="86" class="arch-conn-label">data flow</text>
  </svg>
</div>
```

## Styling Reference

### Common Classes (shared across all styles)
- `.arch-wrapper` — flex container for sidebar + main layout
- `.arch-sidebar` — fixed-width sidebar column
- `.arch-main` — flexible main content area
- `.arch-layer` — layer container (add semantic class: `.user`, `.application`, `.ai`, `.data`, `.infra`, `.external`)
- `.arch-box` — component box; `.arch-box.highlight` for key items; `.arch-box.tech` for smaller tech items
- `.arch-grid-2` to `.arch-grid-6` — grid column layouts
- `.arch-sidebar-panel` — sidebar panel container
- `.arch-sidebar-item` — sidebar item; `.arch-sidebar-item.metric` for highlighted metrics

## Best Practices

### HTML Usage Guidelines

1. **Direct embedding only** — Always embed HTML directly in Markdown, never use ` ```html ` code blocks
2. **No empty lines in structure** — Keep the entire HTML block continuous without any empty lines
3. **Incremental development** — Build diagrams step by step:
   - Start with basic framework and layout structure (single/two/three column as needed)
   - Add empty layer containers with proper CSS classes
   - Fill in content layer by layer from top to bottom
   - Refine content and add highlights last

### Architecture Design

1. **Keep layers logically separated** — Each layer should represent a clear architectural tier
2. **Use consistent naming** — Follow naming conventions for components and services
3. **Highlight key components** — Use `.highlight` class for critical components
4. **Add technical details** — Include technology stack info in `<small>` tags
5. **Balance information density** — Don't overcrowd components with text
6. **Use icons sparingly** — Add emojis to titles for visual hierarchy
7. **Maintain color semantics** — Stick to the established color meanings
8. **Consider responsive design** — Grids automatically adapt to content
