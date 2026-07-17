---
name: gap-analysis
description: Use when producing or updating a gap-analysis HTML report. Triggers on "gap analysis", "gap register", "gap index", "analyse the requirement docs", "find gaps between BPMN and requirements", or when the user references requirement / BPMN / FeatureSpec / RFP docs and asks for a structured comparison. Also triggers when the user points at a folder of existing gap-analysis reports and asks to refresh, re-roll up, or rebuild the master register/index. Produces a self-contained, theme-switching HTML report in the gap-analysis house style. Use this skill instead of free-form Markdown when the user wants a sharable HTML deliverable; do not use for prose summaries or open-question lists.
metadata:
  version: 1.1.0
---

# Gap Analysis

This skill produces two related deliverables that live in the project's **gap-analysis folder** (referred to as `<gap-analysis-folder>` throughout — the actual path is project-specific and supplied by the user; see "Required inputs" below):

1. **Individual gap-analysis reports** — one HTML file per workflow / component / system, comparing a BPMN (or set of requirement docs) to the RFP and Detailed Requirements, listing gaps with severity, workstream, and remediation owner.
2. **The master gap & risk register** (`gap-register.html`) — a roll-up index that re-tabulates every gap from every individual report, grouped by category, with a scorecard and filter bar.

Both deliverables share the same theme system, severity rubric, workstream pills, and owner pills. Pick the right flow based on the user's intent:

```
User asks for a fresh gap analysis on a specific workflow / component
+ no existing report at <gap-analysis-folder>/<topic>-gap-analysis.html
        │
        ▼
   Flow A — Fresh individual report
        │
        ├──→ assets/individual-report.template.html
        └──→ references/individual-report.md

User asks to update / add to / refresh an existing individual report
(usually points at <gap-analysis-folder>/<topic>-gap-analysis.html)
        │
        ▼
   Flow A2 — Update existing report
        │
        └──→ references/individual-report.md (§ Updating an existing report)

User points at gap-analysis folder, OR mentions "register" / "index"
+ wants the master rollup refreshed
        │
        ▼
   Flow B — Master register
        │
        ├──→ assets/register.template.html
        └──→ references/register.md
```

If the user asks to "do gap analysis" without specifying which, ask once before generating. If the user names a specific topic, check whether `<gap-analysis-folder>/<topic>-gap-analysis.html` already exists — if it does, default to Flow A2 (update) rather than Flow A (fresh).

---

## Required inputs

Two things are project-specific and cannot be embedded — they must come from the user at invocation time. **Ask once at the start of any flow for whichever is missing; confirm the path explicitly rather than guessing or inferring it from a filename in the prompt.**

1. **`<gap-analysis-folder>`** — where reports live. This document uses the token `<gap-analysis-folder>` throughout; substitute the path the user gives. Engagements lay out `output/` differently (`output/requirement/gap-analysis/`, `output/gap-analysis/`, `docs/gap-analysis/`, …), so a wrong path silently writes into the wrong place or fails to find existing reports on a register refresh. Ask: "What's the project's gap-analysis output folder — the one that holds (or will hold) the `*-gap-analysis.html` files and `gap-register.html`?"

2. **Glossary / ubiquitous-language file** — the terminology source of truth. Every engagement uses different terms, acronyms, and cross-document synonyms, so a hardcoded path produces wrong analysis on a new project. It may live anywhere (`output/requirement/ubiquitous-language.md`, `docs/glossary.md`, embedded in a README, …). Ask: "Where's the glossary / ubiquitous-language file — the one listing canonical terms and known synonyms?" Read it in full before drafting any row whose verdict turns on a term (including every `AMB-` decision). `conventions.md` §6 is the source of truth for glossary discipline.

If the user genuinely has no glossary: proceed, default every terminology mismatch to `AMB-`, and note up-front in the report intro — "No glossary supplied — terminology variants flagged conservatively; reconcile against a glossary before circulating widely."

---

## Shared conventions

The reference file **`references/conventions.md`** is the source of truth for severity rubric, gap-ID prefixes, pill class forms, owner pills, card types, glossary discipline, provenance rules, and the row ↔ arch-box coupling rule. Read the sections relevant to your flow — don't read what you won't use:

| Flow | Sections to read first |
|------|------------------------|
| A — Fresh report | §1 severity · §2 prefixes · §3 pills · §4 owners · §5 cards · §6 glossary · §7 provenance · §8 coupling |
| A2 — Update existing report | §2 prefixes (decision tree only) · §3 pills (table + filename rule) · §8 coupling. Skip §5 cards unless you're adding a new phase-flow card. |
| B — Master register | §1 severity · §2 prefixes · §3 pills · §4 owners · §6 glossary · §7 provenance |

The legacy `R-` IDs preserved in some earlier reports are never renumbered; new SAP-integration payload blockers use `SAP-`.

Two cross-cutting rules from this workspace's `CLAUDE.md` apply to all flows, but the *form* differs by deliverable:

- **Provenance.** In HTML reports (this skill), provenance lives inline in the gap row itself: the FR / RFP / BPMN citation goes in the *Gap* column wrapped in `<code>...</code>`, and the *Why It Matters* sentence frames why the citation matters for the bid. Do **not** insert Markdown blockquotes (`> **RFP source reference:** ...`) into HTML — those are the convention for the workspace's Markdown deliverables (e.g. `rfp-2026.md`) and look out-of-place in the gap-analysis house style.
- **Inconsistencies.** Surface contradictions between source documents rather than papering over them. Where documents disagree on a term, preserve both variants verbatim and tag the row `AMB-` rather than silently picking one — see `conventions.md` §6 for the full glossary discipline.

---

## Flow A — Fresh individual gap analysis report

Use when the user asks to gap-analyse a specific workflow, component, sub-system, or BPMN file *and* no report already exists for that topic. Examples:

- "Analyse `WS5-01_Quote Creation.bpmn` against the detailed requirements and create a gap analysis report."
- "Compare `RFP.md` and `Detailed_Requirements_FINAL.md` for the standard approval workflow and produce a gap analysis."

If a report on this topic *already* exists in `<gap-analysis-folder>` (e.g. the user is asking to re-run on a topic that's been done before), switch to Flow A2 — preserving existing gap IDs and the historical record matters more than starting clean.

### Steps

1. **Locate inputs.** Read every requirement / BPMN / FeatureSpec / RFP document the user named, plus the glossary file the user supplied (see "Required inputs" above; ask if absent). Convert binaries (`.docx`, `.xlsx`) per the project's conversion conventions before reading.
2. **Pick a slug** for the filename: `<topic>-gap-analysis.html`, kebab-case, no spaces. New file lives in `<gap-analysis-folder>` (the path the user supplied — see "Required inputs" above; ask if absent).
3. **Copy** `assets/individual-report.template.html` to the output path. The template is self-contained — theme CSS, theme toggle, and the JS block are ready as-is. Do not strip them.
4. **Customise** the title, subtitle (source files + date), legend, phase rows, gap-register table, architecture summary, and reading notes. See `references/individual-report.md` for the full section anatomy and what each card type / badge means.
5. **Mirror every row to the arch boxes.** Per `conventions.md` §8: every row in the gap-register table also needs a matching bullet in `box-gap` / `box-implied` / `box-confirmed`. Don't save until both views are in sync.
6. **Re-roll up.** After saving, offer to run Flow B to refresh `gap-register.html` so the master index reflects the new findings.

---

## Flow A2 — Update existing individual report

Use when the user names a specific existing report and asks to add a finding, change severity, mark a gap resolved, or refresh the date. Examples:

- "Update the approval-workflow gap analysis with one new High-severity row about JARVIS error-handling."
- "Mark G-04 in the quote-creation gap analysis as resolved — the FX-rate question was answered."
- "Refresh the rebate-accounting report date to today."

This flow is deliberately narrow. Do *not* re-read the full RFP / BPMN source unless the new finding asserts a fact you cannot verify from the user's prompt or the existing report. Treat the existing report as authoritative for everything else.

### Steps

1. **Read the existing HTML report only.** Do not pull source documents unless the user's instruction names a specific FR/RFP/BPMN reference you have not seen before and need to verify. If the new finding hinges on terminology (you're flagging an `AMB-` ambiguity, or you're not sure whether two terms are synonyms), also read the glossary file the user supplied.
2. **Locate the change site.** Find the `Gap Register` `<tbody>` and the `arch-row` containing `box-confirmed` / `box-implied` / `box-gap`. These two regions are the entire change surface for most updates.
3. **For a new gap row:**
   - Pick the prefix using the decision tree in `conventions.md` §2 (BPMN modelling defect → `BPM-`, missing FR → `MFR-`, two-doc contradiction → `CTR-`, etc. — `G-` is the default, not the first choice).
   - Pick the next available number for that prefix by scanning the existing rows; never reuse or renumber.
   - Place the row after the last existing row of the same severity (Critical → High → Medium → Low), then by ascending ID within severity.
   - Use the individual-report pill form: `<span class="pill pill-ws4">WS4</span>`, *not* the master-register `ws ws-ws4` form. See `conventions.md` §3.
   - Severity uses the bare-class cell form here: `<td class="sev-high">High</td>` — not the badge form (which is reserved for the master register).
4. **Mirror the row to the matching arch box** (per `conventions.md` §8). Open gaps → `box-gap`. Inconsistencies → `box-implied`. Newly verified items → `box-confirmed`. Bullet format: `<li>Short title (BPM-04)</li>`. Skipping this step is the single most common reason updates fail review.
5. **For severity changes** on an existing row: update both the row's severity class *and* move the matching arch-box bullet if the box-mapping changed (e.g. resolving an open gap → bullet moves from `box-gap` to `box-confirmed`).
6. **For "mark resolved":** change the row to `<td class="sev-resolved">Resolved</td>` and add `class="resolved"` to the `<tr>`. Do not delete the row — the historical record matters. Update the arch box per step 4.
7. **Update the subtitle date** to today (the user usually says so, but do it even when they don't — the date is the audit trail).
8. **Save and stop.** Do not re-write unrelated sections, do not "improve" surrounding prose, do not refactor the legend. Surgical changes only.

After Flow A2, offer to run Flow B if the change was material (new Critical / High row, new prefix family introduced).

---

## Flow B — Master gap & risk register

Use when the user points at the gap-analysis folder, says "regenerate the index", "refresh the register", or otherwise asks for the cross-file rollup.

### Steps

1. **Discover inputs.** List `<gap-analysis-folder>/*.html` (excluding `gap-register.html` itself), where `<gap-analysis-folder>` is the path the user supplied — see "Required inputs" above; ask if absent. Read each report and extract every row from its gap-register table.
2. **Re-categorise.** The register is grouped by *category* (e.g. "SAP Integration — Payload Design Blockers", "WS6 Rebate Accounting", "Workflow Configuration Risk", etc.) — not by source file. Map each gap into the existing category set first; only create a new category when the existing seven do not fit. See `references/register.md` for the canonical category list and category numbering colours.
3. **Promote IDs as needed.** When a gap appears in multiple individual reports, keep one canonical ID and note the cross-references. Where gaps in different reports describe the same underlying issue, dedupe.
4. **Recompute the scorecard.** Count gaps by severity (Critical / High / Medium / Open Decision / Resolved+Low) and list IDs in each tile.
5. **Add per-report quick links.** The template already includes a `<div class="report-links">` block (after the scorecard, before the filter bar) and the matching `.report-links` CSS rule. Replace its example `<a>` tags with one `<a href="<slug>-gap-analysis.html">` per individual report discovered in step 1 (exclude `gap-register.html` itself). Link text is the human-readable topic name (e.g. "Quote Creation", "Approval Workflow", "SAP Integration"). Keep this list in the same order as the categories below where practical.
6. **Copy** `assets/register.template.html` to `<gap-analysis-folder>/gap-register.html` and fill in scorecard, report links (step 5), filter bar, category headers, and category tables. The filter JS is pre-wired — keep the `data-sev` and `data-ws` attributes consistent with the filter buttons.
7. **Footer pointer.** Update the footer's last-updated date and any pointers to companion reports.

---

## What "good" looks like

Both deliverables are bid-support artefacts — clarity for BSC and the bid team is more important than completeness. A good report:

- **Names the contradiction explicitly** ("RFP §5 says 1,200 concurrent users; NFR-P02 says 200 — 6× discrepancy") rather than picking a value.
- **Ties every gap to a source citation** (FR ID, NFR ID, RFP section, BPMN task ID). A gap with no source pointer is a gap the reader cannot verify.
- **Distinguishes blocker from concern** in the *Why It Matters* column. "Vendor cannot start build until BSC answers this" is different from "audit trail is weaker than ideal".
- **Surfaces missing FRs separately** from contradicted FRs (e.g. `MFR-` prefix for "FeatureSpec P0, no FR exists"). The bid team needs both lists for different reasons.
- **Keeps the open-question loop closed.** Every Critical / High gap should have a counterpart in the project's open-questions file (typically a sibling of `<gap-analysis-folder>`, e.g. `<requirement-folder>/open-questions.md`, grouped A–G). Mention this to the user when finishing — and ask for the open-questions file path if you don't already have it.
