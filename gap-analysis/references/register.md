# Master Gap & Risk Register — Anatomy

Read after `conventions.md`. The master register is `<gap-analysis-folder>/gap-register.html` (the path the user supplied — see SKILL.md → Required inputs; never hardcode). It is a roll-up of every individual report, re-organised by category rather than by source file. The template `assets/register.template.html` already contains the theme system, the scorecard skeleton, the report-links row, the filter bar, and the JS — you fill in the scorecard counts, the report-links anchors, the category headers, and the category tables.

---

## Section 1 — Header

```html
<h1><Project> — Master Gap &amp; Risk Register</h1>
<p class="subtitle"><Project> · BSC APAC Japan Wave 1 · All workstreams · Last updated <Date> · Integrated with full cross-file gap analysis</p>
```

`<Project>` is the engagement / product name — take it from the individual reports or the user, and drop the `<Project> — ` / `<Project> · ` prefix if there is no obvious project name. Keep the title and the "All workstreams" framing. The subtitle is the only line that changes per refresh — bump the date and (if applicable) update the closing clause.

---

## Section 2 — Scorecard (5 tiles)

Five tiles across the top, in this exact order:

1. **Critical** (`tile-critical`) — count + ID list
2. **High** (`tile-high`) — count + ID list
3. **Medium** (`tile-medium`) — count + ID list
4. **Open Decision** (`tile-open`) — count + ID list (the `D-` prefix lives almost exclusively here)
5. **Resolved / Low** (`tile-resolved`) — count + ID list, faded

Each tile:

```html
<div class="score-tile tile-critical">
  <div class="score-label">Critical</div>
  <div class="score-count">22</div>
  <div class="score-ids">R-01–R-04 · G-01–G-03 · G-11<br>...</div>
</div>
```

The IDs in `score-ids` should be condensed (`R-01–R-04` rather than `R-01 · R-02 · R-03 · R-04`) to keep the tile readable. Wrap onto multiple lines with `<br>` once the line gets long.

The total across all five tiles must equal the total rows in all category tables. If they don't match, you missed a row when re-counting.

---

## Section 2b — Report links

A row of pill-shaped quick links to the individual reports, sitting between the scorecard and the filter bar. The template ships with the `.report-links` CSS rule and a placeholder `<div class="report-links">` block; replace its example anchors with one `<a href="<slug>-gap-analysis.html">` per report discovered in the refresh procedure (excluding `gap-register.html` itself). Link text is the human-readable topic name — drop the `-gap-analysis` suffix and title-case the slug (e.g. `quote-creation-gap-analysis.html` → "Quote Creation").

```html
<div class="report-links">
  <a href="quote-creation-gap-analysis.html">Quote Creation</a>
  <a href="approval-workflow-gap-analysis.html">Approval Workflow</a>
  <!-- … one anchor per individual report in <gap-analysis-folder> … -->
</div>
```

Order anchors to match the category ordering below where practical — the reader scans the report-links row first to jump into a specific report, then the categories to see the rolled-up findings.

---

## Section 3 — Filter bar

The filter bar is rendered as-is by the template and wired to `filterRows()` in the page JS. It looks like:

```html
<div class="filter-bar">
  <span class="filter-label">Filter by:</span>
  <button class="filter-btn active" onclick="filterRows('all')">All</button>
  <button class="filter-btn" onclick="filterRows('critical')">Critical</button>
  ...
  <button class="filter-btn" onclick="filterRows('ws6')">WS6 Accounting</button>
  <button class="filter-btn" onclick="filterRows('reg')">Regulatory</button>
  <button class="filter-btn" onclick="filterRows('comm')">Commercial</button>
</div>
```

Don't add or rename buttons casually — `filterRows()` matches by literal string. If you genuinely need a new filter (e.g. you create a new workstream), update both the button HTML and the `filterRows` JS together.

The corresponding `data-sev` and `data-ws` attributes on each `<tr>` must match the filter strings (`critical`, `high`, `medium`, `open`, `resolved`, `ws1`–`ws6`, `arch`, `cross`, `reg`, `comm`).

---

## Section 4 — Categories

The register groups gaps into seven canonical categories. Don't invent new ones unless the existing seven genuinely don't fit.

| # | Title                                                              | Number colour       | Typical content |
|---|--------------------------------------------------------------------|---------------------|-----------------|
| 1 | SAP Integration — Payload Design Blockers                          | indigo (`#6366f1`)  | `SAP-` prefixes (and legacy `R-` IDs preserved from earlier reports), plus any `AMB-`/`GAP-` rows that block VK11 / VA01 development. |
| 2 | WS6 Rebate Accounting — Unresolved Integration Boundaries          | violet (`#a855f7`)  | `G-` and `CTR-` rows about accrual postings, credit notes, settlement. |
| 3 | Workflow — Configuration Risk & BPMN Modelling Defects             | green (`#22c55e`)   | `W-` (governance) + `BPM-` (modelling defects) rows. |
| 4 | Architecture — Confirmed Assumptions, Contradictions & Integration Gaps | pink (`#ec4899`) | `A-`, `CTR-`, `MFR-`, `INT-` rows about JARVIS / ADL / Snowflake / integration topology. |
| 5 | Requirements Coverage — Contradictions, Missing FRs & Ambiguities  | sky (`#0ea5e9`)     | `CTR-`, `AMB-`, `MFR-` rows that are not specifically WS6 or architecture. |
| 6 | Commercial — Price Master / PCA / SAP                              | amber (`#f59e0b`)   | `COM-` rows. |
| 7 | Regulatory & Compliance                                            | purple (`#a855f7`)  | `REG-` rows (APPI, J-SOX, NHI, PMDA, FSA, retention). |

Category header markup:

```html
<div class="category-header" data-category="cat1">
  <div class="category-number" style="background:#6366f120;color:#a5b4fc;">1</div>
  <div>
    <div class="category-title">SAP Integration — Payload Design Blockers</div>
    <div class="category-desc">Vendor cannot build the API calls without BSC SAP team answering these first</div>
  </div>
</div>
```

The `category-number` background is the colour at 12% alpha; the text is a lighter tint of the same hue. The pairs already used:

- `#6366f120` / `#a5b4fc` — indigo
- `#6366f120` / `#c4b5fd` — violet (slightly different text for variety)
- `#22c55e20` / `#86efac` — green
- `#ec489920` / `#fda4af` — pink
- `#0ea5e920` / `#7dd3fc` — sky
- `#f59e0b20` / `#fbbf24` — amber
- `#a855f720` / `#d8b4fe` — purple

---

## Section 5 — Category tables

Each category gets its own table with this header:

```html
<table>
  <thead>
    <tr>
      <th>ID</th>
      <th>Gap / Risk</th>
      <th>Why Critical</th>
      <th>Severity</th>
      <th>Workstream</th>
      <th>Owner</th>
    </tr>
  </thead>
  <tbody>
    <tr data-sev="critical" data-ws="ws6">
      <td class="gap-id">SAP-01</td>
      <td>
        <span class="gap-title">Short title</span>
        <div class="gap-detail">One-paragraph description with citations in <code>...</code>.</div>
      </td>
      <td>Why-it-matters sentence.</td>
      <td><span class="sev sev-critical">Critical</span></td>
      <td><span class="ws ws-ws6">WS6</span></td>
      <td><span class="owner owner-bsc-sap">BSC SAP Team</span></td>
    </tr>
    ...
  </tbody>
</table>
```

Critical rules:

- **`data-sev` and `data-ws` on every `<tr>`** — required for the filter JS. Allowed `data-sev` values: `critical`, `high`, `medium`, `low`, `open`, `resolved`. Allowed `data-ws` values match the filter buttons.
- **Severity column uses badge form** (`<span class="sev sev-critical">Critical</span>`), not the bare `class="sev-critical"` cell used in individual reports. This is a deliberate visual distinction.
- **Owner column is mandatory** in the register and absent from individual reports.
- **Resolved rows** carry `class="resolved"` on the `<tr>` for fading: `<tr data-sev="resolved" data-ws="ws6" class="resolved">`. Keep them — they are evidence the team has been actively closing gaps.

Sort order within a category: `data-sev` Critical → High → Medium → Low → Resolved, then ascending ID within each severity.

---

## Section 6 — Footer

```html
<div style="margin-top:40px;padding-top:24px;border-top:1px solid var(--border);font-size:11px;color:var(--text-footer);text-align:center;">
  <Project> Master Gap &amp; Risk Register · All workstreams · <Date> · Integrated with full cross-file gap analysis<br/>
  For detailed WS6 accounting analysis see <strong>accounting_gap_analysis.html</strong> · For full findings narrative see <strong>full_gap_analysis.html</strong>
</div>
```

Update the date and, if companion files were renamed, the pointers. The two filenames in the existing footer use underscores — that's a stale artefact from before the kebab-case convention. Leave them untouched unless the user explicitly asks to fix the footer; some downstream documents reference those exact strings.

---

## Refresh procedure

Every time `gap-register.html` is regenerated:

1. **List inputs**: every `*.html` in `<gap-analysis-folder>` except `gap-register.html` itself.
2. **Extract every gap row** from each file (look for the `Gap Register — ...` table and its `<tbody>`).
3. **Map each row into one of the seven categories.** Rows that legitimately belong in two categories (e.g. an `AMB-` ambiguity that blocks SAP integration) go into the *upstream* category — i.e. category 1 wins over category 5 because the SAP integration blocker is the more actionable framing.
4. **Dedupe**: where two source files describe the same underlying issue, keep the higher-severity citation and merge the descriptions. Note both source files in the `gap-detail`.
5. **Recount the scorecard.** The total across the five tiles must equal the count of `<tr>` rows in all category tables.
6. **Re-derive the ID lists** in each scorecard tile. Use compressed ranges (`R-01–R-04`) where contiguous.

When the user asks to *also* refresh the master after generating an individual report, run this procedure once at the end rather than after each report.
