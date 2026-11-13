#!/usr/bin/env python3
"""Assemble the HTML recap companion: assets/recap-shell.html + a hand-written body,
then inline every figure so the page is one shareable file.

  build_html.py <body.html> <out.html> --title "Short name" --description "One sentence."

body.html holds everything from the masthead to the footer, with each figure as an
empty <div class="fig-frame" data-fig="F1_slug"></div>; the SVG comes from
diagram/F1_slug.svg next to <out.html>. On the way in:
  * the Google Fonts @import is dropped, because the page loads its own faces;
  * class="mono" becomes "fmono", because the page's .mono rule (font-size:.88em)
    would shrink figure labels under 12px;
  * every id and url(#id) gets the figure prefix (F1-grid, F1-arrow-primary), because
    SVG ids are global in a page and two figures would otherwise share one marker.
Re-run after any figure or body change.
"""
import argparse, re
from html import escape
from pathlib import Path

SHELL = Path(__file__).resolve().parent.parent / "assets" / "recap-shell.html"
FRAME = re.compile(r'(<div class="fig-frame" data-fig="([^"]+)">)(.*?)(</div>)', re.S)


def prepare(svg_text, prefix):
    svg = svg_text[svg_text.index("<svg"):].strip()
    svg = re.sub(r'@import url\("[^"]*"\);', "", svg)
    svg = svg.replace('class="mono"', 'class="fmono"').replace(".mono{", ".fmono{")
    svg = re.sub(r'id="([^"]+)"', lambda m: f'id="{prefix}-{m.group(1)}"', svg)
    return re.sub(r'url\(#([^)]+)\)', lambda m: f'url(#{prefix}-{m.group(1)})', svg)


def inline(html, diagram_dir):
    filled = []

    def repl(m):
        open_tag, name, _old, close_tag = m.groups()
        src = diagram_dir / f"{name}.svg"
        if not src.exists():
            raise SystemExit(f"missing figure: {src}")
        filled.append(name)
        return f'{open_tag}\n{prepare(src.read_text(encoding="utf-8"), name.split("_")[0])}\n{close_tag}'

    return FRAME.sub(repl, html), filled


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("body"); ap.add_argument("out")
    ap.add_argument("--title", required=True); ap.add_argument("--description", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    page = (SHELL.read_text(encoding="utf-8")
            .replace("{{title}}", escape(a.title))
            .replace("{{description}}", escape(a.description, quote=True))
            .replace("{{theme_key}}", re.sub(r"[^a-z0-9]+", "-", out.stem.lower()) + "-theme")
            .replace("{{body}}", Path(a.body).read_text(encoding="utf-8")))
    page, filled = inline(page, out.parent / "diagram")
    out.write_text(page, encoding="utf-8")
    print(f"wrote {out} with {len(filled)} figure(s) inlined: {', '.join(filled) or 'none'}")


if __name__ == "__main__":
    main()
