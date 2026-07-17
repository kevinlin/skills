#!/usr/bin/env python3
"""Regenerate gallery.html — a one-page, isolated preview of every style.

Reads each styles/*.md template and stitches them into a single HTML page.
Each template renders in its own <iframe srcdoc> because the `scoped`
attribute on <style> is not honoured by browsers: 13 identical class sets
on one page would otherwise clobber each other. Same reason a real document
copies one template at a time, not several.

Usage:  python3 scripts/build_gallery.py
Output: gallery.html at the skill root (open it in any browser).
Run this after changing any styles/*.md so the gallery stays in sync.
"""
import pathlib, re

SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent
STYLES_DIR = SKILL_DIR / "styles"
OUT = SKILL_DIR / "gallery.html"

# Grouped cool -> warm -> light-neutral -> dark for easy scanning.
ORDER = [
    "steel-blue", "indigo-deep", "ocean-teal", "sage-forest",
    "ember-warm", "dusk-glow", "rose-bloom", "pastel-mix",
    "frost-clean", "stark-block", "neon-dark", "slate-dark",
]


def extract_template(md: str) -> str:
    """Everything after the "## Template" heading is the raw HTML block."""
    idx = md.index("## Template")
    return md[idx + len("## Template"):].strip()


def first_line(md: str) -> str:
    m = re.search(r"^\*\*Style\*\*:\s*(.+)$", md, re.M)
    return m.group(1).strip() if m else ""


def typ_row(md: str) -> str:
    m = re.search(r"^\|\s*Typography\s*\|\s*(.+?)\s*\|", md, re.M)
    return m.group(1).strip() if m else ""


def srcdoc_escape(html: str) -> str:
    return html.replace("&", "&amp;").replace('"', "&quot;")


def build() -> str:
    cards = []
    for name in ORDER:
        md = (STYLES_DIR / f"{name}.md").read_text()
        tpl = extract_template(md)
        doc = ("<!doctype html><meta charset='utf-8'>"
               "<body style='margin:0;padding:16px;background:#eceff3;'>" + tpl + "</body>")
        cards.append(f"""
  <section class="card">
    <div class="meta">
      <h2>{name}</h2>
      <p class="voice">{typ_row(md)}</p>
      <p class="desc">{first_line(md)}</p>
    </div>
    <iframe loading="lazy" srcdoc="{srcdoc_escape(doc)}"></iframe>
  </section>""")

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>architecture-diagram - style gallery</title>
<style>
  :root {{ color-scheme: light; }}
  body {{ margin:0; font-family: system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;
         background:#f6f7f9; color:#1f2430; }}
  header {{ padding:28px 32px 8px; }}
  header h1 {{ margin:0 0 4px; font-size:24px; letter-spacing:-.3px; }}
  header p {{ margin:0; color:#5b6572; font-size:14px; }}
  .grid {{ padding:20px 24px 60px; display:flex; flex-direction:column; gap:34px; }}
  .card {{ background:#fff; border:1px solid #e3e7ec; border-radius:12px; overflow:hidden;
           box-shadow:0 1px 3px rgba(15,23,42,.05); }}
  .meta {{ padding:14px 18px 10px; border-bottom:1px solid #eef1f4; }}
  .meta h2 {{ margin:0; font-size:16px; font-family:ui-monospace,Menlo,monospace; color:#0f172a; }}
  .voice {{ margin:4px 0 2px; font-size:13px; font-weight:600; color:#334155; }}
  .desc {{ margin:0; font-size:12px; color:#78838f; }}
  iframe {{ display:block; width:100%; height:780px; border:0; background:#eceff3; }}
</style></head>
<body>
<header>
  <h1>architecture-diagram - style gallery</h1>
  <p>12 styles, each isolated in its own frame. Grouped cool -> warm -> light-neutral -> dark. Regenerate with <code>python3 scripts/build_gallery.py</code>.</p>
</header>
<div class="grid">{''.join(cards)}</div>
</body></html>"""


if __name__ == "__main__":
    OUT.write_text(build())
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes, {len(ORDER)} styles)")
