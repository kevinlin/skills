#!/usr/bin/env python3
"""Self-test for the gap-analysis script judges. Prints "ok" and exits 0 when every judge behaves as expected.

Each judge is run the way skill-up runs it: copied into a fresh temp dir as a file named "script" and executed with
the case workspace as cwd and the final reply in EVAL_FINAL_MESSAGE. Every judge meets one hand-made good workspace,
which must pass with no FAIL line, and several bad ones, each of which must fail on the check named in its expect() call.

The good samples are hand-built from build_fixtures.py's builders (or, for the update cases, from the shipped
fixture report plus the exact edit the skill prescribes); each bad sample is that good sample with one defect.

Usage: python3 selftest.py        (also runs build_fixtures.py --check first, so a stale fixture or judge fails here)
"""
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True      # keep __pycache__ out of the skill directory (it changes the digest)
HERE = Path(__file__).resolve().parent
FIX = HERE.parent
sys.path.insert(0, str(FIX))
import build_fixtures as bf  # noqa: E402

GAP = bf.GAPDIR
OLD, NEW = bf.OLD_DATE, bf.NEW_DATE
FAILURES = []


# ---- harness ----

def run_judge(tmp, judge, ws, message):
    box = tmp / 'judges' / judge
    box.mkdir(parents=True, exist_ok=True)
    script = box / 'script'
    shutil.copy(HERE / f'judge_{judge}.py', script)        # skill-up uploads a judge as a file named "script"
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    env = {k: v for k, v in os.environ.items() if not k.startswith('EVAL_')}
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    if message is not None:
        env['EVAL_FINAL_MESSAGE'] = message
    p = subprocess.run([str(script)], cwd=ws, env=env, capture_output=True, text=True, timeout=60)
    return p.returncode, p.stdout + p.stderr


def workspace(tmp, name, repo, files=None):
    ws = tmp / 'work' / name
    shutil.copytree(bf.REPOS / repo, ws)
    for rel, content in (files or {}).items():
        path = ws / rel
        if content is None:
            path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')
    return ws


def expect(tmp, judge, name, repo, files, message, fails=None):
    """fails=None: must pass cleanly. fails='text': must exit 1 with a FAIL line containing text."""
    ws = workspace(tmp, f'{judge}-{name}', repo, files)
    rc, out = run_judge(tmp, judge, ws, message)
    bad_lines = [l for l in out.splitlines() if l.startswith('FAIL')]
    if fails is None:
        ok = rc == 0 and not bad_lines
        why = 'expected a clean pass'
    else:
        ok = rc == 1 and any(fails in l for l in bad_lines)
        why = f'expected FAIL containing {fails!r}'
    print(('ok   ' if ok else 'FAIL ') + f'{judge}: {name}' + ('' if ok else f'  ({why})'))
    if not ok:
        FAILURES.append(f'{judge}: {name}\n' + '\n'.join('      ' + l for l in out.splitlines()[-14:]))


# ---- sample builders ----

def row(*a):
    return bf._row(*a)


SETTLE = dict(
    topic='WS6 Settlement', ws_context='WS6 Rebate Accounting \u2014 Settlement',
    sources=['output/process/BPMN/WS6-02_Settlement.bpmn', 'input/Detailed_Requirements.md'], date=NEW,
    phases=[
        ('1. Calculate', [
            ('inscope', 'Start_PeriodClose', 'FR_M20', 'Settlement period closes', 'The run starts at period close.'),
            ('inscope', 'Task_CalcSettlement', 'FR_M20', 'Calculate rebate settlement', 'Accrued less prior settlements.')]),
        ('2. Review and post', [
            ('inscope', 'Task_FinanceReview', 'FR_M22', 'Finance review', 'Above the threshold.'),
            ('implied', 'Task_PostCreditNote', 'FR_M24', 'Post credit note', 'FR_M24 says credit memo. <strong>See AMB-01.</strong>'),
            ('gap', 'Task_HoldDispute', 'FR_M26', 'Hold for dispute', 'Dead end. <strong>See BPM-01.</strong>')])],
    rows=[
        row('CTR-01', 'Settlement run sizing contradicts the RFP',
            'RFP \u00a73.1 sizes a run at 1,200 customer accounts; <code>NFR-P02</code> allows 4 hours for 200 accounts, a 6\u00d7 gap.',
            'The run window cannot be committed to.', 'critical', 'ws6'),
        row('BPM-01', 'Dispute hold is a dead end',
            '<code>Task_HoldDispute</code> has no outgoing flow, so a disputed settlement never resolves (<code>FR_M26</code>).',
            'A disputed settlement stalls with no owner.', 'high', 'ws6'),
        row('MFR-01', 'Partial settlement has no FR',
            'The FeatureSpec lists partial settlement against open accruals as P0; no FR backs it (<code>FeatureSpec</code>).',
            'The vendor would price a P0 feature nobody specified.', 'high', 'ws6'),
        row('AMB-01', 'Credit memo vs credit note',
            '<code>FR_M24</code> says "credit memo"; RFP \u00a73.1 and <code>Task_PostCreditNote</code> say "credit note". '
            'The glossary lists no synonym.', 'Two documents would need two postings.', 'medium', 'ws6'),
        row('G-01', 'Audit trail not modelled',
            '<code>FR_M28</code> logs every approval decision but <code>Task_FinanceReview</code> writes no record.',
            'The audit trail has no source.', 'low', 'ws6'),
    ],
    confirmed=['Settlement calculation (FR_M20)'],
    implied=['Run sizing mismatch (CTR-01)', 'Credit memo vs credit note (AMB-01)'],
    gap=['Dispute hold dead end (BPM-01)', 'Partial settlement has no FR (MFR-01)', 'Audit trail not modelled (G-01)'],
)
FRESH_PATH = f'{GAP}/ws6-settlement-gap-analysis.html'
FRESH_MSG = (f'Saved {FRESH_PATH}. Want me to refresh gap-register.html? The Critical and High gaps also belong in '
             'your open-questions file; where does it live?')


def fresh_html(**over):
    spec = dict(SETTLE)
    spec.update(over)
    return bf.report_html(**spec)


def swap(html, old, new, count=1):
    assert old in html, old
    return html.replace(old, new, count)


def drop_row(html, id_):
    new = re.sub(r'      <tr[^>]*>\s*<td>' + re.escape(id_) + r'</td>.*?</tr>\n', '', html, count=1, flags=re.S)
    assert new != html, id_
    return new


def row_block(html, id_):
    m = re.search(r'      <tr[^>]*>\s*<td>' + re.escape(id_) + r'</td>.*?</tr>\n', html, re.S)
    assert m, id_
    return m.group(0)


def test_fresh(tmp):
    good = fresh_html()

    def go(name, html, fails=None, path=FRESH_PATH, message=FRESH_MSG):
        expect(tmp, 'fresh_report', name, 'fresh-settlement', {path: html}, message, fails)

    go('good report', good)
    expect(tmp, 'fresh_report', 'no report saved', 'fresh-settlement', {}, FRESH_MSG, 'a *-gap-analysis.html report was saved')
    go('underscored filename', good, path=f'{GAP}/WS6 Settlement_gap_analysis.html', fails='filename is <topic>-gap-analysis.html')
    go('badge-form severity', swap(good, '<td class="sev-critical">Critical</td>',
                                   '<td><span class="sev sev-critical">Critical</span></td>'),
       fails='severity is a bare class')
    go('register-form workstream pill', good.replace('pill pill-ws6', 'ws ws-ws6'), fails='workstream cells use pill-ws pills')
    go('theme JS stripped', swap(good, 'function setTheme', 'function setMode'), fails='theme JS and light-theme CSS kept')
    go('external stylesheet', swap(good, '</head>', '<link rel="stylesheet" href="x.css"></head>'), fails='self-contained HTML')
    go('template placeholder left', swap(good, '<h2>Gap Register', '<h2>&lt;Short title&gt; Gap Register'),
       fails='no template placeholder text')
    go('arch bullet missing', swap(good, '      <li>Partial settlement has no FR (MFR-01)</li>\n', ''),
       fails='every gap row is mirrored')
    go('bullet cites a ghost row', swap(good, '<li>Audit trail not modelled (G-01)</li>',
                                        '<li>Audit trail not modelled (G-01)</li>\n      <li>Ghost (G-07)</li>'),
       fails='no arch-box bullet cites a gap ID')
    go('dead end filed under G-', good.replace('BPM-01', 'G-09'), fails='BPMN dead-end task is a BPM- row')
    go('missing FR filed under G-', good.replace('MFR-01', 'G-08'), fails='P0 feature with no FR is an MFR- row')
    go('contradiction not naming both values', swap(good, '1,200 customer accounts', 'the RFP figure for accounts'),
       fails='RFP-vs-NFR contradiction is a CTR- row')
    go('contradiction filed under G-', good.replace('CTR-01', 'G-07'), fails='RFP-vs-NFR contradiction is a CTR- row')
    go('credit memo not raised as AMB-', good.replace('AMB-01', 'G-06'), fails='undeclared term variant is an AMB- row')
    syn = fresh_html(rows=SETTLE['rows'] + [row('AMB-02', 'Rebate vs claim settlement',
                                                'RFP says "rebate settlement"; <code>FR_M20</code> says "claim settlement".',
                                                'Terminology.', 'low', 'ws6')],
                     gap=SETTLE['gap'] + ['Rebate vs claim settlement (AMB-02)'])
    go('declared synonym raised as AMB-', syn, fails='glossary-declared synonym')
    go('no <code> citation on a row', swap(good, '<code>FR_M28</code> logs', 'FR_M28 logs').replace(
        '<code>Task_FinanceReview</code> writes', 'Task_FinanceReview writes'), fails='every row cites its source in <code>')
    go('rows out of order', fresh_html(rows=list(reversed(SETTLE['rows']))), fails='rows are ordered')
    go('blockquote provenance', swap(good, '<h2>Gap Register', '<blockquote>RFP source reference: x</blockquote><h2>Gap Register'),
       fails='no Markdown blockquote provenance')
    go('owner column added', swap(good, '<th style="width:100px;">Workstream</th>',
                                  '<th style="width:100px;">Workstream</th><th>Owner</th>'),
       fails='no Owner column')
    go('reply never names the file', good, message='Done. Anything else?', fails='final reply names the saved report')
    go('reply skips the open-questions loop', good, message=f'Saved {FRESH_PATH}. Want me to refresh the register?',
       fails='open-questions loop')


def test_asks(tmp):
    ask = ('Before I draft anything: what is the project\'s gap-analysis output folder, the one that holds the '
           '*-gap-analysis.html files? And where is the glossary or ubiquitous-language file?')
    expect(tmp, 'asks_inputs', 'good', 'returns',
           {'.claude/skills/gap-analysis/assets/individual-report.template.html': '<html></html>'}, ask)
    expect(tmp, 'asks_inputs', 'wrote a report anyway', 'returns',
           {'docs/gap-analysis/returns-gap-analysis.html': '<html></html>'}, ask, 'no HTML report was written')
    expect(tmp, 'asks_inputs', 'wrote a report elsewhere', 'returns',
           {'reports/returns.html': '<html></html>'}, ask, 'no HTML report was written')
    expect(tmp, 'asks_inputs', 'asks only for the folder', 'returns', {},
           'Which gap-analysis output folder should I save to?', 'asks for the glossary')
    expect(tmp, 'asks_inputs', 'asks only for the glossary', 'returns', {},
           'Where is the glossary file?', 'asks for the gap-analysis output folder')
    expect(tmp, 'asks_inputs', 'states instead of asking', 'returns', {},
           'I will save into docs/gap-analysis and use no glossary.', 'asks for the gap-analysis output folder')
    expect(tmp, 'asks_inputs', 'no reply exported', 'returns', {}, None, 'EVAL_FINAL_MESSAGE was not exported')


APPROVAL = bf.approval_report()
APPROVAL_PATH = f'{GAP}/approval-workflow-gap-analysis.html'
REGISTER_PATH = f'{GAP}/gap-register.html'
NEW_ROW = '''      <tr>
        <td>BPM-04</td>
        <td><strong>No error-handling sub-processes for hub-mediated SAP calls</strong><br>WS4-01 / WS4-02 / WS4-03 do not model boundary error events or retry flows for SAP calls routed via the integration hub (<code>FR_W08</code>).</td>
        <td>An SAP-side failure during approval routing leaves the task in an undefined state; error handling must be specified before build.</td>
        <td class="sev-high">High</td>
        <td><span class="pill pill-ws4">WS4</span></td>
      </tr>
'''
UPDATE_MSG = 'Added BPM-04 as a High WS4 row, mirrored it in box-gap and refreshed the date. Want me to refresh the register?'


def edit_add(html, row=NEW_ROW, bullet='<li>Hub error handling for SAP calls (BPM-04)</li>', date=NEW, after='W-01',
             box_after='<li>Notification wording (G-01)</li>'):
    block = row_block(html, after)
    html = swap(html, block, block + row)
    if bullet:
        html = swap(html, box_after, box_after + '\n      ' + bullet)
    return swap(html, OLD, date) if date else html


def test_update(tmp):
    def go(name, html, fails=None, message=UPDATE_MSG, extra=None):
        files = {APPROVAL_PATH: html}
        files.update(extra or {})
        expect(tmp, 'update_row', name, 'update-approval', files, message, fails)
    good = edit_add(APPROVAL)
    go('good edit', good)
    go('G- prefix instead of BPM-', edit_add(APPROVAL, NEW_ROW.replace('BPM-04', 'G-03'), '<li>Hub error handling (G-03)</li>'),
       'the new row takes the next BPM- number')
    go('arch bullet not added', edit_add(APPROVAL, bullet=None), 'box-gap gained exactly one bullet')
    go('bullet in box-implied instead', edit_add(APPROVAL, bullet=None).replace(
        '<li>Approver / Authoriser terminology (AMB-01)</li>',
        '<li>Approver / Authoriser terminology (AMB-01)</li>\n      <li>Hub error handling (BPM-04)</li>'),
       'box-gap gained exactly one bullet')
    go('badge-form severity', edit_add(APPROVAL, NEW_ROW.replace('<td class="sev-high">High</td>',
                                                               '<td><span class="sev sev-high">High</span></td>')),
       'new row severity is the bare-class cell')
    go('register-form pill', edit_add(APPROVAL, NEW_ROW.replace('pill pill-ws4', 'ws ws-ws4')), 'new row uses the individual-report pill')
    go('severity Medium', edit_add(APPROVAL, NEW_ROW.replace('sev-high">High', 'sev-medium">Medium')),
       'new row severity is the bare-class cell')
    go('FR_W08 not cited', edit_add(APPROVAL, NEW_ROW.replace('<code>FR_W08</code>', 'FR_W08')), 'new row cites FR_W08')
    go('date not refreshed', edit_add(APPROVAL, date=None), 'subtitle date refreshed')
    go('an original row dropped', drop_row(good, 'BPM-03'), 'every original gap ID')
    go('an original row reworded', swap(good, 'a 2.5\u00d7 difference', 'a big difference'), 'existing rows are byte-for-byte')
    go('new row in the Low block', edit_add(APPROVAL, after='G-01', box_after='<li>Notification wording (G-01)</li>'),
       'rows stay ordered')
    go('legend refactored', swap(good, 'In-scope activity (FR-mapped)', 'In-scope activity'), 'nothing outside the subtitle')
    go('theme JS touched', swap(good, "localStorage.setItem('gap-analysis-theme'", "localStorage.setItem('theme'"),
       'nothing outside the subtitle')
    go('two rows added', swap(good, NEW_ROW, NEW_ROW + NEW_ROW.replace('BPM-04', 'BPM-05')), 'exactly one row was added')
    go('register rewritten too', good, 'gap-register.html is not rewritten', extra={REGISTER_PATH: bf.stale_register(NEW)})
    go('owner column added', swap(good, '<th style="width:100px;">Workstream</th>',
                                  '<th style="width:100px;">Workstream</th><th>Owner</th>'), 'no Owner column')
    go('reply does not offer the register', good, 'offers to refresh the master register', message='Done, BPM-04 added.')
    go('report deleted', '', 'every original gap ID')


def edit_resolve(html, date=NEW, move=True, mark_row=True, mark_sev=True):
    block = row_block(html, 'CTR-01')
    new = block
    if mark_row:
        new = swap(new, '<tr>', '<tr class="resolved">')
    if mark_sev:
        new = swap(new, '<td class="sev-critical">Critical</td>', '<td class="sev-resolved">Resolved</td>')
    html = swap(html, block, new)
    if move:
        html = swap(html, '      <li>Approval SLA mismatch (CTR-01)</li>\n', '')
        html = swap(html, '<li>Approval decision recorded (FR_W04)</li>',
                    '<li>Approval decision recorded (FR_W04)</li>\n      <li>Approval SLA confirmed at 5 business days (FR_W03)</li>')
    return swap(html, OLD, date) if date else html


RESOLVE_MSG = 'CTR-01 is marked Resolved, moved to the aligned box, and the date is refreshed.'


def test_resolve(tmp):
    def go(name, html, fails=None, extra=None):
        files = {APPROVAL_PATH: html}
        files.update(extra or {})
        expect(tmp, 'mark_resolved', name, 'update-approval', files, RESOLVE_MSG, fails)
    good = edit_resolve(APPROVAL)
    go('good edit', good)
    go('bullet dropped instead of moved', swap(good, '\n      <li>Approval SLA confirmed at 5 business days (FR_W03)</li>', ''))
    go('row deleted', drop_row(good, 'CTR-01'), 'the resolved row is kept')
    go('severity not changed', edit_resolve(APPROVAL, mark_sev=False), 'severity cell is <td class="sev-resolved">')
    go('tr class missing', edit_resolve(APPROVAL, mark_row=False), '<tr> carries class="resolved"')
    go('badge-form severity', swap(good, '<td class="sev-resolved">Resolved</td>',
                                   '<td><span class="sev sev-resolved">Resolved</span></td>'), 'severity cell is <td class="sev-resolved">')
    go('bullet left in box-implied', edit_resolve(APPROVAL, move=False), 'bullet left box-implied and box-gap')
    go('moved bullet has no citation', swap(good, 'Approval SLA confirmed at 5 business days (FR_W03)', 'Approval SLA confirmed'),
       'box-confirmed keeps its bullets')
    go('date not refreshed', edit_resolve(APPROVAL, date=None), 'subtitle date refreshed')
    go('another row re-severitied', swap(good, '<td class="sev-high">High</td>', '<td class="sev-medium">Medium</td>'),
       'every other row is byte-for-byte untouched')
    go('legend refactored', swap(good, 'Gap: missing or under-specified', 'Gap'), 'nothing outside the subtitle')
    go('register rewritten too', good, 'gap-register.html is not rewritten', extra={REGISTER_PATH: bf.stale_register(NEW)})
    go('a new row added', edit_add(good, date=None), 'no row is added or deleted')


REG_LINKS = [('quote-creation-gap-analysis.html', 'Quote Creation'),
             ('rebate-settlement-gap-analysis.html', 'Rebate Settlement'),
             ('retention-gap-analysis.html', 'Retention')]
REG_ROWS = [
    bf.reg_row(1, 'SAP-01', 'SAP condition type undefined', '<code>FR_Q12</code>; Quote Creation report.',
               'Payload cannot be built.', 'critical', 'ws5', 'owner-cust-sap'),
    bf.reg_row(5, 'CTR-01', 'Account volume contradicts the RFP',
               'RFP \u00a73: 1,200 accounts; <code>NFR-P02</code>: 200. Found in the Quote Creation and Rebate Settlement reports.',
               'Capacity is priced on two volumes.', 'critical', 'ws6', 'owner-shared'),
    bf.reg_row(2, 'G-01', 'Accrual reversal owner unclear', '<code>FR_M20</code>.', 'Double or no booking.',
               'high', 'ws6', 'owner-shared'),
    bf.reg_row(7, 'REG-01', 'Retention period unspecified', '<code>NFR-A01</code>.', 'Records may be deleted early.',
               'high', 'reg', 'owner-legal'),
    bf.reg_row(3, 'BPM-01', 'Quote validation has no failure path', '<code>Task_ValidateQuote</code>.', 'Quotes stall.',
               'medium', 'ws5', 'owner-vendor'),
    bf.reg_row(5, 'AMB-01', 'Credit memo vs credit note', '<code>FR_M24</code>.', 'Two postings.',
               'medium', 'ws6', 'owner-cust-biz'),
    bf.reg_row(6, 'COM-01', 'Price master priced but out of scope', '<code>FR_M20</code>.', 'Unscoped work priced.',
               'medium', 'comm', 'owner-cust-biz'),
    bf.reg_row(3, 'G-02', 'Finance role mapping', 'Answered.', 'Closed.', 'resolved', 'ws1', 'owner-cust-biz'),
]
REG_MSG = f'Regenerated {REGISTER_PATH} from the three reports.'


def reg_block(html, id_):
    m = re.search(r'    <tr data-sev[^>]*>\s*<td class="gap-id">' + re.escape(id_) + r'</td>.*?</tr>\n', html, re.S)
    assert m, id_
    return m.group(0)


def test_register(tmp):
    def reg(rows=REG_ROWS, date=NEW, links=REG_LINKS):
        return bf.register_html(date, links, rows)

    def go(name, html, fails=None, extra=None, message=REG_MSG):
        files = {REGISTER_PATH: html}
        files.update(extra or {})
        expect(tmp, 'register', name, 'regenerate-register', files, message, fails)

    def with_row(id_, **kw):
        return [dict(r, **kw) if r['id'] == id_ else r for r in REG_ROWS]
    good = reg()
    go('good register', good)
    go('CTR-01 listed twice', reg(REG_ROWS + [bf.reg_row(5, 'CTR-01', 'Account volume (quote report)', 'RFP \u00a73.', 'x', 'high', 'ws5', 'owner-shared')]),
       'exactly once')
    go('a gap missing', reg([r for r in REG_ROWS if r['id'] != 'COM-01']), 'exactly once')
    go('CTR-01 kept at the lower severity', reg(with_row('CTR-01', sev='high')), 'kept once, at the higher severity')
    go('CTR-01 cites one report only', reg(with_row('CTR-01', detail='RFP \u00a73: 1,200; <code>NFR-P02</code>: 200.')),
       'notes both source reports')
    go('tile count wrong', swap(good, '<div class="score-count">2</div>', '<div class="score-count">9</div>'),
       'tile counts equal the rows')
    go('tile loses its ID list', swap(good, '<div class="score-ids">SAP-01 \u00b7 CTR-01</div>', '<div class="score-ids">2 gaps</div>'),
       'each tile lists the IDs')
    go('tile missing', swap(good, 'tile-open', 'tile-extra'), 'five scorecard tiles in order')
    go('data-ws missing on a row', swap(good, ' data-ws="reg"', ''), 'every row has data-sev and data-ws')
    go('data-ws invalid', swap(good, 'data-ws="comm"', 'data-ws="commercial"'), 'every row has data-sev and data-ws')
    go('data-ws has no filter button', swap(good, "filterRows('comm')", "filterRows('c0mm')"), 'every data-ws value used has a filter button')
    go('pill form in a register', swap(good, 'ws ws-reg', 'pill pill-reg'), 'workstream is the register form')
    go('bare-class severity in a register', swap(good, '<td><span class="sev sev-critical">Critical</span></td>',
                                                 '<td class="sev-critical">Critical</td>'), 'severity is the badge form')
    go('owner column dropped', re.sub(r'<td><span class="owner[^>]*>.*?</span></td>\n?', '', swap(good, '<th>Owner</th>', '')),
       'every row has the six register cells')
    go('wrong owner for the SAP blocker', swap(good, 'owner owner-cust-sap', 'owner owner-vendor'), 'owner pills fit the gap')
    go('resolved row loses its class', swap(good, ' class="resolved"', ''), 'the resolved row G-02')
    go('SAP row under the wrong category', reg(with_row('SAP-01', cat=5)), 'fixed-category rows sit under')
    go('invented category', swap(good, 'Regulatory &amp; Compliance', 'Misc Findings'), 'categories are drawn from the seven')
    a, b = reg_block(good, 'CTR-01'), reg_block(good, 'AMB-01')
    go('rows unsorted within a category', swap(swap(good, a, '@@'), b, a).replace('@@', b),
       'rows within each category run')
    go('link to a report missing', reg(links=REG_LINKS[:2]), 'report quick links')
    go('link to the register itself', reg(links=REG_LINKS + [('gap-register.html', 'Register')]), 'report quick links')
    go('date not refreshed', reg(date=OLD), 'subtitle "Last updated" date refreshed')
    go('footer date stale', swap(good, f'All workstreams \u00b7 {NEW} \u00b7 Integrated with full cross-file gap analysis\n</div>',
                                 f'All workstreams \u00b7 {OLD} \u00b7 Integrated with full cross-file gap analysis\n</div>'),
       'footer date refreshed too')
    go('filter JS removed', swap(good, 'function filterRows', 'function filterX'), 'filter bar and filterRows() JS kept')
    go('theme JS removed', swap(good, 'function applyTheme(mode) {', 'function applyX(mode) {'),
       'self-contained HTML document with the theme toggle')
    go('an input report edited', good, 'individual reports and the glossary are untouched',
       extra={f'{GAP}/retention-gap-analysis.html': '<html>edited</html>'})
    go('reply does not name the register', good, 'final reply names the regenerated register', message='Done.')


def test_no_glossary(tmp):
    base = ('docs/gap-analysis/returns-authorisation-gap-analysis.html')
    note = ('<p class="section-intro">No glossary supplied \u2014 terminology variants flagged conservatively; '
            'reconcile against a glossary before circulating widely.</p>\n')
    spec = dict(
        topic='Returns Authorisation', ws_context='Returns handling',
        sources=['docs/returns/returns-authorisation.bpmn', 'docs/returns/requirements.md'], date=NEW,
        phases=[('1. Authorise', [('inscope', 'Task_IssueRma', 'FR_R03', 'Issue RMA number', 'Code issued.'),
                                  ('implied', 'Task_ApplyRestockingFee', 'FR_R05', 'Apply restocking fee',
                                   'Charge deducted. <strong>See AMB-02.</strong>')])],
        rows=[row('AMB-01', 'RMA number vs return authorisation code',
                  'BPMN <code>Task_IssueRma</code> says "RMA number"; <code>FR_R03</code> says "return authorisation code".',
                  'Two names for one code, or two codes.', 'medium', 'ws5'),
              row('AMB-02', 'Restocking fee vs re-stock charge',
                  'BPMN <code>Task_ApplyRestockingFee</code> says "restocking fee"; <code>FR_R05</code> says "re-stock charge".',
                  'Fee and charge may be calculated differently.', 'medium', 'ws5'),
              row('BPM-01', 'No rejection path after the policy check',
                  '<code>Task_CheckPolicy</code> has one outgoing flow (<code>FR_R02</code>).', 'A refused request stalls.',
                  'high', 'ws5')],
        confirmed=['Return requested (FR_R01)'], implied=['RMA number vs return authorisation code (AMB-01)',
                                                         'Restocking fee vs re-stock charge (AMB-02)'],
        gap=['No rejection path (BPM-01)'])
    good = swap(bf.report_html(**spec), '<div class="flow-container">', note + '<div class="flow-container">')
    msg = f'Saved {base}.'

    def go(name, html, fails=None, message=msg):
        expect(tmp, 'no_glossary', name, 'returns', {base: html}, message, fails)
    go('good report', good)
    go('no note about the glossary', swap(good, note, ''), 'the intro, before the gap table, says no glossary')
    go('note placed after the table', swap(swap(good, note, ''), '</body>', note + '</body>'),
       'the intro, before the gap table')
    go('term pair filed under G-', good.replace('AMB-01', 'G-01'), 'RMA number" vs "return authorisation code" is an AMB-')
    go('one variant dropped', good.replace('re-stock charge', 'charge'), 'restocking fee" vs "re-stock charge"')
    go('theme JS stripped', swap(good, 'function applyTheme', 'function applyX'), 'self-contained HTML document with the theme JS')
    go('badge-form severity', swap(good, '<td class="sev-high">High</td>', '<td><span class="sev sev-high">High</span></td>'),
       'severity is a bare class')
    go('bullet missing for a row', swap(good, '      <li>No rejection path (BPM-01)</li>\n', ''), 'every gap row is mirrored')
    expect(tmp, 'no_glossary', 'nothing saved', 'returns', {}, msg, 'a *-gap-analysis.html report was saved')


def main():
    p = subprocess.run([sys.executable, str(FIX / 'build_fixtures.py'), '--check'], capture_output=True, text=True)
    print(p.stdout.strip() or p.stderr.strip())
    if p.returncode:
        sys.exit('fixtures or judge regions are stale; run build_fixtures.py --write')
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        for fn in (test_fresh, test_asks, test_update, test_resolve, test_register, test_no_glossary):
            fn(tmp)
    if FAILURES:
        print('\n' + '\n'.join(FAILURES))
        sys.exit(f'{len(FAILURES)} self-test case(s) misbehaved')
    print('ok')


if __name__ == '__main__':
    main()
