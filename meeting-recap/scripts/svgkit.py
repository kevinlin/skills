#!/usr/bin/env python3
"""Light-theme SVG helpers for meeting figures. Copy this file into the meeting's
diagram/_src/ next to _figs.py and import it from there; don't import it from the
skill path, or the figures stop regenerating when the skill moves.

Layout follows baoyu-diagram's rules (mask rect under each box, per-colour arrow
markers, legend outside the content); colours and type scale are light and readable.
Every text goes through t(), which refuses anything under 12px. chip() refuses a
label that would overflow its box, because SVG text never wraps.

    from svgkit import head, t, box, region, line, chip, legend_item, save
    s = head(1200, 600, "Title", "Re-drawn from the whiteboard; dashed = from the transcript")
    s += chip(40, 100, 200, 44, "Order service", "primary")
    save(OUT / "F1_order-flow", s)
"""
from html import escape
from pathlib import Path

BG = "#FDFCFD"
INK = "#1F2126"
SUB = "#5B5E66"
AMBER = "#B45309"   # open / at-risk text
MIN_PX = 12
CHAR_EM = 0.6       # JetBrains Mono advance width: 7.2 px per char at 12px
CAT = {  # fill, stroke
    "primary": ("#E6F4F8", "#0E7490"),
    "secondary": ("#E7F5EE", "#047857"),
    "tertiary": ("#F3ECF4", "#6E3F72"),
    "accent": ("#FDF3E0", "#B45309"),
    "alert": ("#FBE9EE", "#BE123C"),
    "connector": ("#FDEEE2", "#C2410C"),
    "neutral": ("#F3F3F5", "#6B7280"),
    "highlight": ("#E8EFFB", "#1D4ED8"),
}


def text_w(s, size=MIN_PX):
    return len(s) * size * CHAR_EM


def head(w, h, title, subtitle):
    markers = "".join(
        f'<marker id="arrow-{k}" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">'
        f'<polygon points="0 0, 10 3.5, 0 7" fill="{s}"/></marker>'
        for k, (_, s) in CAT.items())
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" font-family="JetBrains Mono, SF Mono, Menlo, monospace">\n'
        '<style>@import url("https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&amp;display=swap");'
        " text{font-family:'JetBrains Mono','SF Mono','Cascadia Code',monospace;}</style>\n"
        '<defs><pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">'
        '<path d="M 40 0 L 0 0 0 40" fill="none" stroke="#EFEAF0" stroke-width="0.5"/></pattern>'
        f'{markers}</defs>\n'
        f'<rect width="{w}" height="{h}" fill="{BG}"/><rect width="{w}" height="{h}" fill="url(#grid)"/>\n'
        + t(30, 44, title, 20, INK, 700) + t(30, 68, subtitle, 12, SUB))


def t(x, y, s, size=MIN_PX, fill=INK, weight=400, anchor="start", italic=False):
    assert size >= MIN_PX, f"font under {MIN_PX}px: {s!r}"
    st = ' font-style="italic"' if italic else ""
    return (f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" font-weight="{weight}" '
            f'text-anchor="{anchor}"{st}>{escape(s)}</text>\n')


def box(x, y, w, h, cat, dashed=False, rx=6, sw=1.5):
    """The first rect masks the grid in the ground colour; baoyu's dark mask would turn boxes black."""
    fill, stroke = CAT[cat]
    d = ' stroke-dasharray="6,4"' if dashed else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{BG}"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>\n')


def region(x, y, w, h, cat, label=None):
    s = CAT[cat][1]
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="none" stroke="{s}" stroke-width="1" stroke-dasharray="8,4"/>\n'
    return out + (t(x + 14, y + 20, label, 12, s, 600) if label else "")


def line(pts, cat="neutral", arrow=True, dashed=False, sw=1.5):
    s = CAT[cat][1]
    d = "M " + " L ".join(f"{a},{b}" for a, b in pts)
    m = f' marker-end="url(#arrow-{cat})"' if arrow else ""
    da = ' stroke-dasharray="5,4"' if dashed else ""
    return f'<path d="{d}" fill="none" stroke="{s}" stroke-width="{sw}"{da}{m}/>\n'


def chip(x, y, w, h, label, cat, size=MIN_PX, dashed=False):
    """Centred multi-line label in a box; split lines with \\n."""
    lines = label.split("\n")
    for ln in lines:
        assert text_w(ln, size) <= w - 12, f"{ln!r} overflows a {w}px chip at {size}px"
    out = box(x, y, w, h, cat, dashed=dashed, rx=5, sw=1.2)
    y0 = y + h / 2 + size * 0.35 - (len(lines) - 1) * (size + 2) / 2
    for i, ln in enumerate(lines):
        out += t(x + w / 2, y0 + i * (size + 2), ln, size, INK, 600, "middle")
    return out


def legend_item(x, y, cat, label, dashed=False):
    return box(x, y - 11, 22, 14, cat, dashed=dashed, rx=3, sw=1.2) + t(x + 30, y, label, 12, SUB)


def save(path, svg):
    """path without extension, e.g. OUT / "F1_order-flow"."""
    p = Path(f"{path}.svg")
    p.write_text(svg + "</svg>\n", encoding="utf-8")
    print("wrote", p.name)
