#!/usr/bin/env python3
"""Mechanical checks on a recap before the verifier reads it. FAIL lines exit 1.

  check_recap.py <recap.md> [--transcript T.md] [--ban "Name"]... [--evidence]

FAIL  relative link or image that doesn't resolve
FAIL  figure under diagram/: font under 12px, dark ground, or no @2x.png beside it
FAIL  banned name anywhere in the .md or its .html companion
FAIL  timestamp past the end of the transcript
FAIL  .html companion with an unfilled {{slot}}, an empty figure frame, or a broken href/src
WARN  metadata row missing; .html timestamp the .md never cites (drift)

Glossary aliases are left to the verifier: most are ordinary words ("team", "step")
that are only wrong in context, so a word match drowns the real hits.

--evidence prints each timestamp the recap cites next to the transcript turn that covers
it, for the verifier to read claims against.
"""
import argparse, glob, html as html_lib, os, re, sys
from urllib.parse import unquote
from pathlib import Path

TS = re.compile(r'(?<![\d:])(\d{1,2}):(\d{2}):(\d{2})(?![\d:])')
HREF = re.compile(r'(?:href|src)="([^"]+)"')
LINK = re.compile(r'!?\[[^\]]*\]\((<[^>]+>|[^)\s]+)')
FONT = re.compile(r'font-size(?:="|:\s*)([0-9.]+)')
TURN = re.compile(r'^\*\*\[(\d+:\d{2}:\d{2})\] ([^:*]+):\*\* ?(.*)')
META = ('Status', 'Date', 'Companion', 'Vocabulary', 'Source')
out = {'FAIL': [], 'WARN': []}


def secs(h, m, s):
    return int(h) * 3600 + int(m) * 60 + int(s)


def report(kind, msg):
    out[kind].append(msg)


def check_links(md, text):
    for n, line in enumerate(text.splitlines(), 1):
        for m in LINK.finditer(line):
            target = m.group(1).strip('<>')
            if not resolves(md.parent, target):
                report('FAIL', f'{md.name}:{n} broken link {target.split("#")[0]}')


def resolves(base, target):
    """True for anchors, URLs and data: URIs, else whether the relative path exists."""
    target = unquote(html_lib.unescape(target)).split('#')[0]
    return not target or bool(re.match(r'[a-z]+:', target)) or (base / target).exists()


def dark(hex_):
    h = hex_.lstrip('#')
    h = ''.join(c * 2 for c in h) if len(h) == 3 else h[:6]
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b < 100


def check_figures(md):
    for svg in sorted(glob.glob(str(md.parent / 'diagram' / '*.svg'))):
        name, text = os.path.basename(svg), open(svg, encoding='utf-8').read()
        small = sorted({float(f) for f in FONT.findall(text) if float(f) < 12})
        if small:
            report('FAIL', f'{name}: font sizes under 12px: {small}')
        ground = re.search(r'<rect[^>]*width="(?:100%|[0-9.]+)"[^>]*fill="(#[0-9a-fA-F]{3,6})"', text)
        if ground and dark(ground.group(1)):
            report('FAIL', f'{name}: dark ground {ground.group(1)}; figures are light-theme')
        if not os.path.exists(svg[:-4] + '@2x.png'):
            report('FAIL', f'{name}: no {name[:-4]}@2x.png beside it')


def check_bans(name, text, bans):
    for term in bans:
        for n, line in enumerate(text.splitlines(), 1):
            if term.lower() in line.lower():
                report('FAIL', f'{name}:{n} banned name "{term}"')


def load_turns(path):
    turns = []
    for line in open(path, encoding='utf-8'):
        m = TURN.match(line)
        if m:
            turns.append((secs(*m.group(1).split(':')), m.group(2), m.group(3)))
    return turns


def check_timestamps(md, text, turns, evidence):
    if not turns:
        report('WARN', 'transcript has no **[h:mm:ss] Name:** turns; timestamps not checked')
        return
    end = turns[-1][0] + 300
    for n, line in enumerate(text.splitlines(), 1):
        for m in TS.finditer(line):
            t = secs(*m.groups())
            if t > end:
                report('FAIL', f'{md.name}:{n} timestamp {m.group(0)} is past the end of the transcript')
            elif evidence:   # the covering turn and the next: a cite often lands on a backchannel
                i = max((k for k, x in enumerate(turns) if x[0] <= t), default=0)
                print(f'--- recap:{n} cites {m.group(0)}\n  recap: {line.strip()[:300]}')
                for start, spk, said in turns[i:i + 2]:
                    print(f'  [{start // 3600}:{start // 60 % 60:02d}:{start % 60:02d}] {spk}: {said[:400]}')


def check_html(md, md_text, bans):
    html = md.with_suffix('.html')
    if not html.exists():
        report('WARN', f'no companion {html.name}')
        return
    text = html.read_text(encoding='utf-8')
    if '{{' in text:
        report('FAIL', f'{html.name}: unfilled {{{{slot}}}}')
    for name in re.findall(r'<div class="fig-frame" data-fig="([^"]+)">\s*</div>', text):
        report('FAIL', f'{html.name}: figure frame {name} is empty; run build_html.py')
    check_bans(html.name, re.sub(r'<svg.*?</svg>', '', text, flags=re.S), bans)
    for target in sorted(set(HREF.findall(re.sub(r'<svg.*?</svg>', '', text, flags=re.S)))):
        if not resolves(html.parent, target):   # links that worked in Output/ break after promotion
            report('FAIL', f'{html.name}: broken link {target.split("#")[0]}')
    md_ts = {m.group(0) for m in TS.finditer(md_text)}
    ranges = [(secs(*a.groups()), secs(*b.groups()))   # an html chip may cite a point inside a .md range
              for a, b in re.findall(r'(\d{1,2}:\d{2}:\d{2})\s*[–-]\s*(\d{1,2}:\d{2}:\d{2})', md_text)
              for a, b in [(TS.match(a), TS.match(b))]]
    html_ts = {m for m in TS.finditer(re.sub(r'<svg.*?</svg>', '', text, flags=re.S))}
    extra = sorted({m.group(0) for m in html_ts if m.group(0) not in md_ts
                    and not any(lo <= secs(*m.groups()) <= hi for lo, hi in ranges)})
    if extra:
        report('WARN', f'{html.name} cites timestamps the .md does not: {", ".join(extra[:10])}')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('recap'); ap.add_argument('--transcript')
    ap.add_argument('--ban', action='append', default=[]); ap.add_argument('--evidence', action='store_true')
    a = ap.parse_args()
    md = Path(a.recap)
    text = md.read_text(encoding='utf-8')
    head = '\n'.join(text.splitlines()[:25])
    for row in META:
        if not re.search(rf'^\|\s*{row}\s*\|', head, re.M):
            report('WARN', f'metadata row "{row}" missing')
    check_links(md, text)
    check_figures(md)
    check_bans(md.name, text, a.ban)
    if a.transcript:
        check_timestamps(md, text, load_turns(a.transcript), a.evidence)
    check_html(md, text, a.ban)
    for kind in ('FAIL', 'WARN'):
        for msg in out[kind]:
            print(f'{kind} {msg}')
    print(f"\n{len(out['FAIL'])} FAIL, {len(out['WARN'])} WARN")
    sys.exit(1 if out['FAIL'] else 0)


if __name__ == '__main__':
    main()
