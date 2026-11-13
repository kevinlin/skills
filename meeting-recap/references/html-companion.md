# HTML companion: body.html for the recap shell

The HTML companion is the recap .md rewritten as one shareable page. You write `body.html` by hand from the finished .md; nothing generates it. The two are kept in sync by hand: when the .md changes, change `body.html` to match and rebuild.

`assets/recap-shell.html` holds the head, all CSS, the theme switch script and the tail scripts (TOC scrollspy, figure lightbox). `body.html` holds everything from the skip link to the footer. Never put a `<style>` block in `body.html`. If a component is missing, add it to the shell so every later page gets it.

## Contents

1. Build
2. Skeleton
3. Markdown to HTML
4. Figures and captures
5. Rules that break things when ignored

## 1. Build

```sh
python3 <skill>/scripts/build_html.py body.html <Slug>-recap.html --title "Short name" --description "One sentence."
```

It fills `{{title}}`, `{{description}}`, `{{theme_key}}` (derived from the output file name) and `{{body}}`. Then it inlines `diagram/F*.svg`, read from next to the output file, into each empty `<div class="fig-frame" data-fig="...">`. Check that the "N figure(s) inlined" count matches the number of figures. Re-run after any change to the body or a figure.

## 2. Skeleton

`body.html` starts at the skip link. No `<html>`, `<head>` or `<body>` tags: the shell supplies them.

```html
<a class="skip" href="#main">Skip to main content</a>

<header class="masthead">
  <div class="masthead-in">
    <div class="theme" role="radiogroup" aria-label="Colour theme">
      <input type="radio" name="theme" id="theme-system" value="system" checked><label for="theme-system">Auto</label>
      <input type="radio" name="theme" id="theme-light" value="light"><label for="theme-light">Light</label>
      <input type="radio" name="theme" id="theme-dark" value="dark"><label for="theme-dark">Dark</label>
      <input type="radio" name="theme" id="theme-sepia" value="sepia"><label for="theme-sepia">Sepia</label>
    </div>
    <p class="eyebrow">{{Our firm}}<span class="sep">/</span>Internal meeting recap<span class="sep">/</span>Not for {{Client}} distribution</p><span class="status">Draft</span>
    <h1>{{Meeting title}}</h1>
    <p class="deck">{{Two or three sentences: what changed, what is decided, what is blocked.}}</p>
    <dl class="meta">
<div><dt>Date</dt><dd>{{9 October 2026, in the office, 47 minutes}}</dd></div>
<div><dt>{{Client}}</dt><dd>{{Name (role in this session)}}</dd></div>
<div><dt>{{Our firm}}</dt><dd>{{Name (role) · Name (role)}}</dd></div>
<div><dt>Status</dt><dd>Draft. {{What it was built from, and who has not checked it yet}}</dd></div>
<div><dt>Source</dt><dd><a href="{{transcript.md}}">Transcript</a> · <a href="{{slides.pdf}}">slides</a> · <a href="{{recording.m4a}}">recording</a></dd></div>
<div><dt>Vocabulary</dt><dd><a href="{{Glossary.md}}">Glossary.md</a>, updated from this session; see §{{N}}</dd></div>
    </dl>
    <p class="related">Related: <a href="{{earlier-recap.html}}">{{Earlier meeting, date}}</a>.
    Timestamps such as <span class="ts">0:18:34</span> point into the transcript. {{How far the transcript was checked against the audio.}}</p>
  </div>
</header>

<div class="shell">
  <nav class="toc" aria-label="Contents">
    <p class="toc-title">Contents</p>
    <ol>
<li><a href="#sec1"><span class="num">1</span>The short version</a></li>
<li><a href="#sec2"><span class="num">2</span>{{Short label}}</a></li>
<li><a href="#sec9"><span class="num">9</span>Raw captures</a></li>
    </ol>
  </nav>
  <main id="main">

<section id="sec1" aria-labelledby="h-sec1">
<h2 id="h-sec1"><span class="num">01</span>The short version</h2><div class="rule"></div>
<ul>
<li><strong>{{Lead sentence.}}</strong> {{Detail.}} <span class="ts">0:12:05</span></li>
</ul>
</section>

<!-- one <section id="secN"> per ## heading of the .md, same h2 pattern -->

<section id="sec9" aria-labelledby="h-sec9">
<h2 id="h-sec9"><span class="num">09</span>Raw captures</h2><div class="rule"></div>
<p>The source images the figures were re-drawn from. Click one to enlarge it.</p>
<div class="captures">
<!-- one a.cap-card per image, see section 4 -->
</div>
</section>

  </main>
</div>

<footer>
  <div class="footer-in">
    <p>Written on {{date}} from {{the transcript, the slides and the whiteboard photos}}. Internal only.</p>
  </div>
</footer>
```

## 3. Markdown to HTML

| In the .md | In body.html |
|---|---|
| `## 3. Heading` | `<section id="sec3" aria-labelledby="h-sec3">` + `<h2 id="h-sec3"><span class="num">03</span>Heading</h2><div class="rule"></div>`, plus a TOC entry |
| `### Sub-heading` | `<h3>Sub-heading</h3>`; a TOC entry for it, if any, is `<a class="sub" href="#...">` |
| `(0:18:34)` | `<span class="ts">0:18:34</span>` at the end of the sentence, one chip per time. A range keeps its en dash in one chip or shortens to its start |
| §1 bold-lead bullets | `<li><strong>Lead.</strong> Detail.</li>` inside `#sec1 > ul`; they render as cards. The last card gets the accent border, so put the blocker or biggest risk last |
| Other bold-lead bullets | Same `<li><strong>…</strong> …</li>`, rendered as a plain list |
| Numbered "how it ran" list | `<ol class="steps"><li>…</li></ol>` |
| A quote worth pulling out | `<figure class="pull"><blockquote>Quote.</blockquote><figcaption><cite>Speaker role, on topic · <span class="ts">0:30:31</span></cite></figcaption></figure>`. Use it rarely; other quotes stay inline in their bullets |
| Blocker or risk | `<div class="callout warn"><h4>Blocked</h4><p>…</p></div>`; a neutral note or decision is `<div class="callout">` |
| Status words in a table | `<span class="st">Decided</span>`, `<span class="st open">Open</span>` (open, ask, blocked), `<span class="st check">Check</span>` (to verify). A short note may follow the chip |
| Table, short cells | `<div class="table-wrap"><table class="c-table">…</table></div>`: `#`, item, soft middle columns, emphasised last column |
| Table, prose middle columns | `<table class="c-table wide-table">`, e.g. "where sources disagree" |
| Open-questions table | `<table class="c-table oq-table">` with columns `#`, question, why it matters |
| Next steps `**Owner:** action` | `<li><span class="owner">Owner</span>Action.</li>` |
| Provenance `[Board]`, `[Inferred]` | `<span class="pv">Board</span>`, `<span class="pv inf">Inferred</span>` for our own unchecked reading |
| Key/value run (access items, rulings) | `<dl class="kv"><div><dt>Item</dt><dd>Value</dd></div></dl>` |
| `` `code` `` | `<code>code</code>` |
| Figure + italic caption | see section 4 |

The .md may use straight quotes; body.html uses typographic ones (’ “ ”), and `&amp;` for a literal ampersand.

## 4. Figures and captures

A figure in the .md:

```markdown
![Release plan](diagram/F2_release-plan.svg)

*Figure 2: The release plan slide, re-drawn. [Original photo](<captured-image/Release-plan.png>).*
```

becomes:

```html
<figure id="figure-2">
<div class="fig-frame" data-fig="F2_release-plan"></div>
<figcaption><span class="tag">Figure 2</span><span class="cap">The release plan slide, re-drawn.</span><span class="src"><a class="photo" href="captured-image/Release-plan.png">Original photo</a> · <a href="diagram/F2_release-plan@2x.png">PNG</a></span></figcaption>
</figure>
```

- `data-fig` is the SVG file name without `.svg`. The part before the first `_` (`F2`) prefixes every id inside the SVG, so two figures never share a marker.
- Leave the div empty. The build fills it; a missing SVG stops the build.
- "Original photo" (or "Original slide", "Original screenshot") and the PNG link both open in the lightbox; modifier-clicks still open the file.
- Figures sit on a light card in every theme, so draw them with light backgrounds and dark text.
- Keep the .md's figure numbers, even when a figure appears out of order.

A raster snapshot used as a figure (a screenshot of a page or tool shown in the meeting, not re-drawn) goes in the same frame without `data-fig`:

```html
<figure id="figure-1">
<div class="fig-frame"><a class="shot" href="captured-image/Roadmap-overview.png"><img src="captured-image/Roadmap-overview.png" alt="…" width="1722" height="1800" loading="lazy"></a></div>
<figcaption><span class="tag">Figure 1</span><span class="cap">…, snapshot.</span><span class="src"><a href="captured-image/Roadmap-overview.png">PNG</a></span></figcaption>
</figure>
```

`a.shot` opens in the lightbox. The build reports 0 figures inlined for these; that is expected.

Each raw capture is one card in the `captures` grid:

```html
<a class="cap-card" href="captured-image/Release-plan.png"><img src="captured-image/Release-plan.png" alt="Photo of the release plan slide" loading="lazy" width="1800" height="1168"><span><b>Release plan</b> slide · Figure 2</span></a>
```

Give `width` and `height` the image's real pixel size so the grid doesn't jump while images load. The `alt` text is what the lightbox shows. Print hides the gallery.

## 5. Rules that break things when ignored

- Section ids are `sec1` to `secN`, h2 ids are `h-secN`, and every TOC `href` matches a section id. The scrollspy finds sections through the TOC links.
- §1 must be `id="sec1"`: the card grid is keyed on it.
- The h2 number is two digits (`01`); the TOC number is plain (`1`). TOC labels may be shorter than the h2.
- Every table goes inside `div.table-wrap`. Without it, a wide table pushes the page sideways on a phone.
- No inline `style=` and no per-page CSS. Check a new page at 400px wide and in dark mode before sharing it.
