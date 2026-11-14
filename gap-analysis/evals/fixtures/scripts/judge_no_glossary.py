#!/usr/bin/env python3
"""Script judge for the flow-a-no-glossary case. Exit 0 = pass.

Runs with the case workspace as cwd. The user says there is no glossary. The skill then proceeds, defaults every
terminology mismatch to AMB-, preserves both variants verbatim, and notes the missing glossary up front in the
report intro. The fixture plants two mismatches ("RMA number" vs "return authorisation code", "restocking fee"
vs "re-stock charge") that a glossary would normally have to settle.
"""
# >>> COMMON (pasted from fixtures/judge_common.py by build_fixtures.py; edit it there)
import hashlib
import os
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path.cwd()
RESULTS = []                                   # (label, ok)
ID_RE = re.compile(r'\b(?:AMB|BPM|COM|CTR|GAP|INT|MFR|REG|SAP|G|W|A|B|D|R)-\d{1,3}\b')
SEV_RANK = {'critical': 0, 'high': 1, 'medium': 2, 'open': 2.5, 'low': 3, 'resolved': 4}
WS_VALUES = {'ws1', 'ws2', 'ws3', 'ws4', 'ws5', 'ws6', 'ws7', 'arch', 'cross', 'reg', 'comm'}


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


def norm(text):
    """Collapse whitespace and straighten typographic quotes and dashes."""
    text = text.replace('\u2019', "'").replace('\u2018', "'").replace('\u201c', '"').replace('\u201d', '"')
    text = re.sub(r'[\u2010-\u2015\u2212]', '-', text)
    return re.sub(r'\s+', ' ', text).strip()


def squash(raw):
    """Whitespace-insensitive form of raw markup, for byte-for-byte style comparisons."""
    return re.sub(r'>\s+<', '><', re.sub(r'\s+', ' ', raw)).strip()


def sha(text):
    return hashlib.sha1(text.encode('utf-8')).hexdigest()


def final_message():
    """skill-up exports the final reply as EVAL_FINAL_MESSAGE; None when it did not."""
    return os.environ.get('EVAL_FINAL_MESSAGE')


def check_message(label, patterns, required=False):
    """Every regex in patterns matches the final reply. A missing reply skips unless required."""
    msg = final_message()
    if msg is None:
        if required:
            check(label, False, 'EVAL_FINAL_MESSAGE was not exported to the judge')
        else:
            print('SKIP ' + label + ' -- EVAL_FINAL_MESSAGE not exported')
        return
    check(label, all(re.search(p, msg, re.I | re.S) for p in patterns), 'final reply ends: ' + msg[-240:])


# ---- a small DOM: just enough structure for class, attribute and text checks ----

VOID = {'meta', 'link', 'br', 'hr', 'img', 'input', 'col', 'source', 'wbr', 'area', 'base', 'embed', 'param', 'track'}


class Node:
    def __init__(self, tag, attrs, parent):
        self.tag, self.attrs, self.parent, self.kids = tag, dict(attrs), parent, []

    @property
    def classes(self):
        return (self.attrs.get('class') or '').split()

    def walk(self):
        yield self
        for k in self.kids:
            if isinstance(k, Node):
                yield from k.walk()

    def find(self, tag=None, cls=None):
        return [n for n in self.walk()
                if n is not self and (tag is None or n.tag == tag) and (cls is None or cls in n.classes)]

    def first(self, tag=None, cls=None):
        found = self.find(tag, cls)
        return found[0] if found else None

    def children(self, tag):
        return [k for k in self.kids if isinstance(k, Node) and k.tag == tag]

    def text(self):
        parts = []

        def go(n):
            if n.tag in ('script', 'style'):
                return
            for k in n.kids:
                go(k) if isinstance(k, Node) else parts.append(k)
        go(self)
        return norm(' '.join(parts))


class _Builder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node('#root', [], None)
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs, self.cur)
        self.cur.kids.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.cur.kids.append(Node(tag, attrs, self.cur))

    def handle_endtag(self, tag):
        n = self.cur
        while n is not None and n.tag != tag:
            n = n.parent
        if n is not None and n.parent is not None:
            self.cur = n.parent

    def handle_data(self, data):
        self.cur.kids.append(data)


def parse(raw):
    b = _Builder()
    b.feed(raw)
    b.close()
    return b.root


def text_before(root, tag):
    """Visible text that precedes the first <tag> in document order."""
    parts = []

    def go(n):
        for k in n.kids:
            if isinstance(k, Node):
                if k.tag == tag:
                    return True
                if k.tag not in ('script', 'style') and go(k):
                    return True
            else:
                parts.append(k)
        return False
    go(root)
    return norm(' '.join(parts))


# ---- house-style structure shared by the report judges ----

def cells(tr):
    return tr.children('td')


def gap_table(root):
    """(lower-cased headers, rows) of the first table that has a Severity column."""
    for t in root.find('table'):
        heads = [th.text().lower() for th in t.find('th')]
        if any('severity' in h for h in heads):
            body = t.first('tbody')
            rows = []
            for tr in (body.find('tr') if body else []):
                tds = cells(tr)
                rows.append(dict(tr=tr, tds=tds, id=tds[0].text() if tds else ''))
            return heads, rows
    return [], []


def col(heads, word, default):
    for i, h in enumerate(heads):
        if word in h:
            return i
    return default


def cell_text(row, idx):
    return row['tds'][idx].text() if idx < len(row['tds']) else ''


def row_text(row):
    return norm(' '.join(td.text() for td in row['tds']))


def sev_class(td):
    """The bare severity class on a td (the individual-report form), or None."""
    hit = [c for c in td.classes if c.startswith('sev-')]
    return hit[0][4:] if hit else None


def pill_classes(td):
    return [c for sp in td.find('span') for c in sp.classes if c.startswith('pill-')]


def box_bullets(root):
    out = {}
    for name in ('confirmed', 'implied', 'gap'):
        box = root.first(cls='box-' + name)
        out[name] = [li.text() for li in box.find('li')] if box else None
    return out


def register_rows(root):
    """Every tbody row in document order, tagged with the category title it sits under."""
    rows, cat = [], None
    for n in root.walk():
        if 'category-title' in n.classes:
            cat = n.text()
        elif n.tag == 'tr' and n.parent is not None and n.parent.tag == 'tbody':
            tds = cells(n)
            rows.append(dict(tr=n, tds=tds, id=tds[0].text() if tds else '', cat=cat,
                             sev=n.attrs.get('data-sev'), ws=n.attrs.get('data-ws')))
    return rows


# ---- surgical-update helpers: what an update may touch, and what it must leave alone ----

def remainder(raw):
    """The file with the three regions an update may touch emptied: subtitle, table bodies, arch-box lists."""
    raw = re.sub(r'(<p class="subtitle">).*?(</p>)', r'\1\2', raw, flags=re.S)
    raw = re.sub(r'(<tbody>).*?(</tbody>)', r'\1\2', raw, flags=re.S)
    raw = re.sub(r'(<div class="arch-box[^"]*">\s*<h3>.*?</h3>\s*<ul>).*?(</ul>)', r'\1\2', raw, flags=re.S)
    return sha(squash(raw))


def row_hashes(raw):
    """{gap id: hash of the row markup} for every row of the first tbody."""
    m = re.search(r'<tbody>(.*?)</tbody>', re.sub(r'<!--.*?-->', '', raw, flags=re.S), re.S)
    out = {}
    for tr in re.findall(r'<tr\b.*?</tr>', m.group(1) if m else '', re.S):
        td = parse(tr).first('td')
        out.setdefault(td.text() if td else '?', sha(squash(tr)))
    return out


def subtitle_masked(raw, *dates):
    m = re.search(r'<p class="subtitle">(.*?)</p>', raw, re.S)
    text = squash(m.group(1)) if m else ''
    for d in dates:
        text = text.replace(d, 'DATE')
    return text
# <<< COMMON

GAPDIR = 'docs/gap-analysis'
KEBAB = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*-gap-analysis\.html')
ID_FORM = re.compile(r'(?:AMB|BPM|COM|CTR|GAP|INT|MFR|REG|SAP|[GWABD])-\d{2,}')
PILL_FORM = re.compile(r'pill-(?:ws[1-7]|arch|cross|reg|comm)')


def variants(s):
    """Lower-case, hyphens as spaces, -ise/-ize folded: 'Re-stock charge' == 're stock charge'."""
    return re.sub(r'authori[sz]ation', 'authorisation', norm(s).lower().replace('-', ' '))


def main():
    folder = ROOT / GAPDIR
    files = sorted(p for p in folder.glob('*.html') if p.name != 'gap-register.html') if folder.is_dir() else []
    named = [p for p in files if 'return' in p.name.lower()]
    report = (named or files or [None])[0]
    if not check(f'a *-gap-analysis.html report was saved in {GAPDIR}/', report, 'no html file there'):
        finish()
    check('filename is <topic>-gap-analysis.html in kebab-case', KEBAB.fullmatch(report.name), report.name)
    raw = read(report)
    root = parse(raw)
    check('self-contained HTML document with the theme JS kept',
          re.match(r'\s*<!DOCTYPE html>', raw, re.I) and not re.search(r'<script[^>]+\bsrc\s*=', raw, re.I)
          and all(s in raw for s in ('function setTheme', 'function applyTheme', 'gap-analysis-theme')))

    intro = variants(text_before(root, 'table'))
    check('the intro, before the gap table, says no glossary was supplied and terms were flagged conservatively',
          re.search(r'no glossary', intro) and re.search(r'conservativ|reconcile|amb', intro), intro[-240:])

    heads, rows = gap_table(root)
    if not check('a gap table with at least three rows', len(rows) >= 3, f'{len(rows)} rows'):
        finish()
    i_gap, i_sev, i_ws = col(heads, 'gap', 1), col(heads, 'severity', 3), col(heads, 'workstream', 4)
    if not check('every row has all its cells', all(len(r['tds']) > max(i_gap, i_sev, i_ws) for r in rows)):
        finish()
    gids = [r['id'] for r in rows]
    check('every gap ID has a valid prefix and number, and none repeats',
          all(ID_FORM.fullmatch(i) for i in gids) and len(set(gids)) == len(gids), gids)
    check('severity is a bare class on the td, workstream cells use pill pills',
          all(sev_class(r['tds'][i_sev]) in ('critical', 'high', 'medium', 'low') and not r['tds'][i_sev].find(cls='sev')
              and pill_classes(r['tds'][i_ws]) and all(PILL_FORM.fullmatch(c) for c in pill_classes(r['tds'][i_ws]))
              for r in rows))
    check('every row cites its source in <code> in the Gap column',
          all(any(c.text() for c in r['tds'][i_gap].find('code')) for r in rows),
          [r['id'] for r in rows if not r['tds'][i_gap].find('code')])

    amb = [variants(row_text(r)) for r in rows if r['id'].startswith('AMB-')]
    check('"RMA number" vs "return authorisation code" is an AMB- row quoting both forms',
          any('rma number' in t and 'return authorisation code' in t for t in amb), amb)
    check('"restocking fee" vs "re-stock charge" is an AMB- row quoting both forms',
          any('restocking fee' in t and 're stock charge' in t for t in amb), amb)

    boxes = box_bullets(root)
    check('three architecture boxes, each with bullets', all(boxes[k] for k in boxes), boxes)
    flagged = set()
    for k in ('implied', 'gap'):
        for b in boxes[k] or []:
            flagged |= set(ID_RE.findall(b))
    check('every gap row is mirrored by a bullet in box-gap or box-implied',
          all(i in flagged for i in gids), [i for i in gids if i not in flagged])
    check_message('final reply names the saved report', [re.escape(report.name)])


main()
finish()
