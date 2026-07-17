# Individual Gap Analysis Report — Anatomy

Read after `conventions.md`. This describes the section-by-section structure of a single gap-analysis HTML file. The template in `assets/individual-report.template.html` already contains the theme system, the theme toggle, and the JS — you fill in only the marked content sections.

The four reports that follow this layout cleanly are:

- `quote-creation-gap-analysis.html`
- `approval-workflow-gap-analysis.html`
- `requirements-coverage-gap-analysis.html`
- (and the master `gap-register.html` — see `register.md`)

Match their structure when generating new reports. The older three (`accounting-gap-analysis.html`, `rebate-accounting-gap-analysis.html`, `sap-integration-gapanalysis.html`) pre-date the theme system and should not be used as the structural reference, though their content is still valid.

---

## Section 1 — Header

```html
<h1><Project> — <Topic> Gap Analysis</h1>
<p class="subtitle">
  <Workstream context> · Source: <code>...</code> vs <code>...</code> · <Date>
</p>
```

- **H1**: always `<Project> — <Topic> Gap Analysis`. `<Project>` is the engagement / product name — take it from the source docs or the user, and drop the `<Project> — ` prefix entirely if there is no obvious project name. Topic should match the slug in the filename (Title Case, no slashes).
- **Subtitle**: name the workstream (e.g. "WS4 Internal Approval Workflows", "WS5 Contract Management — Quote sub-process"), the source files compared (BPMN file path, requirements doc, RFP), and today's date.

The theme toggle is rendered before the H1 by the template. Don't move it.

---

## Section 2 — Legend

Five-item legend mapping card colours to meanings. Keep it identical across reports unless you genuinely added a new card type:

```html
<div class="legend">
  <div class="legend-item"><div class="legend-dot dot-inscope"></div> In-scope activity (FR-mapped)</div>
  <div class="legend-item"><div class="legend-dot dot-external"></div> External system (SFDC / SAP / ADL / JDH)</div>
  <div class="legend-item"><div class="legend-dot dot-actor"></div> Out-of-system actor (Customer / Dealer)</div>
  <div class="legend-item"><div class="legend-dot dot-implied"></div> Implied / inconsistent with requirements</div>
  <div class="legend-item"><div class="legend-dot dot-gap"></div> Gap — missing or under-specified</div>
</div>
```

If the report has no BPMN flow section (rare — really only when comparing two pure-text specs), drop the legend entirely.

---

## Section 3 — Phase flow (the big visual)

This is the BPMN-aligned, left-labelled, card-grid section. Each phase row is a `<div class="phase-row">` with a `<div class="phase-label">` on the left and a `<div class="phase-content">` on the right. Cards inside `.phase-content` are connected by `<div class="flow-arrow">→</div>` text arrows.

Between phases, a `.phase-arrow` element with an explanatory line.

```html
<div class="phase-row">
  <div class="phase-label">1. Initiation</div>
  <div class="phase-content">
    <div class="card card-actor">
      <div class="card-bpmn">Start_WS3B_SR (start event)</div>
      <div class="card-fr">FR_S01 · FR_Q01</div>
      <div class="card-title">SR initiates quote from SFDC Opportunity</div>
      <div class="card-desc">...</div>
      <span class="card-badge badge-actor">Documented</span>
    </div>
    <div class="flow-arrow">→</div>
    <div class="card card-inscope">...</div>
    <div class="flow-arrow">→</div>
    <div class="card card-implied">...
      <span class="card-badge badge-implied">Inconsistent with FR_Q02</span>
    </div>
  </div>
</div>

<div class="phase-arrow">
  <div class="phase-arrow-left"></div>
  <div class="phase-arrow-right">
    <div class="arrow-line">→ Validate prerequisite master data before deal-entry screen renders</div>
  </div>
</div>
```

Guidelines:

- **One row per BPMN phase.** Use the BPMN's natural phase boundaries, not arbitrary slicing.
- **Phase label is short** — 2–3 words, allow line breaks (`<br>`) for readability.
- **Branches** (e.g. 3A / 3B / 3C in quote creation) get their own row with `class="phase-label branch-a"` etc., colour-coded.
- **Cards stay narrow.** Don't stretch a card to fit a long description — break the description into multiple cards or add a `phase-arrow` annotation.
- **Card badges are optional** but help for `card-implied` (`badge-implied`) and `card-gap` (`badge-gap`) — they reinforce that the card needs attention.
- **Embed gap IDs** in card descriptions when relevant: `<strong>… — see G-04.</strong>`. The reader should be able to scroll down to the gap table and find the row.

---

## Section 4 — Gap register (the table)

The single most-read section. Format:

```html
<div class="gap-table-section">
  <h2>Gap Register — BPMN vs. RFP / Detailed Requirements</h2>
  <p class="section-intro">
    Severity classification: <strong>Critical</strong> = blocks bid scoping or implementation; ...
    Every gap should be added to <code>open-questions.md</code> for BSC clarification, grouped by the workstream pill shown on the right.
  </p>
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
      <tr>
        <td>G-01</td>
        <td><strong>Short title</strong><br>One-paragraph description with FR/RFP citations in <code>...</code>.</td>
        <td>Why-it-matters sentence framed for bid team or BSC.</td>
        <td class="sev-critical">Critical</td>
        <td><span class="pill pill-ws5">WS5</span><span class="pill pill-arch">ARCH</span></td>
      </tr>
      ...
    </tbody>
  </table>
</div>
```

Rules:

- **Severity is text + class** (`<td class="sev-critical">Critical</td>`), not a badge in this view. Badges are reserved for the master register.
- **Pills go in the workstream column.** Use multiple pills when a row truly straddles workstreams; single pill is the default.
- **Order rows by severity, then by gap ID** — Critical first, then High, then Medium, then Low. Within a severity, ascending ID.
- **Don't add an Owner column here.** The individual report assumes the workstream pill implies the owner; the master register adds the owner column for cross-WS visibility.

---

## Section 5 — Architecture summary (3 boxes)

Three side-by-side `arch-box` cards summarising the gap landscape:

- **`box-confirmed`** — "✓ BPMN ↔ Requirements Aligned" — bullet list of FRs that are correctly modelled.
- **`box-implied`** — "~ Implied / Inconsistent" — bullets pointing at `card-implied` items, each tagged with the gap ID.
- **`box-gap`** — "✗ Missing — Must Be Raised" — bullets pointing at `card-gap` items, each tagged with the gap ID.

```html
<div class="arch-row">
  <div class="arch-box box-confirmed">
    <h3>✓ BPMN ↔ Requirements Aligned</h3>
    <ul>
      <li>SFDC Opportunity entry (FR_S01 · FR_Q01)</li>
      ...
    </ul>
  </div>
  <div class="arch-box box-implied">
    <h3>~ Implied / Inconsistent</h3>
    <ul>
      <li>JDH-mediated SFDC pull (G-02)</li>
      ...
    </ul>
  </div>
  <div class="arch-box box-gap">
    <h3>✗ Missing — Must Be Raised</h3>
    <ul>
      <li>BSC360 mandatory Pricing Council injection (G-04)</li>
      ...
    </ul>
  </div>
</div>
```

The architecture summary is what the bid lead will skim first. Make every bullet copy-pasteable into a Q&A item.

---

## Section 6 — Reading notes (optional)

A final `gap-table-section` titled "Reading Notes — How This Maps to the BPMN" with three or four small info boxes (quote types, lifecycle states, cross-workstream boundaries, BPMN ID conventions). Useful when the report will be shared with non-BPMN readers — drop the section if the audience is purely the bid team.

---

## Section 7 — Footer (optional)

The template provides a lightweight footer line. Keep it minimal — date, file family, pointer to the master register.

---

## Filename and location

```
<gap-analysis-folder>/<topic-slug>-gap-analysis.html
```

- `<gap-analysis-folder>` is the path the user supplied at invocation time — never hardcode (see SKILL.md → Required inputs).
- `<topic-slug>` is kebab-case; no spaces, no underscores.
- If you encounter a legacy filename in the supplied folder that is missing a hyphen (e.g. `sap-integration-gapanalysis.html` rather than `sap-integration-gap-analysis.html`), do not perpetuate that typo for new reports — use the hyphenated form going forward, but do not rename the existing file unless explicitly asked (it may be referenced from `gap-register.html`'s footer and from companion deliverables).

---

## Updating an existing report

This is Flow A2's reference section. SKILL.md has the step-by-step procedure; this section gives you the anatomy detail.

### What "update" usually means

Roughly half of all gap-analysis work is updates rather than fresh reports. The common sub-cases:

- **Add one new finding** (new row + new arch-box bullet). Most common.
- **Update severity** of an existing row (row class change + arch-box bullet may move boxes).
- **Mark resolved** (row gets `sev-resolved` + `class="resolved"` on `<tr>`; arch-box bullet moves to `box-confirmed` or is dropped).
- **Refresh date only** (no row changes, just the subtitle).

The common failure mode is updating only one of the two views — the table OR the arch box, not both. Per `conventions.md` §8 the two are coupled; treat them as a single edit.

### Anatomy rules for updates

1. **Read the existing HTML in full** before editing — it's the source of truth for current gap IDs and the existing severity-sort order. Do *not* re-read the source RFP / BPMN unless the new finding cites a fact you cannot verify from the prompt or the existing report.
2. **Preserve every existing gap ID.** New gaps go at the end of their severity tier with the next available number for that prefix.
3. **Pick the prefix from `conventions.md` §2's decision tree** — `G-` is the default fallback, not the first choice. A "BPMN modelling gap" belongs under `BPM-`, not `G-`.
4. **Mirror the row in the arch box** in the same edit. New gap → bullet in `box-gap`. New inconsistency → bullet in `box-implied`. Newly verified item → bullet in `box-confirmed`. Bullet format: `<li>Short title (BPM-04)</li>`.
5. **Mark superseded rows resolved** — change the severity to `<td class="sev-resolved">Resolved</td>` and apply `class="resolved"` to the `<tr>` to fade it. Leave the row in place; deletions break references in `open-questions.md` and the master register.
6. **Update the date** in the subtitle.
7. **Don't refactor adjacent prose, don't re-derive the full bullet lists from scratch, don't touch the legend or theme JS.** Surgical changes only — every extra change is something the reviewer has to verify is intentional.

### Worked example — adding one row

User: *"Add a High-severity BPMN modelling gap to the approval-workflow report: WS4 BPMN files have no error-handling sub-processes for SAP integration calls via JARVIS, referenced in FR_W08."*

Steps:

1. Read `<gap-analysis-folder>/approval-workflow-gap-analysis.html` (using the gap-analysis folder path the user supplied at invocation time).
2. Pick prefix → "BPMN modelling gap" → `BPM-`. Scan existing rows for highest `BPM-NN` → next is `BPM-04` (or the first if none exists).
3. Find the gap-register `<tbody>`. The last existing High-severity row is at line N; insert immediately after it:

   ```html
   <tr>
     <td>BPM-04</td>
     <td><strong>No error-handling sub-processes for JARVIS-mediated SAP calls</strong><br>WS4-01 / WS4-02 / WS4-03 BPMN files do not model boundary error events, compensation handlers, or retry/timeout flows for SAP integration calls routed via JARVIS (<code>FR_W08</code>). Failure paths (JARVIS unavailable, SAP timeout, partial response) are unspecified.</td>
     <td>Without explicit error-handling, an SAP-side failure during approval routing leaves the approval task in an undefined state. The integration contract with JARVIS must specify retries, dead-letter queues, and compensating actions before WS4 build can start.</td>
     <td class="sev-high">High</td>
     <td><span class="pill pill-ws4">WS4</span></td>
   </tr>
   ```

4. Find the `arch-box box-gap` `<ul>` and add: `<li>JARVIS error-handling sub-processes for SAP calls (BPM-04)</li>`.
5. Bump the subtitle date.
6. Save. Done.

Note the explicit choices: `pill pill-ws4` (not `ws ws-ws4` — that's register form), `BPM-` prefix (not `G-`), bare-class severity cell (not the badge form). All three rules live in `conventions.md`; double-check there if uncertain.
