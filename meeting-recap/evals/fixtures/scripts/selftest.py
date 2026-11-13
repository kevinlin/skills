#!/usr/bin/env python3
"""Grader self-test, driven by selftest.sh. Not run by skill-up.

For each script judge it builds workspaces in a temp dir: a good one, a good one with other valid
formatting, and one bad one per assertion (a single isolated mutation each). It runs the judge
copy that selftest.sh placed in a fresh temp dir, exactly as skill-up does (uploaded as a file
named "script", run with the workspace as cwd), and asserts the exit code and the set of FAIL
labels: a bad workspace must fail exactly the assertion its mutation targets, nothing else.

  selftest.py <judges-dir> <work-dir>
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
FIX = HERE.parent
SKILL = FIX.parent.parent
sys.path.insert(0, str(FIX))
import build_manifests as B  # noqa: E402

CLEAN = FIX / 'src' / 'clean-output'
RD = B.RECAP_DIR
MD, HTML = RD + '/Rollout-planning-recap.md', RD + '/Rollout-planning-recap.html'
CHECKER_SRC = SKILL / 'scripts' / 'check_recap.py'
INSTALLED = '.claude/skills/meeting-recap/scripts/check_recap.py'
LATE = '0:24:59'   # inside the transcript, but far from every turn a fact is anchored to


class WS:
    def __init__(self, case, dest):
        self.root = Path(dest)
        shutil.copytree(FIX / 'workspaces' / case, self.root)

    def path(self, rel):
        return self.root / rel

    def read(self, rel):
        return self.path(rel).read_text(encoding='utf-8')

    def write(self, rel, text):
        self.path(rel).parent.mkdir(parents=True, exist_ok=True)
        self.path(rel).write_text(text, encoding='utf-8')

    def edit(self, rel, old, new, count=1):
        text = self.read(rel)
        n = text.count(old)
        assert n == count or (count == -1 and n), f'{rel}: expected {count} of {old!r}, found {n}'
        self.write(rel, text.replace(old, new))

    def delete(self, rel):
        self.path(rel).unlink()

    def append(self, rel, text):
        self.write(rel, self.read(rel) + text)

    def install_checker(self, stub=False):
        self.write(INSTALLED, 'import sys\nprint("FAIL stub")\nsys.exit(1)\n' if stub else CHECKER_SRC.read_text())

    def run_checker(self, md_rel, out_dir):
        """Produce check.txt and evidence.txt the way step 6 of the skill does."""
        md, transcript = self.path(md_rel), self.path(B.TRANSCRIPT)
        base = [sys.executable, str(CHECKER_SRC), str(md), '--transcript', str(transcript)]
        chk = subprocess.run(base + ['--ban', 'Project Kestrel'], capture_output=True, text=True)
        ev = subprocess.run(base + ['--evidence'], capture_output=True, text=True)
        assert chk.returncode == 0, f'the real check_recap.py rejects the good sample:\n{chk.stdout}'
        self.write(out_dir + '/check.txt', chk.stdout)
        self.write(out_dir + '/evidence.txt', ev.stdout)


def shift(ws, rel, stamps):
    for s in stamps:
        text = ws.read(rel)
        if s in text:
            ws.write(rel, text.replace(s, LATE))


# ---------------------------------------------------------------- recap-from-transcript

def recap_good(ws, alt=False):
    md, html, glossary = (CLEAN / MD).read_text(), (CLEAN / HTML).read_text(), (CLEAN / 'Glossary.md').read_text()
    stem = 'Rollout-planning-recap'
    if alt:   # other file name, heading case and level, plain banner, hyphenated ranges, synonyms, minified html
        stem = '20261105-rollout-recap'
        md = md.replace('**Internal to Northwind Consulting. Not for Harbour Freight distribution.**',
                        'Internal to Northwind Consulting. Not for Harbour Freight distribution.')
        for a, b in (('## 1. The short version', '## 1. The Short Version'),
                     ('## 7. Where sources disagree', '## 7. Where Sources Disagree'),
                     ('## 9. Open questions', '## 9. Open Questions'),
                     ('## 10. Next steps', '### 10. Next Steps')):
            md = md.replace(a, b)
        md = md.replace('\u2013', '-').replace('two-week shadow run', '2-week parallel run')
        md = md.replace('[Rollout-planning-recap.html](<Rollout-planning-recap.html>)', f'[{stem}.html](<{stem}.html>)')
        html = html.replace('two-week shadow run', '2-week parallel run')
        # a recap may leave out Ingrid's 1,800-parcel figure; the attribution check only binds when it is kept
        md = re.sub(r'- \*\*Southport handles about 1,800 parcels.*\n', '', md)
        html = re.sub(r'<li><strong>Southport handles about 1,800 parcels.*?</li>\s*', '', html, flags=re.S)
        html = html.replace('\u2013', '&ndash;').replace('\u2019', '&rsquo;')
        html = re.sub(r'\s*\n\s*', ' ', html)
        glossary = glossary.replace('Dock-door profile', 'Dock door profile').replace('Shadow run', 'Shadow-run')
    for ext in ('.md', '.html'):
        ws.write(f'{RD}/{stem}{ext}', md if ext == '.md' else html)
    ws.write('Glossary.md', glossary)
    ws.run_checker(f'{RD}/{stem}.md', RD)
    return f'{RD}/{stem}'


L = dict(
    found='recap .md exists under Output/Meetings/20261105_*/',
    banner='internal banner is line 1',
    heads='has the short-version, where-sources-disagree, open-questions and next-steps headings',
    wsd='where-sources-disagree section names the 30 Nov contradiction',
    html='html companion exists next to the recap',
    standalone='html companion is standalone (no <script src>, no {{slot}})',
    mech='mechanical checks pass (links, banned name, timestamps, html slots)',
    inst="the installed skill's check_recap.py exits 0",
    saved='check.txt and evidence.txt saved in the meeting folder',
    gloss='Glossary.md updated with at least 2 of the 3 new terms',
    keep='Glossary.md keeps every original term as a table row',
    ban='banned name absent from the glossary and every other deliverable',
    stray='no UBIQUITOUS_LANGUAGE.md and no second glossary anywhere',
    inp='Input/ is byte-identical to the fixture',
    art='Artefacts/ is byte-identical to the fixture',
)
FACT = {'decision': ['0:09:20', '0:09:48', '0:09:52'],
        'open disagreement': ['0:10:25', '0:11:22', '0:11:42', '0:13:24', '0:13:40', '0:13:52'],
        'contradiction': ['0:04:30', '0:03:41', '0:05:24'], 'attribution': ['0:02:36']}


def recap_cases():
    cases = []

    def add(name, fn, expect):
        cases.append((name, fn, set(expect)))
    add('no recap file', lambda w: (w.delete(MD), w.delete(HTML), w.delete(RD + '/check.txt'), w.delete(RD + '/evidence.txt')), [L['found']])
    add('banner missing on line 1', lambda w: w.edit(MD, '**Internal to Northwind Consulting. Not for Harbour Freight distribution.**\n\n', ''), [L['banner']])
    add('a required heading renamed', lambda w: w.edit(MD, '## 10. Next steps', '## 10. Actions'), [L['heads']])
    add('contradiction missing from the where-sources-disagree section',
        lambda w: w.edit(MD, 'wave-one cutover on Monday 30 November | Ingrid', 'wave-one cutover on the planned date | Ingrid'), [L['wsd']])
    for fact, stamps in FACT.items():
        add(f'md has no timestamp near the {fact} turn', lambda w, s=stamps: shift(w, MD, s), [f'md carries fact: {fact}'])
        add(f'html has no timestamp near the {fact} turn', lambda w, s=stamps: shift(w, HTML, s), [f'html carries fact: {fact}'])
    add('figure credited to Tomasz', lambda w: w.edit(MD, 'Ingrid used it to show', 'Tomasz used it to show'), ['md carries fact: attribution'])
    add('open disagreement written up as settled', lambda w: [w.edit(MD, a, b) for a, b in (
        ('**Eastgate in wave one is open.**', '**Eastgate goes in wave one.**'),
        ('If they are still split after 20 November it goes to Dalia.', 'Dalia is informed.'),
        ('Eastgate was argued and left open', 'Eastgate was argued and agreed'),
        ('Status: Open.', 'Status: Agreed.'), ('**Neither moved.**', '**Both agreed.**'),
        ('If Ingrid and Tomasz are still split, it goes to Dalia', 'Dalia is informed'),
        ('| Open. Settled after the survey on 20 November, or by Dalia', '| Agreed.'))],
        ['md carries fact: open disagreement'])
    add('html companion missing', lambda w: w.delete(HTML), [L['html'], L['mech'], L['inst']])   # the md's Companion link breaks too
    add('html loads an external script', lambda w: w.edit(HTML, '</head>', '<script src="https://cdn.example/x.js"></script></head>'), [L['standalone']])
    add('html has an unfilled slot', lambda w: w.edit(HTML, '</main>', '<p>{{body}}</p></main>'), [L['standalone'], L['mech'], L['inst']])
    add('banned name in the recap .md', lambda w: w.append(MD, '\nTomasz mentioned Project Kestrel.\n'), [L['mech'], L['inst']])
    add('broken link in the recap .md', lambda w: w.edit(MD, '<../../../Glossary.md>', '<../../Glossary.md>', -1), [L['mech'], L['inst']])
    add('broken link in the recap .html', lambda w: w.edit(HTML, 'href="../../../Glossary.md"', 'href="../../Glossary.md"', -1), [L['mech'], L['inst']])
    add('timestamp past the transcript end', lambda w: w.edit(MD, '0:14:40\u20130:25:12', '0:14:40\u20130:48:12'), [L['mech'], L['inst']])
    add("installed check_recap.py reports a FAIL", lambda w: w.install_checker(stub=True), [L['inst']])
    add('check.txt missing', lambda w: w.delete(RD + '/check.txt'), [L['saved']])
    add('evidence.txt missing', lambda w: w.delete(RD + '/evidence.txt'), [L['saved']])
    add('evidence.txt is not --evidence output', lambda w: w.write(RD + '/evidence.txt', 'done\n'), [L['saved']])
    add('glossary unchanged', lambda w: w.write('Glossary.md', (FIX / 'src/base/Glossary.md').read_text()), [L['gloss']])
    add('glossary gains only one new term', lambda w: w.write('Glossary.md', (FIX / 'src/base/Glossary.md').read_text().replace(
        '| **Wave** |', '| **Peak freeze** | Window in which depots change nothing. | change freeze |\n| **Wave** |')), [L['gloss']])
    add('glossary loses an original term', lambda w: w.edit('Glossary.md', '| **Site survey** | An IT walk-through of a depot\'s network coverage and dock layout. | walkthrough |\n', ''), [L['keep']])
    add('banned name in the glossary', lambda w: w.append('Glossary.md', '\nFormerly Project Kestrel.\n'), [L['ban']])
    add('banned name in another deliverable', lambda w: w.write('Output/Meetings/20261105_Rollout-planning/notes.md', 'Project Kestrel notes\n'), [L['ban']])
    add('UBIQUITOUS_LANGUAGE.md written', lambda w: w.write('Output/UBIQUITOUS_LANGUAGE.md', '# Terms\n'), [L['stray']])
    add('second Glossary.md written', lambda w: w.write('Output/Glossary.md', '# Glossary\n'), [L['stray']])
    add('Input/ file edited', lambda w: w.append(B.TRANSCRIPT, '\nextra line\n'), [L['inp']])
    add('Input/ file added', lambda w: w.write('Input/Meetings/20261105_Rollout-planning/notes.txt', 'x\n'), [L['inp']])
    add('recap promoted into Artefacts/', lambda w: w.write('Artefacts/Meetings/20261105_Rollout-planning/r.md', w.read(MD)), [L['art']])
    add('stakeholder list edited', lambda w: w.append('Artefacts/Stakeholders/stakeholders.md', '\n| Extra | X | Y | Z |\n'), [L['art']])
    return cases


def recap_setup(ws, alt=False, installed=True):
    recap_good(ws, alt)
    if installed:
        ws.install_checker()


# ---------------------------------------------------------------- verify-planted-defects

V = dict(
    place='recap .md and .html are still in place',
    sections_md='md keeps all of its sections', sections_html='html keeps all of its sections',
    banner='internal banner is still line 1',
    mech=L['mech'], inst=L['inst'],
    art='Artefacts/ is byte-identical (nothing promoted)', inp=L['inp'],
)


def verify_setup(ws, alt=False, installed=True):
    if alt:
        verify_alt_fix(ws)   # the shipped workspace still carries the planted defects
    else:
        for ext in ('.md', '.html'):
            ws.write(RD + '/Rollout-planning-recap' + ext, (CLEAN / (MD if ext == '.md' else HTML)).read_text())
    if installed:
        ws.install_checker()


def verify_alt_fix(ws):
    """The four planted defects fixed other ways: a renamed term, a timestamp range, a paraphrase, a link with a fragment."""
    for rel in (MD, HTML):
        ws.edit(rel, 'still carries Project Kestrel in half its headers', 'still carries the old name in half its headers')
    ws.edit(MD, 'Mei-Ling (0:48:12).', 'Mei-Ling (0:07:55\u20130:08:05).')
    ws.edit(HTML, 'Mei-Ling <span class="ts">0:48:12</span>.', 'Mei-Ling <span class="ts">0:07:55\u20130:08:05</span>.')
    ws.edit(MD, 'Ingrid: "Manifest sync has never once finished before the Monday morning shift."',
            'Tomasz said manifest sync has never once finished before the Monday morning shift')
    ws.edit(HTML, 'Ingrid: \u201cManifest sync has never once finished before the Monday morning shift.\u201d',
            'Tomasz said manifest sync has never once finished before the Monday morning shift')
    ws.edit(MD, 'Rollout-plan-transcript.md>)', 'Rollout-planning-transcript.md>)')
    ws.edit(HTML, 'Rollout-plan-transcript.md"', 'Rollout-planning-transcript.md#t=0"')


def verify_cases():
    cases = []

    def add(name, fn, expect):
        cases.append((name, fn, set(expect)))

    def plant(defect, ext):
        rel = RD + '/Rollout-planning-recap' + ext
        return lambda w: w.write(rel, B.apply_defect(defect, ext, w.read(rel)))
    k = {'banned name in a body line': 'banned', 'timestamp past the transcript end': 'ts',
         'quote attributed to the wrong person': 'quote', 'broken relative link': 'link'}
    for ext, kind in (('.md', 'md'), ('.html', 'html')):
        add(f'banned name planted in the {kind}', plant('banned name in a body line', ext),
            [f'{kind}: banned name is gone', V['mech'], V['inst']])
        add(f'bad timestamp planted in the {kind}', plant('timestamp past the transcript end', ext),
            [f'{kind}: no timestamp past the transcript end', f'{kind} carries fact: bad-timestamp line (automated comparison)',
             V['mech']] + ([V['inst']] if kind == 'md' else []))   # check_recap.py reads timestamps from the .md only
        add(f'wrong speaker planted in the {kind}', plant('quote attributed to the wrong person', ext),
            [f'{kind}: the manifest-sync quote is attributed to Tomasz'])
        add(f'broken link planted in the {kind}', plant('broken relative link', ext),
            [f'{kind}: every relative link resolves', f'{kind}: the transcript link is kept and resolves', V['mech'], V['inst']])
    add('a link unrelated to the transcript broken', lambda w: w.edit(MD, '<../../../Glossary.md>', '<../../Glossary.md>', -1),
        ['md: every relative link resolves', V['mech'], V['inst']])
    add('transcript link dropped from the html', lambda w: w.edit(HTML, '<a href="../../../Input/Meetings/20261105_Rollout-planning/Rollout-planning-transcript.md">Transcript</a>', 'Transcript'),
        ['html: the transcript link is kept and resolves'])
    add('fixed by deleting the interface-spec line',
        lambda w: w.edit(MD, '- **Interface spec.** The interface spec still carries the old programme name in half its headers (0:03:18). Rohan knows.\n', ''),
        ['md carries fact: banned-name line (interface spec)'])
    add('fixed by deleting the quote',
        lambda w: w.edit(HTML, 'Tomasz: \u201cManifest sync has never once finished before the Monday morning shift.\u201d <span class="ts">0:16:48</span>. ', ''),
        ['html: the manifest-sync quote is attributed to Tomasz', 'html carries fact: misattributed quote (manifest sync)'])
    add('fixed by dropping the timestamp instead of correcting it',
        lambda w: w.edit(MD, 'Mei-Ling (0:08:00).', 'Mei-Ling.'), ['md carries fact: bad-timestamp line (automated comparison)'])
    add('fixed by deleting the staffing line', lambda w: w.edit(HTML, '<li><strong>No extra floor staff.</strong> The comparison is automated, so nobody extra is needed at Southport. Mei-Ling <span class="ts">0:08:00</span>.</li>\n', ''),
        ['html carries fact: bad-timestamp line (automated comparison)'])
    for fact, stamps in FACT.items():
        add(f'md has no timestamp near the {fact} turn', lambda w, s=stamps: shift(w, MD, s), [f'md carries fact: {fact}'])
        add(f'html has no timestamp near the {fact} turn', lambda w, s=stamps: shift(w, HTML, s), [f'html carries fact: {fact}'])
    add('a section demoted in the md', lambda w: w.edit(MD, '## 8. Changes to our own records', '### 8. Changes to our own records'), [V['sections_md']])
    add('a section dropped from the html', lambda w: w.edit(HTML, '<section id="sec8" aria-labelledby="h-sec8">', '<div id="sec8" aria-labelledby="h-sec8">'), [V['sections_html']])
    add('banner removed', lambda w: w.edit(MD, '**Internal to Northwind Consulting. Not for Harbour Freight distribution.**\n\n', ''), [V['banner']])
    add('md deleted', lambda w: w.delete(MD), [V['place']])
    add('html deleted', lambda w: w.delete(HTML), [V['place']])
    add('unfilled slot left in the html', lambda w: w.edit(HTML, '</main>', '<p>{{body}}</p></main>'), [V['mech'], V['inst']])
    add("installed check_recap.py reports a FAIL", lambda w: w.install_checker(stub=True), [V['inst']])
    add('recap promoted into Artefacts/', lambda w: w.write('Artefacts/Meetings/20261105_Rollout-planning/r.md', w.read(MD)), [V['art']])
    add('Input/ file edited', lambda w: w.append(B.TRANSCRIPT, '\nextra line\n'), [V['inp']])
    return cases


# ---------------------------------------------------------------- client-safe-copy

SANITISED = '''# Tidewater: rollout planning, 5 November 2026

| Who | Side | Role in this session |
|---|---|---|
| Ingrid Solheim | Harbour Freight | Head of Depot Operations |
| Tomasz Wieczorek | Harbour Freight | IT Infrastructure Lead |
| Callum Reeve | Northwind Consulting | Engagement Lead |
| Mei-Ling Tan | Northwind Consulting | Delivery Manager |

Dalia Nasser and Rohan Mistry were not able to join this session.

---

## 1. Summary

- **The 30 November cutover moves.** Harbour Freight's peak freeze runs from 23 November to 8 January, and no depot changes are made during it. Wave-one cutover is now planned for after the freeze.
- **Agreed: Southport runs a two-week shadow run from 11 January 2027.** During it the old tracker stays the system of record while Tidewater receives a copy of every live scan. Cutover is planned for no earlier than 25 January, and only if the daily parcel counts match.
- **Whether Eastgate joins wave one is still to be agreed.** Depot Operations would like it in wave one. IT would first like to complete the site survey of the dock-area network coverage, which is due by 20 November.

## 2. How the session ran

The session opened on the wave plan agreed at the kickoff and on what a cutover night involves for the floor teams. The peak freeze came up when the 30 November date was checked against the depot calendar. The group then agreed an approach for Southport and discussed Eastgate.

## 3. The freeze moves the cutover

The peak freeze runs from 23 November to 8 January. Nothing changes in a depot in that window: no new systems, no new scanners and no process changes. The 30 November cutover falls inside it, so the earliest wave-one cutover is after 8 January.

## 4. The shadow run at Southport

Southport will run Tidewater alongside the old tracker for two weeks from Monday 11 January. The old tracker stays the system of record. Each morning the daily parcel counts from both systems are compared, and the test is that they match. Floor teams do not change how they work, and no extra staff are needed.

## 5. Eastgate: wave one or wave two

Depot Operations would like Eastgate in wave one because it is the largest depot. IT can support it only once the site survey has confirmed that dock-area coverage can be fixed in time. The survey is due by Friday 20 November and the question returns to the programme sponsor if the two views still differ.

## 6. Points to confirm

| # | Topic | Position from the session | Proposed action |
|---|---|---|---|
| 1 | Revised cutover date | The 30 November date falls inside the peak freeze | Update the plan and send it to the programme sponsor by Tuesday 10 November |
| 2 | Eastgate in wave one | Views differ until the site survey is complete | Revisit on 20 November with the survey result |
| 3 | Name for the per-door setup record | Teams use different names for it | Agree one name with Harbour Freight |

## 7. Open questions

| # | Question | Why it matters |
|---|---|---|
| 1 | Will the programme sponsor approve the revised dates? | Everything else depends on them |
| 2 | Which weekday suits the cutover? | The nightly sync has to finish before the first shift |
'''

C = dict(
    found='a new .md exists under Output/Meetings/Sanitised/',
    ts='no h:mm:ss timestamps', banner='no internal banner or "internal only" wording', img='no image embeds',
    ban='banned name absent', summary='has a "Summary" heading with content',
    points='has a "Points to confirm" heading with content', titles='internal section titles renamed',
    meta='metadata table removed', trans='transcript, model and re-check notes removed',
    reading='"Our reading" strategy lines removed', third='sensitive third-party name removed',
    unconf='(unconfirmed) markers gone', quote='colloquial quote paraphrased',
    numbered='keeps at least 3 numbered sections with real content', who='keeps the Who table with the attendees',
    decision='still states the decision', internal='internal recap is unchanged', inp=L['inp'], art=L['art'],
)
SAN = 'Output/Meetings/Sanitised/20261105_Rollout-planning.md'


def hollow(text, numbers):
    for n in numbers:
        text, hit = re.subn(rf'(^## {n}\. [^\n]*\n\n).*?(?=^## |\Z)', r'\1TBD.\n\n', text, flags=re.M | re.S)
        assert hit == 1, f'section {n}'
    return text


def client_setup(ws, alt=False):
    text = SANITISED
    path = SAN
    if alt:   # other file name, heading level, bullets instead of tables, other title case
        path = 'Output/Meetings/Sanitised/Tidewater-rollout-planning-client.md'
        text = text.replace('## ', '### ').replace('Points to confirm', 'Points To Confirm').replace('## 1. Summary', '## 1. SUMMARY')
        text = text.replace('| Who | Side | Role in this session |', '| Name | Organisation | Role |')
    ws.write(path, text)


def client_cases():
    cases = []

    def add(name, fn, expect):
        cases.append((name, fn, set(expect)))

    def put(old, new, count=1):
        return lambda w: w.edit(SAN, old, new, count)

    add('no sanitised copy', lambda w: w.delete(SAN), [C['found']])
    add('timestamp left in', put('two-week shadow run', 'two-week shadow run (0:09:20)'), [C['ts']])
    add('internal banner left in', lambda w: w.write(SAN, '**Internal to Northwind Consulting.**\n\n' + SANITISED), [C['banner']])
    add('figure embedded', put('## 3. The freeze', '![Figure 1](diagram/F1_x.svg)\n\n## 3. The freeze'), [C['img']])
    add('banned name written', put('Southport will run', 'Under the old name, Project Kestrel, Southport will run'), [C['ban']])
    add('Summary renamed', put('## 1. Summary', '## 1. Overview'), [C['summary']])
    add('Points to confirm renamed', put('## 6. Points to confirm', '## 6. Open issues'), [C['points']])
    add('internal section title kept', lambda w: w.edit(SAN, '## 1. Summary', '## 1. The short version'), [C['summary'], C['titles']])
    add('where-sources-disagree section added', lambda w: w.append(SAN, '\n## 8. Where sources disagree\n\nSee above.\n'), [C['titles']])
    add('metadata row left in', put('Dalia Nasser and Rohan', '| Status | Draft |\n\nDalia Nasser and Rohan'), [C['meta']])
    add('transcript mentioned', put('and discussed Eastgate.', 'and discussed Eastgate, as heard in the transcript.'), [C['trans']])
    add('re-check note left in', put('and discussed Eastgate.', 'and discussed Eastgate (heard as "East Gate").'), [C['trans']])
    add('Our-reading line left in', put('## 3. The freeze moves the cutover\n\n', '## 3. The freeze moves the cutover\n\n**Our reading.** The freeze was always there.\n\n'), [C['reading']])
    add('strategy wording left in', put('no extra staff are needed.', 'no extra staff are needed; we would raise a change request.'), [C['reading']])
    add('third-party company named', put('because it is the largest depot', 'because it is the largest depot, unlike Saltmarsh Freight'), [C['third']])
    add('unconfirmed term left in', put('per-door setup record', 'dock-door profile (unconfirmed)'), [C['unconf']])
    add('colloquial quote left in', put('dock-area coverage can be fixed', 'the dock-area Wi-Fi is a graveyard and can be fixed'), [C['quote']])
    add('numbering stripped from most sections',
        lambda w: [w.edit(SAN, f'## {n}. ', '## ') for n in (3, 4, 5, 6, 7)], [C['numbered']])
    add('section bodies hollowed out', lambda w: w.write(SAN, hollow(w.read(SAN), (2, 3, 4, 5, 7))), [C['numbered']])
    add('Who table removed', lambda w: w.edit(SAN, SANITISED[SANITISED.index('| Who'):SANITISED.index('Dalia Nasser')], ''), [C['who']])
    add('decision dropped', lambda w: w.write(SAN, w.read(SAN).replace('shadow run', 'trial').replace('Shadow run', 'Trial')), [C['decision']])
    add('internal recap edited', lambda w: w.append(MD, '\nEdited.\n'), [C['internal']])
    add('internal recap deleted', lambda w: w.delete(HTML), [C['internal']])
    add('Input/ file edited', lambda w: w.append(B.TRANSCRIPT, '\nextra line\n'), [C['inp']])
    add('recap promoted into Artefacts/', lambda w: w.write('Artefacts/Meetings/20261105_Rollout-planning/r.md', 'x\n'), [C['art']])
    return cases


# ---------------------------------------------------------------- runner

SUITES = [
    ('recap_from_transcript', 'recap-from-transcript', recap_setup, recap_cases),
    ('verify_planted_defects', 'verify-planted-defects', verify_setup, verify_cases),
    ('client_safe_copy', 'client-safe-copy', client_setup, client_cases),
]


def run_judge(judges, name, ws):
    script = judges / name / 'script'
    p = subprocess.run([str(script)], cwd=ws.root, capture_output=True, text=True, timeout=120)
    fails = {line[5:].split(' -- ', 1)[0] for line in p.stdout.splitlines() if line.startswith('FAIL ')}
    return p.returncode, fails, p


def main():
    judges, work = Path(sys.argv[1]), Path(sys.argv[2])
    problems, total = [], 0
    for name, case, setup, make_cases in SUITES:
        cases = make_cases()
        count = [0]

        def fresh(tag, **kw):
            count[0] += 1
            ws = WS(case, work / f'{name}-{count[0]}')
            setup(ws, **kw)
            return ws

        goods = [('good sample', {}), ('good sample, alternative formatting', {'alt': True})]
        if setup is not client_setup:
            goods.append(('good sample without the installed checker', {'installed': False}))
        for label, kw in goods:
            code, fails, p = run_judge(judges, name, fresh(label, **kw))
            total += 1
            if code != 0 or fails or p.stderr.strip():
                problems.append(f'{name}: {label} should pass: exit {code}, FAIL {sorted(fails)} {p.stderr.strip()[:300]}')
        for label, mutate, expect in cases:
            ws = fresh(label)
            mutate(ws)
            code, fails, p = run_judge(judges, name, ws)
            total += 1
            if code == 0 or fails != expect or p.stderr.strip():
                problems.append(f'{name}: "{label}" should fail exactly {sorted(expect)}; got exit {code}, '
                                f'FAIL {sorted(fails)} {p.stderr.strip()[:300]}')
        print(f'{name}: {len(goods)} good and {len(cases)} bad workspaces checked')
    if problems:
        print('\n'.join(['SELFTEST FAILED'] + problems))
        sys.exit(1)
    print(f'{total} workspaces behaved as expected')


if __name__ == '__main__':
    main()
