#!/usr/bin/env python3
"""Each FAIL rule of scripts/check_recap.py fires once on a bad recap and never on a clean one.
Run: python3 tests/test_check_recap.py"""
import os, subprocess, sys, tempfile
from pathlib import Path

CHECK = Path(__file__).resolve().parent.parent / 'scripts' / 'check_recap.py'
GOOD_SVG = '<svg viewBox="0 0 10 10"><rect width="10" height="10" fill="#FDFCFD"/><text font-size="12">a</text></svg>'
BAD_SVG = '<svg viewBox="0 0 10 10"><rect width="10" height="10" fill="#0f172a"/><text font-size="9">a</text></svg>'
META = '| | |\n|---|---|\n' + ''.join(f'| {r} | x |\n' for r in
                                     ('Status', 'Date', 'Companion', 'Vocabulary', 'Source'))


def run(md_body, svg, png=True, html=None):
    d = Path(tempfile.mkdtemp())
    (d / 'diagram').mkdir()
    (d / 'diagram' / 'F1_x.svg').write_text(svg)
    if png:
        (d / 'diagram' / 'F1_x@2x.png').write_bytes(b'')
    (d / 'r.md').write_text(META + md_body)
    if html is not None:
        (d / 'r.html').write_text(html)
    (d / 't.md').write_text('**[0:00:05] Ana:** we ship in May\n\n**[0:10:00] Ben:** fine\n')
    p = subprocess.run([sys.executable, str(CHECK), str(d / 'r.md'), '--transcript', str(d / 't.md'),
                        '--ban', 'Old Name'], capture_output=True, text=True)
    return p.returncode, [l for l in p.stdout.splitlines() if l.startswith('FAIL')]


html_ok = ('<a href="#sec1">1</a> <a href="https://x.test/a">x</a> <a href="diagram/F1_x@2x.png">PNG</a>'
           '<p>Ana <span class="ts">0:00:05</span> <span class="ts">0:00:07</span></p>'
           '<div class="fig-frame" data-fig="F1_x"><svg></svg></div>')
code, fails = run('![F1](diagram/F1_x.svg)\n- **Ships in May** (0:00:05–0:00:09).\n', GOOD_SVG, html=html_ok)
assert code == 0 and not fails, fails

code, fails = run('[gone](missing.md) and the Old Name (0:59:00)\n', BAD_SVG, png=False,
                  html='{{body}}<div class="fig-frame" data-fig="F1_x"></div><a href="captured-image/gone.png">x</a>')
text = '\n'.join(fails)
for want in ('broken link missing.md', 'font sizes under 12px', 'dark ground', 'no F1_x@2x.png',
             'banned name "Old Name"', 'past the end', 'unfilled', 'is empty',
             'r.html: broken link captured-image/gone.png'):
    assert want in text, f'missing FAIL: {want}\n{text}'
assert code == 1
print('ok')
