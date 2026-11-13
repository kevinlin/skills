"""Helpers shared by the three script judges.

skill-up copies a script judge into a temp dir before running it, so a judge cannot import
or read anything beside itself. build_manifests.py therefore pastes this file, verbatim,
between the COMMON markers of every judge in scripts/. Edit it here, then re-run
build_manifests.py. Standard library only. The judge runs with the case workspace as cwd.
"""
import hashlib
import html as html_lib
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path.cwd()
RESULTS = []                                   # (label, ok)
BANNED = 'Project Kestrel'
TRANSCRIPT = 'Input/Meetings/20261105_Rollout-planning/Rollout-planning-transcript.md'
RECAP_DIR = 'Output/Meetings/20261105_Rollout-planning'
BANNER = re.compile(r'internal to northwind consulting.*not for harbour freight distribution', re.I)


def check(label, ok, detail=''):
    RESULTS.append((label, bool(ok)))
    line = ('PASS ' if ok else 'FAIL ') + label
    if not ok and detail:
        line += ' -- ' + re.sub(r'\s+', ' ', str(detail))[:400]
    print(line)
    return bool(ok)


def finish():
    bad = [r for r in RESULTS if not r[1]]
    print(f'{len(RESULTS) - len(bad)} passed, {len(bad)} failed')
    sys.exit(1 if bad else 0)


def read(path):
    return Path(path).read_text(encoding='utf-8', errors='replace')


# ---- pristine-state checks (sha256 manifests are embedded in each judge) ----

def tree(rel):
    """{workspace-relative path: sha256} for every file under ROOT/rel."""
    out = {}
    base = ROOT / rel
    if base.is_dir():
        for p in sorted(base.rglob('*')):
            if p.is_file() and p.name != '.DS_Store':
                out[p.relative_to(ROOT).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def same_tree(label, rel, expected, exact=True):
    """The files under rel are the expected ones, byte for byte. exact=False allows extra files."""
    got = tree(rel)
    added = sorted(set(got) - set(expected)) if exact else []
    gone = sorted(set(expected) - set(got))
    changed = sorted(k for k in expected if k in got and got[k] != expected[k])
    parts = [f'{name}: {", ".join(items[:3])}' for name, items in
             (('added', added), ('missing', gone), ('changed', changed)) if items]
    return check(label, not parts, '; '.join(parts))


# ---- text helpers ----

TS = re.compile(r'(?<![\d:])(\d{1,2}):(\d{2}):(\d{2})(?![\d:])')


def hms(s):
    return f'{s // 3600}:{s // 60 % 60:02d}:{s % 60:02d}'


def stamps(text):
    return [int(h) * 3600 + int(m) * 60 + int(s) for h, m, s in TS.findall(text)]


def norm(text):
    text = text.replace('\u2019', "'").replace('\u2018', "'").replace('\u201c', '"').replace('\u201d', '"')
    text = re.sub(r'[\u2010-\u2015\u2212]', '-', text)
    text = re.sub(r'(?<=\d),(?=\d{3}\b)', '', text)          # 1,800 -> 1800
    return re.sub(r'\s+', ' ', text)


def has_all(text, groups):
    """Every group of alternative regexes has at least one hit in text."""
    t = norm(text)
    return all(any(re.search(p, t, re.I) for p in group) for group in groups)


def headings(md):
    return [norm(m.group(2)) for m in re.finditer(r'^(#{1,6})[ \t]+(.*?)[ \t#]*$', md, re.M)]


def has_heading(md, pattern):
    return any(re.search(pattern, h, re.I) for h in headings(md))


def section(md, pattern):
    """Text from the first heading matching pattern to the next heading of the same or a higher level."""
    lines, out, level = md.splitlines(), [], 0
    for line in lines:
        m = re.match(r'^(#{1,6})[ \t]+(.*?)[ \t#]*$', line)
        if m and not out and re.search(pattern, norm(m.group(2)), re.I):
            level, out = len(m.group(1)), [line]
        elif m and out and len(m.group(1)) <= level:
            break
        elif out:
            out.append(line)
    return '\n'.join(out)


def md_blocks(md):
    """Logical blocks: one table row, heading, bullet or paragraph each (a bullet's wrapped lines join it)."""
    blocks, cur = [], []

    def flush():
        if cur:
            blocks.append(' '.join(cur))
            cur.clear()
    for line in md.splitlines():
        s = line.strip()
        if not s:
            flush()
        elif s[0] in '#|':
            flush()
            blocks.append(s)
        elif re.match(r'([-*+]|\d+[.)])\s', s):
            flush()
            cur.append(s)
        else:
            cur.append(s)
    flush()
    return blocks


BLOCK_TAG = re.compile(r'(?i)</?(?:li|p|tr|blockquote|h[1-6]|ul|ol|table|section|figure|figcaption|div|header|'
                       r'footer|nav|main|dl|dt|dd|details|summary|caption|br)\b[^>]*>')


def html_blocks(html):
    html = re.sub(r'(?is)<(script|style|svg)\b.*?</\1>', ' ', html)
    parts = BLOCK_TAG.split(html)
    return [re.sub(r'\s+', ' ', html_lib.unescape(re.sub(r'<[^>]+>', ' ', p))).strip() for p in parts if p.strip()]


# ---- facts a good recap carries; every one needs a timestamp within WINDOW seconds of its turn ----

WINDOW = 90
OPEN_WORDS = [r'\bopen\b', r'unresolved', r'undecided', r'not (yet )?(decided|agreed|settled|resolved)',
              r'no decision', r'disagree', r'\bsplit\b', r'contested', r'unsettled', r'\bpending\b',
              r'\bstuck\b', r'to be (settled|resolved|decided)', r'revisit', r'goes to dalia']
EARLIER_SOURCE = [r'kick-?off', r'scope', r'29 oct', r'oct(ober)? 29', r'(earlier|previous|prior) (recap|plan|meeting|date)',
                  r'(our|the) plan', r'plan sent']
# turns: transcript seconds of the turns the fact comes from. groups: what the block that cites it must
# say. context: what the block or its two neighbours must say (a status word often sits one bullet over).
FACTS = {
    'decision': dict(
        turns=[560, 588, 592],
        groups=[[r'shadow[- ]run', r'parallel[- ]run', r'dual[- ]run', r'shadow period'],
                [r'two[- ]weeks?', r'2[- ]weeks?', r'fortnight', r'14[- ]day', r'fourteen[- ]day'],
                [r'southport']],
        context=[[r'decided', r'agreed', r'decision', r'\bfirm\b', r'settled', r'confirmed', r'approved']]),
    'open disagreement': dict(
        turns=[625, 682, 702, 804, 820, 832],
        groups=[[r'eastgate']],
        context=[OPEN_WORDS, [r'ingrid', r'depot operations', r'\boperations\b'],
                 [r'tomasz', r'infrastructure', r'\bIT (lead|team|side|says|cannot|can.t|support)']]),
    'contradiction': dict(
        turns=[238, 270],
        groups=[[r'30(th)? (of )?nov', r'nov(ember)? 30', r'30/11', r'2026-11-30'], [r'freeze']]),
    'attribution': dict(   # a recap may leave the figure out; if it keeps it, it must be Ingrid's and cited
        turns=[156], if_mentioned=True,
        groups=[[r'ingrid'], [r'\b1800\b', r'eighteen hundred', r'1\.8k', r'1\.8 thousand']]),
}


def fact_found(blocks, fact, window=WINDOW):
    for i, b in enumerate(blocks):
        if not has_all(b, fact['groups']) or not any(abs(t - a) <= window for t in stamps(b) for a in fact['turns']):
            continue
        if has_all(' '.join(blocks[max(0, i - 1):i + 2]), fact.get('context', [])):
            return True
    return False


def check_facts(kind, blocks, facts=None):
    for name, fact in (facts or FACTS).items():
        absent = fact.get('if_mentioned') and not any(has_all(b, fact['groups'][-1:]) for b in blocks)
        check(f'{kind} carries fact: {name}', absent or fact_found(blocks, fact),
              f'no block names it together with a timestamp within {WINDOW}s of the transcript turn')


SPEAKERS = ['Ingrid', 'Tomasz', 'Callum', 'Mei-Ling']


def nearest_speaker(block, anchor):
    """The first-name mention closest to the first hit of the anchor regex."""
    t = norm(block)
    m = re.search(anchor, t, re.I)
    if not m:
        return None
    best = None
    for name in SPEAKERS:
        for n in re.finditer(re.escape(name), t, re.I):
            d = min(abs(n.start() - m.start()), abs(n.end() - m.start()))
            if best is None or d < best[0]:
                best = (d, name)
    return best[1] if best else None


# ---- the FAIL rules of scripts/check_recap.py, inlined, applied to the .md and its .html ----

LINK = re.compile(r'!?\[[^\]]*\]\((<[^>]+>|[^)\s]+)')
HREF = re.compile(r'(?:href|src)="([^"]+)"')


def resolves(base, target):
    target = unquote(html_lib.unescape(target)).split('#')[0]
    return not target or bool(re.match(r'[a-z][a-z0-9+.-]*:', target, re.I)) or (base / target).exists()


def md_link_targets(md):
    return [m.group(1).strip('<>') for line in md.splitlines() for m in LINK.finditer(line)]


def html_link_targets(html):
    return HREF.findall(re.sub(r'(?is)<svg.*?</svg>', '', html))


def mechanical(md_path, end):
    """Broken links, the banned name, timestamps past the transcript end, unfilled html slots."""
    problems = []
    docs = [(md_path, read(md_path))]
    html_path = md_path.with_suffix('.html')
    if html_path.is_file():
        docs.append((html_path, read(html_path)))
    for path, text in docs:
        is_html = path.suffix == '.html'
        body = re.sub(r'(?is)<svg.*?</svg>', '', text) if is_html else text
        for target in (html_link_targets(text) if is_html else md_link_targets(text)):
            if not resolves(path.parent, target):
                problems.append(f'{path.name}: broken link {target.split("#")[0]}')
        if BANNED.lower() in body.lower():
            problems.append(f'{path.name}: banned name')
        late = sorted({s for s in stamps(body) if s > end + 300})
        if late:
            problems.append(f'{path.name}: timestamp past the end of the transcript ({hms(late[0])})')
        if is_html and '{{' in text:
            problems.append(f'{path.name}: unfilled {{{{slot}}}}')
        if is_html and re.search(r'<div class="fig-frame" data-fig="[^"]+">\s*</div>', text):
            problems.append(f'{path.name}: empty figure frame')
    return problems


def installed_checker(md_path):
    """Run the skill's own check_recap.py if the engine installed it in this workspace. None if absent."""
    found = sorted((ROOT / '.claude' / 'skills').glob('*/scripts/check_recap.py'))
    if not found:
        return None
    p = subprocess.run([sys.executable, str(found[0]), str(md_path), '--transcript', str(ROOT / TRANSCRIPT),
                        '--ban', BANNED], capture_output=True, text=True, timeout=60, cwd=str(ROOT))
    return p.returncode, [l for l in p.stdout.splitlines() if l.startswith('FAIL')]


def check_mechanical(md_path, end):
    problems = mechanical(md_path, end)
    check('mechanical checks pass (links, banned name, timestamps, html slots)', not problems,
          '; '.join(problems[:4]))
    res = installed_checker(md_path)
    if res is not None:
        check("the installed skill's check_recap.py exits 0", res[0] == 0, '; '.join(res[1][:4]))


def html_is_standalone(html_path):
    text = read(html_path)
    bad = []
    if re.search(r'<script\b[^>]*\bsrc\s*=', text, re.I):
        bad.append('external <script src=>')
    if '{{' in text:
        bad.append('unfilled {{slot}}')
    return not bad, ', '.join(bad)
