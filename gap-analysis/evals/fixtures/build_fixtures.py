#!/usr/bin/env python3
"""Builds the synthetic HTML fixtures for the gap-analysis evals and keeps the judges in sync.

Usage:
    python3 build_fixtures.py --write   regenerate the HTML fixtures and the judges' generated regions
    python3 build_fixtures.py --check   exit 1 when anything on disk differs from what --write would produce

Everything here is invented: the "Contoso Rebates" project, its reports and its gaps. The markup follows the
gap-analysis house style (theme toggle, bare-class severity cells, pill-ws pills, three arch boxes for an
individual report; badge severity, ws pills, owner pills, scorecard and filter bar for the register), but the
CSS is trimmed. It is used three ways: the update and register cases start from these files, the judges embed
hashes of them as the "unchanged" baseline, and selftest.py builds its hand-made good and bad samples from the
same builders.

The COMMON region of every judge is pasted from judge_common.py, and the FIXTURE DATA region is computed from the
files below, so a judge never carries a hand-edited copy.
"""
import html
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True      # keep __pycache__ out of the skill directory (it changes the digest)
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import judge_common as jc  # noqa: E402  (the COMMON region's source of truth)

REPOS = HERE / 'repos'
SCRIPTS = HERE / 'scripts'
GAPDIR = 'output/requirement/gap-analysis'
OLD_DATE = '2026-03-12'
NEW_DATE = '2026-04-30'

CSS_COMMON = """
  * { box-sizing: border-box; margin: 0; padding: 0; }
  :root { --bg-page:#0f1117; --bg-card:#0f172a; --border:#1e293b; --text-primary:#f8fafc; --text-body:#e2e8f0;
    --text-muted:#94a3b8; --text-dim:#64748b; --text-faint:#475569; --bg-header:#1e293b; --bg-hover:#0f172a;
    --toggle-bg:#1e293b; --toggle-active-bg:#334155; --toggle-text:#94a3b8; --toggle-active-text:#f1f5f9; }
  [data-theme="light"] { --bg-page:#f8fafc; --bg-card:#ffffff; --border:#e2e8f0; --text-primary:#0f172a;
    --text-body:#1e293b; --text-muted:#64748b; --text-dim:#94a3b8; --text-faint:#94a3b8; --bg-header:#f1f5f9;
    --bg-hover:#f1f5f9; --toggle-bg:#f1f5f9; --toggle-active-bg:#e2e8f0; --toggle-text:#64748b;
    --toggle-active-text:#0f172a; }
  .theme-toggle { position: fixed; top: 16px; right: 16px; display: flex; background: var(--toggle-bg);
    border-radius: 8px; padding: 3px; font-size: 12px; }
  .theme-toggle button { padding: 5px 10px; border: none; border-radius: 6px; background: transparent;
    color: var(--toggle-text); cursor: pointer; }
  .theme-toggle button.active { background: var(--toggle-active-bg); color: var(--toggle-active-text); }
  body { font-family: 'Segoe UI', sans-serif; background: var(--bg-page); color: var(--text-body); padding: 32px 24px; }
  h1 { font-size: 22px; color: var(--text-primary); margin-bottom: 4px; }
  .subtitle { font-size: 13px; color: var(--text-dim); margin-bottom: 32px; }
  table { width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 24px; }
  th { text-align: left; padding: 8px 12px; background: var(--bg-header); color: var(--text-muted); font-size: 10px; }
  td { padding: 9px 12px; border-bottom: 1px solid var(--border); vertical-align: top; }
  tr.resolved td { opacity: .55; }
"""

CSS_REPORT = """
  .legend { display: flex; gap: 20px; margin-bottom: 28px; font-size: 12px; }
  .legend-dot { width: 12px; height: 12px; border-radius: 3px; display: inline-block; }
  .dot-inscope { background: #0ea5e9; } .dot-implied { background: #f59e0b; } .dot-gap { background: #ef4444; }
  .phase-row { display: grid; grid-template-columns: 160px 1fr; margin-bottom: 4px; }
  .phase-label { text-align: right; padding-right: 16px; font-size: 11px; color: var(--text-faint); }
  .phase-content { display: flex; gap: 12px; flex-wrap: wrap; padding: 12px 0 12px 20px; }
  .card { border-radius: 8px; padding: 12px 14px; min-width: 200px; max-width: 280px; }
  .card-inscope { background: #0c2340; border: 1px solid #0ea5e9; }
  .card-implied { background: #1c1200; border: 1px dashed #f59e0b; }
  .card-gap { background: #2d0a0a; border: 2px dashed #ef4444; }
  .card-bpmn { font-size: 9px; color: var(--text-faint); } .card-fr { font-size: 10px; }
  .card-title { font-size: 12px; font-weight: 700; } .card-desc { font-size: 11px; }
  .flow-arrow { align-self: center; font-size: 18px; }
  .gap-table-section { margin-top: 40px; border-top: 1px solid var(--border); padding-top: 28px; }
  .sev-critical { color: #f87171; font-weight: 700; } .sev-high { color: #fbbf24; font-weight: 600; }
  .sev-medium { color: #34d399; font-weight: 600; } .sev-low { color: var(--text-muted); }
  .sev-resolved { color: var(--text-dim); }
  .pill { display: inline-block; padding: 2px 8px; border-radius: 99px; font-size: 10px; font-weight: 700; }
  .pill-ws1 { color: #86efac; } .pill-ws4 { color: #fb923c; } .pill-ws5 { color: #38bdf8; }
  .pill-ws6 { color: #a5b4fc; } .pill-reg { color: #d8b4fe; } .pill-comm { color: #5eead4; }
  .arch-row { display: flex; gap: 12px; margin-top: 36px; }
  .arch-box { flex: 1; border-radius: 8px; padding: 16px; border: 1px solid var(--border); background: var(--bg-card); }
  .arch-box ul { list-style: none; font-size: 11px; line-height: 1.8; }
"""

CSS_REGISTER = """
  .scorecard { display: flex; gap: 12px; margin-bottom: 24px; }
  .score-tile { flex: 1; border-radius: 8px; padding: 14px; border: 1px solid var(--border); }
  .score-count { font-size: 28px; font-weight: 800; } .score-ids { font-size: 10px; color: var(--text-dim); }
  .report-links { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 20px; }
  .report-links a { padding: 4px 12px; border-radius: 99px; border: 1px solid var(--border); font-size: 12px; }
  .filter-bar { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 24px; }
  .filter-btn { padding: 4px 12px; border-radius: 6px; border: 1px solid var(--border); background: transparent;
    color: var(--text-muted); cursor: pointer; font-size: 11px; }
  .filter-btn.active { background: var(--toggle-active-bg); }
  .category-header { display: flex; gap: 14px; align-items: center; margin: 28px 0 10px; }
  .category-number { width: 28px; height: 28px; border-radius: 8px; text-align: center; font-weight: 700; }
  .category-title { font-size: 14px; font-weight: 700; } .category-desc { font-size: 11px; color: var(--text-dim); }
  .sev { display: inline-block; font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 99px; }
  .sev-critical { color: #f87171; } .sev-high { color: #fbbf24; } .sev-medium { color: #34d399; }
  .sev-low { color: var(--text-muted); } .sev-open { color: #a5b4fc; } .sev-resolved { color: var(--text-dim); }
  .owner, .ws { display: inline-block; font-size: 10px; font-weight: 600; padding: 2px 7px; border-radius: 4px; }
  .gap-id { font-weight: 700; white-space: nowrap; } .gap-title { font-weight: 600; }
  .gap-detail { font-size: 11px; color: var(--text-dim); margin-top: 3px; } .row-hidden { display: none; }
"""

THEME_JS = """
  function setTheme(mode) {
    localStorage.setItem('gap-analysis-theme', mode);
    applyTheme(mode);
    document.querySelectorAll('.theme-toggle button').forEach(b => b.classList.remove('active'));
    document.getElementById('theme-' + mode).classList.add('active');
  }
  function applyTheme(mode) {
    if (mode === 'system') {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
    } else {
      document.documentElement.setAttribute('data-theme', mode);
    }
  }
  (function() {
    const saved = localStorage.getItem('gap-analysis-theme') || 'system';
    applyTheme(saved);
    document.getElementById('theme-' + saved).classList.add('active');
  })();
"""

FILTER_JS = """
  function filterRows(filter) {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
    document.querySelectorAll('tbody tr').forEach(row => {
      const sev = row.dataset.sev || '', ws = row.dataset.ws || '';
      const show = filter === 'all' || sev === filter || ws === filter ||
        (filter === 'resolved' && sev === 'low') || (filter === 'ws1' && ws === 'ws2');
      row.classList.toggle('row-hidden', !show);
    });
  }
"""

TOGGLE = """<div class="theme-toggle">
  <button onclick="setTheme('system')" id="theme-system">System</button>
  <button onclick="setTheme('light')" id="theme-light">Light</button>
  <button onclick="setTheme('dark')" id="theme-dark">Dark</button>
</div>"""

LEGEND = """<div class="legend">
  <div class="legend-item"><span class="legend-dot dot-inscope"></span> In-scope activity (FR-mapped)</div>
  <div class="legend-item"><span class="legend-dot dot-implied"></span> Implied / inconsistent with requirements</div>
  <div class="legend-item"><span class="legend-dot dot-gap"></span> Gap: missing or under-specified</div>
</div>"""

PILL_LABEL = {'ws1': 'WS1', 'ws4': 'WS4', 'ws5': 'WS5', 'ws6': 'WS6', 'arch': 'ARCH', 'reg': 'REG', 'comm': 'COMM'}


DOT = ' \u00b7 '


def esc(s):
    return html.escape(s, quote=False)


def pills(keys):
    return ''.join(f'<span class="pill pill-{k}">{PILL_LABEL[k]}</span>' for k in keys)


def report_html(topic, ws_context, sources, date, phases, rows, confirmed, implied, gap):
    """One individual gap-analysis report in the house style (bare-class severity, pill pills, three arch boxes)."""
    phase_html = []
    for label, cards in phases:
        inner = '\n      <div class="flow-arrow">\u2192</div>\n'.join(
            f'''      <div class="card card-{cls}">
        <div class="card-bpmn">{bpmn}</div>
        <div class="card-fr">{fr}</div>
        <div class="card-title">{esc(title)}</div>
        <div class="card-desc">{desc}</div>
      </div>''' for cls, bpmn, fr, title, desc in cards)
        phase_html.append(f'''  <div class="phase-row">
    <div class="phase-label">{label}</div>
    <div class="phase-content">
{inner}
    </div>
  </div>''')
    row_html = []
    for r in rows:
        cls = ' class="resolved"' if r['sev'] == 'resolved' else ''
        row_html.append(f'''      <tr{cls}>
        <td>{r['id']}</td>
        <td><strong>{esc(r['title'])}</strong><br>{r['desc']}</td>
        <td>{esc(r['why'])}</td>
        <td class="sev-{r['sev']}">{r['sev'].capitalize()}</td>
        <td>{pills(r['pills'])}</td>
      </tr>''')

    def li(items):
        return '\n'.join(f'      <li>{esc(i)}</li>' for i in items)
    srcs = ' vs\n  '.join(f'<code style="color:var(--text-muted);">{s}</code>' for s in sources)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Contoso Rebates \u2014 {esc(topic)} Gap Analysis</title>
<style>{CSS_COMMON}{CSS_REPORT}</style>
</head>
<body>

{TOGGLE}

<h1>Contoso Rebates \u2014 {esc(topic)} Gap Analysis</h1>
<p class="subtitle">
  {ws_context} \u00b7 Source: {srcs} \u00b7 {date}
</p>

{LEGEND}

<div class="flow-container">
{chr(10).join(phase_html)}
</div><!-- end flow-container -->

<div class="gap-table-section">
  <h2>Gap Register \u2014 BPMN vs. RFP / Detailed Requirements</h2>
  <table>
    <thead>
      <tr>
        <th style="width:60px;">#</th>
        <th>Gap</th>
        <th>Why It Matters</th>
        <th style="width:90px;">Severity</th>
        <th style="width:100px;">Workstream</th>
      </tr>
    </thead>
    <tbody>
{chr(10).join(row_html)}
    </tbody>
  </table>
</div>

<div class="arch-row">
  <div class="arch-box box-confirmed">
    <h3>\u2713 BPMN \u2194 Requirements Aligned</h3>
    <ul>
{li(confirmed)}
    </ul>
  </div>
  <div class="arch-box box-implied">
    <h3>~ Implied / Inconsistent</h3>
    <ul>
{li(implied)}
    </ul>
  </div>
  <div class="arch-box box-gap">
    <h3>\u2717 Missing \u2014 Must Be Raised</h3>
    <ul>
{li(gap)}
    </ul>
  </div>
</div>

<script>{THEME_JS}</script>

</body>
</html>
'''


# ---- the approval-workflow report: the starting point of both update cases ----

def _row(id_, title, desc, why, sev, ws):
    return dict(id=id_, title=title, desc=desc, why=why, sev=sev, pills=[ws])


APPROVAL = dict(
    topic='Approval Workflow',
    ws_context='WS4 Internal Approval Workflows',
    sources=['WS4-01_Approval_Routing.bpmn', 'Detailed_Requirements.md'],
    phases=[
        ('1. Request', [
            ('inscope', 'Start_ApprovalRequested', 'FR_W01', 'Approval request raised from a quote',
             'A sales user submits a quote above the discount limit.'),
            ('inscope', 'Task_RouteToApprover', 'FR_W02', 'Route to the approver role',
             'The request is routed to the approver role for the quote owner\'s region.')]),
        ('2. Decision', [
            ('implied', 'Task_Approve', 'FR_W03', 'Approver decides within the SLA',
             'BPMN shows no timer. <strong>See CTR-01.</strong>'),
            ('gap', 'Task_ApprovalRejected', 'FR_W04', 'Rejected approval',
             'The rejection path ends without notifying the requester. <strong>See BPM-02.</strong>')])],
    rows=[
        _row('CTR-01', 'Approval SLA contradicts the RFP',
             'RFP \u00a75 gives approvers 2 business days to decide; <code>FR_W03</code> gives them 5 business days, '
             'a 2.5\u00d7 difference. Escalation timing cannot be designed until one figure is chosen.',
             'Escalation timers and the customer SLA report are built against one figure, so the bid cannot price both.',
             'critical', 'ws4'),
        _row('BPM-01', 'No timeout path on the approval task',
             '<code>Task_Approve</code> has no boundary timer, so a request nobody decides stays open forever '
             '(<code>FR_W03</code>).',
             'Without a timeout the SLA in FR_W03 cannot be enforced and open requests pile up silently.',
             'high', 'ws4'),
        _row('BPM-02', 'Rejected approvals dead-end',
             '<code>Task_ApprovalRejected</code> has no outgoing flow and no end event, and the requester is never '
             'told (<code>FR_W04</code>).',
             'A rejected quote stalls with no owner, which breaks the process at runtime.',
             'high', 'ws4'),
        _row('W-01', 'One approver per role, no delegate',
             'Each approver role has a single named user and no fallback during absence (<code>FR_W02</code>).',
             'The first holiday leaves requests unrouted at go-live.',
             'high', 'ws4'),
        _row('AMB-01', 'Approver vs Authoriser',
             '<code>FR_W02</code> says "Approver"; <code>FR_W05</code> says "Authoriser". The glossary lists no '
             'synonym.',
             'If these are two roles the routing table is incomplete; if one, the spec should say so.',
             'medium', 'ws4'),
        _row('BPM-03', 'Approval decision has no data object',
             'The decision and the approver\'s comment are not written to a data object in the BPMN '
             '(<code>FR_W04</code>).',
             'The audit trail the requirements ask for has nothing to read from.',
             'medium', 'ws4'),
        _row('G-01', 'Notification wording not specified',
             'No requirement sets the wording of the approval notification email (<code>FR_W01</code>).',
             'Wording can be settled during build.',
             'low', 'ws4'),
    ],
    confirmed=['Approval request raised from a quote (FR_W01)', 'Role-based approver routing (FR_W02)',
               'Approval decision recorded (FR_W04)'],
    implied=['Approval SLA mismatch (CTR-01)', 'Approver / Authoriser terminology (AMB-01)'],
    gap=['No timeout path on the approval task (BPM-01)', 'Rejected approvals dead-end (BPM-02)',
         'One approver per role, no delegate (W-01)', 'Approval decision data object (BPM-03)',
         'Notification wording (G-01)'],
)


def approval_report(date=OLD_DATE):
    return report_html(date=date, **APPROVAL)


# ---- the three small reports behind the register case ----

QUOTE = dict(
    topic='Quote Creation',
    ws_context='WS5 Contract Management \u2014 Quote sub-process',
    sources=['WS5-01_Quote_Creation.bpmn', 'Detailed_Requirements.md'],
    phases=[('1. Quote', [
        ('inscope', 'Start_QuoteRequested', 'FR_Q01', 'Quote raised from an opportunity',
         'A sales user starts a quote.'),
        ('gap', 'Task_ValidateQuote', 'FR_Q12', 'Validate the quote',
         'No failure path when validation rejects the quote. <strong>See BPM-01.</strong>')])],
    rows=[
        _row('SAP-01', 'SAP condition type for the rebate credit is undefined',
             '<code>FR_Q12</code> asks for a rebate credit on the quote but names no SAP condition type or document '
             'type, so the pricing payload cannot be built.',
             'The vendor cannot start the pricing integration until the SAP team names the condition type.',
             'critical', 'ws5'),
        _row('CTR-01', 'Account volume contradicts the RFP',
             'RFP \u00a73 sizes the platform for 1,200 customer accounts; <code>NFR-P02</code> sizes it for 200.',
             'Quote and settlement capacity are priced on different volumes.',
             'high', 'ws5'),
        _row('BPM-01', 'Quote validation has no failure path',
             '<code>Task_ValidateQuote</code> has a single outgoing flow, so a rejected quote has nowhere to go '
             '(<code>FR_Q12</code>).',
             'A rejected quote silently stalls.',
             'medium', 'ws5'),
    ],
    confirmed=['Quote raised from an opportunity (FR_Q01)'],
    implied=['Account volume mismatch (CTR-01)'],
    gap=['SAP condition type undefined (SAP-01)', 'Quote validation failure path (BPM-01)'],
)

SETTLEMENT = dict(
    topic='Rebate Settlement',
    ws_context='WS6 Rebate Accounting \u2014 Settlement',
    sources=['WS6-02_Settlement.bpmn', 'Detailed_Requirements.md'],
    phases=[('1. Settlement', [
        ('inscope', 'Task_CalcSettlement', 'FR_M20', 'Calculate rebate settlement',
         'Period-end calculation per customer.'),
        ('implied', 'Task_PostCreditNote', 'FR_M24', 'Post credit note',
         'FR_M24 says credit memo. <strong>See AMB-01.</strong>')])],
    rows=[
        _row('CTR-01', 'Settlement run sizing contradicts the RFP',
             'RFP \u00a73.1 sizes a settlement run at 1,200 customer accounts; <code>NFR-P02</code> allows 4 hours for '
             '200 accounts, a 6\u00d7 difference.',
             'The run window cannot be committed to until one volume is agreed.',
             'critical', 'ws6'),
        _row('G-01', 'Owner of the accrual reversal at settlement is unclear',
             'Neither <code>FR_M20</code> nor <code>FR_M25</code> says whether the platform or the ERP reverses the '
             'accrual when a settlement posts.',
             'Both sides could book the reversal, or neither.',
             'high', 'ws6'),
        _row('AMB-01', 'Credit memo vs credit note',
             '<code>FR_M24</code> says "credit memo"; RFP \u00a73.1 says "credit note". The glossary lists no synonym.',
             'If these are two documents the posting logic differs.',
             'medium', 'ws6'),
    ],
    confirmed=['Settlement calculation (FR_M20)'],
    implied=['Settlement run sizing mismatch (CTR-01)', 'Credit memo vs credit note (AMB-01)'],
    gap=['Accrual reversal owner (G-01)'],
)

RETENTION = dict(
    topic='Retention',
    ws_context='Regulatory and commercial scope',
    sources=['Retention_Notes.md', 'Detailed_Requirements.md'],
    phases=[('1. Retention', [
        ('gap', 'Task_ArchiveSettlement', 'NFR-A01', 'Archive settlement records',
         'No retention period for statements. <strong>See REG-01.</strong>')])],
    rows=[
        _row('REG-01', 'Retention period for settlement statements is unspecified',
             '<code>NFR-A01</code> keeps the audit trail for 7 years but says nothing about settlement statements.',
             'A statutory retention period may apply and the platform would delete too early.',
             'high', 'reg'),
        _row('COM-01', 'Price master changes are priced but out of scope',
             'The RFP prices price-master maintenance in release 1 but <code>FR_M20</code> to <code>FR_M28</code> '
             'exclude it.',
             'The bid prices work the requirements do not describe.',
             'medium', 'comm'),
        _row('G-02', 'Finance user role mapping',
             'Raised earlier: which finance users may see settlements (<code>FR_M22</code>). The customer has '
             'since answered.',
             'Closed; kept for the record.',
             'resolved', 'ws1'),
    ],
    confirmed=['Finance role mapping answered (FR_M22)'],
    implied=[],
    gap=['Retention period for settlement statements (REG-01)', 'Price master scope (COM-01)'],
)

REGISTER_REPORTS = {'quote-creation': QUOTE, 'rebate-settlement': SETTLEMENT, 'retention': RETENTION}

# ---- the master register ----

CATEGORIES = [
    ('SAP Integration \u2014 Payload Design Blockers', 'Vendor cannot build the API calls until the SAP team answers'),
    ('WS6 Rebate Accounting \u2014 Unresolved Integration Boundaries', 'Handoff points and payload design'),
    ('Workflow \u2014 Configuration Risk &amp; BPMN Modelling Defects', 'Go-live configuration risk and BPMN defects'),
    ('Architecture \u2014 Confirmed Assumptions, Contradictions &amp; Integration Gaps', 'Architecture and integration'),
    ('Requirements Coverage \u2014 Contradictions, Missing FRs &amp; Ambiguities', 'Contradicted, absent or vague FRs'),
    ('Commercial \u2014 Price Master / PCA / SAP', 'Pricing workstream commercial gaps'),
    ('Regulatory &amp; Compliance', 'Retention, signature and audit duties'),
]
OWNER_LABEL = {'owner-cust-sap': 'SAP Team', 'owner-cust-biz': 'Finance / Business', 'owner-vendor': 'Vendor',
               'owner-cust-it': 'IT / Digital', 'owner-shared': 'Customer / Vendor', 'owner-legal': 'Legal / Regulatory'}
FILTERS = [('all', 'All'), ('critical', 'Critical'), ('high', 'High'), ('medium', 'Medium'),
           ('open', 'Open Decision'), ('resolved', 'Resolved / Low'), ('ws6', 'WS6 Accounting'),
           ('ws5', 'WS5 Pricing'), ('ws1', 'WS1/WS2 Workflow'), ('arch', 'Architecture'),
           ('cross', 'Contradictions'), ('reg', 'Regulatory'), ('comm', 'Commercial')]


def register_html(date, links, rows):
    """rows: dicts with cat (1-7), id, title, detail, why, sev, ws, owner. Tiles are computed from them."""
    tally = {'critical': [], 'high': [], 'medium': [], 'open': [], 'resolved': []}
    for r in rows:
        tally['resolved' if r['sev'] in ('low', 'resolved') else r['sev']].append(r['id'])
    labels = [('critical', 'Critical'), ('high', 'High'), ('medium', 'Medium'), ('open', 'Open Decision'),
              ('resolved', 'Resolved / Low')]
    tiles = '\n'.join(f'''  <div class="score-tile tile-{k}">
    <div class="score-label">{lab}</div>
    <div class="score-count">{len(tally[k])}</div>
    <div class="score-ids">{DOT.join(tally[k])}</div>
  </div>''' for k, lab in labels)
    anchors = '\n'.join(f'  <a href="{h}">{t}</a>' for h, t in links)
    buttons = '\n'.join(
        f'  <button class="filter-btn{" active" if k == "all" else ""}" onclick="filterRows(\'{k}\')">{t}</button>'
        for k, t in FILTERS)
    cats = []
    for n, (title, desc) in enumerate(CATEGORIES, 1):
        body = []
        for r in sorted((r for r in rows if r['cat'] == n), key=lambda r: (jc.SEV_RANK[r['sev']], r['id'])):
            cls = ' class="resolved"' if r['sev'] == 'resolved' else ''
            body.append(f'''    <tr data-sev="{r['sev']}" data-ws="{r['ws']}"{cls}>
      <td class="gap-id">{r['id']}</td>
      <td><span class="gap-title">{esc(r['title'])}</span><div class="gap-detail">{r['detail']}</div></td>
      <td>{esc(r['why'])}</td>
      <td><span class="sev sev-{r['sev']}">{r['sev'].capitalize()}</span></td>
      <td><span class="ws ws-{r['ws']}">{r['ws'].upper()}</span></td>
      <td><span class="owner {r['owner']}">{OWNER_LABEL[r['owner']]}</span></td>
    </tr>''')
        cats.append(f'''<div class="category-header" data-category="cat{n}">
  <div class="category-number">{n}</div>
  <div>
    <div class="category-title">{title}</div>
    <div class="category-desc">{desc}</div>
  </div>
</div>
<table>
  <thead>
    <tr><th>ID</th><th>Gap / Risk</th><th>Why It Matters</th><th>Severity</th><th>Workstream</th><th>Owner</th></tr>
  </thead>
  <tbody>
{chr(10).join(body)}
  </tbody>
</table>''')
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Contoso Rebates \u2014 Master Gap &amp; Risk Register</title>
<style>{CSS_COMMON}{CSS_REGISTER}</style>
</head>
<body>

{TOGGLE}

<h1>Contoso Rebates \u2014 Master Gap &amp; Risk Register</h1>
<p class="subtitle">Contoso Rebates \u00b7 All workstreams \u00b7 Last updated {date} \u00b7 Integrated with full cross-file gap analysis</p>

<div class="scorecard">
{tiles}
</div>

<div class="report-links">
{anchors}
</div>

<div class="filter-bar">
  <span class="filter-label">Filter by:</span>
{buttons}
</div>

{chr(10).join(cats)}

<div style="margin-top:40px;padding-top:24px;border-top:1px solid var(--border);font-size:11px;text-align:center;">
  Contoso Rebates Master Gap &amp; Risk Register \u00b7 All workstreams \u00b7 {date} \u00b7 Integrated with full cross-file gap analysis
</div>

<script>{THEME_JS}{FILTER_JS}</script>

</body>
</html>
'''


def reg_row(cat, id_, title, detail, why, sev, ws, owner):
    return dict(cat=cat, id=id_, title=title, detail=detail, why=why, sev=sev, ws=ws, owner=owner)


# The stale register that predates the retention report and the second report's findings.
STALE_REGISTER_ROWS = [
    reg_row(1, 'SAP-01', 'SAP condition type for the rebate credit is undefined',
            '<code>FR_Q12</code> names no SAP condition type.', 'The pricing payload cannot be built.',
            'critical', 'ws5', 'owner-cust-sap'),
    reg_row(2, 'G-01', 'Owner of the accrual reversal is unclear',
            '<code>FR_M20</code> and <code>FR_M25</code> are silent.', 'Both sides could book the reversal.',
            'medium', 'ws6', 'owner-shared'),
    reg_row(3, 'BPM-01', 'Quote validation has no failure path',
            '<code>Task_ValidateQuote</code> has one outgoing flow.', 'A rejected quote stalls.',
            'medium', 'ws5', 'owner-vendor'),
]
STALE_LINKS = [('quote-creation-gap-analysis.html', 'Quote Creation'),
               ('rebate-settlement-gap-analysis.html', 'Rebate Settlement')]


def stale_register(date=OLD_DATE):
    return register_html(date, STALE_LINKS, STALE_REGISTER_ROWS)


# ---- files on disk ----

def fixture_files():
    out = {}
    base = REPOS / 'update-approval' / GAPDIR
    out[base / 'approval-workflow-gap-analysis.html'] = approval_report()
    out[base / 'gap-register.html'] = stale_register()
    base = REPOS / 'regenerate-register' / GAPDIR
    for slug, spec in REGISTER_REPORTS.items():
        out[base / f'{slug}-gap-analysis.html'] = report_html(date=OLD_DATE, **spec)
    out[base / 'gap-register.html'] = stale_register()
    return out


def approval_constants():
    base = REPOS / 'update-approval' / GAPDIR
    raw = (base / 'approval-workflow-gap-analysis.html').read_text(encoding='utf-8')
    return dict(
        ids=list(jc.row_hashes(raw)),
        row_hashes=jc.row_hashes(raw),
        bullets=jc.box_bullets(jc.parse(raw)),
        remainder=jc.remainder(raw),
        subtitle=jc.subtitle_masked(raw, OLD_DATE, NEW_DATE),
        size=len(raw.encode('utf-8')),
        register_sha=jc.sha((base / 'gap-register.html').read_text(encoding='utf-8')),
    )


def register_constants():
    base = REPOS / 'regenerate-register'
    inputs = {}
    for p in sorted((base / GAPDIR).glob('*-gap-analysis.html')):
        inputs[p.relative_to(base).as_posix()] = jc.sha(p.read_text(encoding='utf-8'))
    glossary = base / 'output/requirement/ubiquitous-language.md'
    inputs[glossary.relative_to(base).as_posix()] = jc.sha(glossary.read_text(encoding='utf-8'))
    return dict(inputs=inputs)


JUDGE_DATA = {
    'judge_update_row.py': approval_constants,
    'judge_mark_resolved.py': approval_constants,
    'judge_register.py': register_constants,
}
COMMON_RE = re.compile(r'# >>> COMMON.*?# <<< COMMON\n', re.S)
DATA_RE = re.compile(r'# >>> FIXTURE DATA.*?# <<< FIXTURE DATA\n', re.S)


def judge_regions(path):
    """The text the judge's COMMON and FIXTURE DATA regions must contain."""
    common = ('# >>> COMMON (pasted from fixtures/judge_common.py by build_fixtures.py; edit it there)\n'
              + (HERE / 'judge_common.py').read_text(encoding='utf-8').rstrip('\n') + '\n# <<< COMMON\n')
    fn = JUDGE_DATA.get(path.name)
    data = ''
    if fn:
        data = ('# >>> FIXTURE DATA (generated by build_fixtures.py)\nFIXTURE = '
                + json.dumps(fn(), indent=1, ensure_ascii=False) + '\n# <<< FIXTURE DATA\n')
    return common, data


def sync_judges(write):
    drift = []
    for path in sorted(SCRIPTS.glob('judge_*.py')):
        text = path.read_text(encoding='utf-8')
        common, data = judge_regions(path)
        new = COMMON_RE.sub(lambda m: common, text)
        if data:
            new = DATA_RE.sub(lambda m: data, new)
        if new != text:
            drift.append(path.name)
            if write:
                path.write_text(new, encoding='utf-8')
    return drift


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else '--check'
    write = mode == '--write'
    if mode not in ('--write', '--check'):
        sys.exit(__doc__)
    drift = []
    for path, content in fixture_files().items():
        if not path.is_file() or path.read_text(encoding='utf-8') != content:
            drift.append(str(path.relative_to(HERE)))
            if write:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding='utf-8')
    if write:                       # constants are computed from the files just written
        drift += sync_judges(True)
    else:
        drift += sync_judges(False)
    if drift:
        print(('updated: ' if write else 'DRIFT: ') + ', '.join(drift))
        sys.exit(0 if write else 1)
    print('ok: fixtures and judge regions are in sync')


if __name__ == '__main__':
    main()
