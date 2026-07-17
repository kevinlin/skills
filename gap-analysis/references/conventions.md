# Gap Analysis Conventions

Shared rules for both individual reports and the master register. These are the conventions already established across the existing reports in `<gap-analysis-folder>` (the path the user supplied — see SKILL.md → Required inputs). Keep new content consistent with whatever is already there.

---

## 1. Severity rubric

| Tier              | CSS class       | When to use |
|-------------------|-----------------|-------------|
| **Critical**      | `sev-critical`  | Blocks bid scoping, blocks build, or carries unmodelled scope so material that pricing the bid against the wrong assumption could be commercially fatal. Always also tagged Critical in the master register. |
| **High**          | `sev-high`      | Material requirement mismatch, missing FR for a stated MVP capability, or BPMN structural error that will silently break a process at runtime. Must be resolved pre-build. |
| **Medium**        | `sev-medium`    | Scope ambiguity that can be clarified pre-build without blocking design. Includes audit-trail / governance gaps that are not on the critical path. |
| **Low**           | `sev-low`       | Boundary or cross-WS issue that the team can absorb during build, or a downgraded item once a decision is taken. |
| **Open Decision** | `sev-open`      | Genuine business decision not yet made by BSC — not a gap in the requirements, but cannot be ignored. Used in the master register, rare in individual reports. |
| **Resolved**      | `sev-resolved`  | Was previously raised, now answered or designed out. Keep the row but apply `class="resolved"` to fade it. |

Severity should be defensible in one sentence in the *Why It Matters* column. If you can't write that sentence, the severity is wrong.

---

## 2. Gap ID prefixes

Pick the prefix that describes the *kind* of finding, not the source file. Use this decision tree first; the full table below is a fallback when none of the cases match.

The tree is ordered by how often each prefix actually shows up across the existing reports — the first four cases cover the large majority of new rows, so check those before scanning further.

```
Is the gap a BPMN modelling defect (dead-end task, missing data object,
   no error-handling sub-process, untyped task)?              → BPM-
Does a FeatureSpec mark something P0/P1 with no FR to back it? → MFR-
Are two source documents in direct contradiction?              → CTR-
Is it a terminology or condition-type ambiguity?               → AMB-
Is it a SAP API payload the vendor cannot construct yet?       → SAP-
Is it Price Master / PCA / SAP-Integration commercial scope?   → COM-
Is it a regulatory / compliance issue (APPI, J-SOX, NHI,
   PMDA, FSA, retention)?                                      → REG-
Is it a workflow / governance risk that will reappear at
   go-live (single-user-per-role, missing fallback)?           → W-
Is it an integration scope undefined in Appendix A?            → INT-
Is it a confirmed architectural assumption with dispute risk?  → A-
Is it a system-to-system boundary issue?                       → B-
Is it an open business decision awaiting BSC?                  → D-
Default — generic gap or contradiction in the requirements    → G-
```

The `GAP-` prefix is reserved for cross-cutting issues that genuinely fit nowhere else; reach for it sparingly.

### Full table

| Prefix | Meaning |
|--------|---------|
| `G-`   | Generic **gap or contradiction** in the requirements. The default for "this is missing or wrong". |
| `W-`   | **Workflow / governance** risk that is not a platform gap but will reappear at go-live (single-user-per-role, missing fallback, etc.). |
| `B-`   | **Boundary** issue between two systems or workstreams (e.g. WS5/WS7 boundary). |
| `A-`   | Confirmed **architectural assumption** that carries dispute risk if BSC reads it differently. |
| `D-`   | **Open decision** awaiting BSC. Lives almost exclusively in the master register. |
| `AMB-` | **Ambiguity** — terminology, conflicting condition types, or fields that point two ways. |
| `BPM-` | **BPMN modelling defect** — dead-end task, missing data object, untyped task, etc. |
| `COM-` | **Commercial / pricing** gap (Price Master / PCA workstream). |
| `CTR-` | **Direct contradiction** between two source documents (RFP vs requirements vs FeatureSpec). |
| `GAP-` | **Cross-cutting** gap that doesn't fit neatly elsewhere — use sparingly. |
| `INT-` | **Integration scope** undefined — system named in Appendix A but no FR/interface spec. |
| `MFR-` | **Missing FR** — FeatureSpec marks something P0/P1 but no FR exists. |
| `REG-` | **Regulatory / compliance** gap (APPI, J-SOX, NHI, PMDA, FSA, retention). |
| `SAP-` | SAP Integration **payload design blocker** — vendor cannot construct the API call until BSC answers. |

Within each prefix, number sequentially (`G-01`, `G-02`, …). When you re-run the analysis, **never renumber existing IDs** — that breaks every reference in `open-questions.md` and the RFP master summary. Add to the end and mark resolved rows in place.

---

## 3. Workstream pills

The CSS class form differs by deliverable — the two flows use different stylesheets, and emitting the wrong form produces an unstyled grey pill. Always use the form that matches the file you're writing into.

| Workstream | In **individual reports** (Flow A / A2) | In **master register** (Flow B) | Covers |
|------------|------------------------------------------|----------------------------------|--------|
| WS1        | `<span class="pill pill-ws1">WS1</span>`      | `<span class="ws ws-ws1">WS1</span>`      | Identity / RBAC / approval workflow platform |
| WS2        | `<span class="pill pill-ws2">WS2</span>`      | `<span class="ws ws-ws2">WS2</span>`      | Budget / AOP / target setting |
| WS3        | `<span class="pill pill-ws3">WS3</span>`      | `<span class="ws ws-ws3">WS3</span>`      | Price configuration engine |
| WS4        | `<span class="pill pill-ws4">WS4</span>`      | `<span class="ws ws-ws4">WS4</span>`      | Approval workflow execution |
| WS5        | `<span class="pill pill-ws5">WS5</span>`      | `<span class="ws ws-ws5">WS5</span>`      | Contract management (quote, contract, e-sign) |
| WS6        | `<span class="pill pill-ws6">WS6</span>`      | `<span class="ws ws-ws6">WS6</span>`      | Rebate accounting (accrual + settlement + SAP postings) |
| WS7        | `<span class="pill pill-ws7">WS7</span>`      | `<span class="ws ws-ws7">WS7</span>`      | Rebate tracker / monitoring |
| Architecture | `<span class="pill pill-arch">ARCH</span>`  | `<span class="ws ws-arch">ARCH</span>`    | Cross-cutting architecture findings (JARVIS, ADL, Snowflake, integration topology) |
| Cross      | `<span class="pill pill-cross">CROSS</span>`  | `<span class="ws ws-cross">CROSS</span>`  | Affects multiple workstreams roughly equally |
| Regulatory | `<span class="pill pill-reg">REG</span>`      | `<span class="ws ws-reg">REG</span>`      | APPI / J-SOX / NHI / PMDA / FSA / Commercial Code |
| Commercial | `<span class="pill pill-comm">COMM</span>`    | `<span class="ws ws-comm">COMM</span>`    | Price Master / PCA / SAP Integration commercial workstream |

Quick check — confirm class form before saving:
- Filename ends `-gap-analysis.html` (not `gap-register.html`) → use `pill pill-*`.
- Filename is `gap-register.html` → use `ws ws-*`.

A row may carry two pills (e.g. WS5 + WS6 for a boundary issue): `<span class="pill pill-ws5">WS5</span> <span class="pill pill-ws6">WS6</span>` in an individual report, `<span class="ws ws-ws5">WS5</span> <span class="ws ws-ws6">WS6</span>` in the register. Match the `data-ws` attribute to the *upstream* workstream — the filter JS only matches a single value.

---

## 4. Owner pills

| Pill class        | Label                   | Who actually has to act |
|-------------------|-------------------------|--------------------------|
| `owner-bsc-sap`   | BSC SAP Team            | Field values, condition types, document types — anything inside SAP |
| `owner-bsc-biz`   | BSC Finance / Business  | Policy decisions (accrual vs settlement, dispute handling, etc.) |
| `owner-bsc-it`    | BSC IT / Digital        | JARVIS, Pitcher (BSC's sales-content app, not defined as an integration target in the RFP — use only when explicitly mentioned in source), Oracle Japan, RCE App, Snowflake — BSC-owned middleware and platforms |
| `owner-vendor`    | Vendor                  | Zühlke (or the eventual build vendor) |
| `owner-shared`    | BSC / Vendor            | Joint decision — neither party can act unilaterally |
| `owner-legal`     | BSC Legal / Regulatory  | APPI, FSA, NHI, PMDA, electronic signature, retention |

If you can't pick one cleanly, use `owner-shared` — but write the *Why* column so it's obvious what each side has to bring.

---

## 5. Card types (individual reports only)

| Card class        | What it represents |
|-------------------|--------------------|
| `card-inscope`| In-scope activity, FR-mapped. Sky/blue. |
| `card-sap`        | SAP-side activity (VK11, VA01, VF01, FB50). Indigo. |
| `card-external`   | External system activity (SFDC, ADL, JARVIS, JDH, Snowflake). Green/indigo depending on system. |
| `card-actor`      | Out-of-system human actor (Customer, Dealer, BSC user). Green. |
| `card-implied`    | Activity that is implied by the BPMN or requirements but not explicitly specified, or is inconsistent with another source. Amber, dashed border. |
| `card-gap`        | Activity that *should* exist but is missing. Red, dashed border. |
| `card-deferred`   | Activity explicitly deferred (post-MVP, out-of-scope). Green-grey. |
| `card-gateway`    | BPMN gateway (XOR / parallel). Neutral, diamond-style. |

Each card carries a small `card-bpmn` label (the BPMN ID) at top, an optional `card-fr` line (the FR/NFR/RFP citation), the title, the description, and one badge. Use the badges sparingly — they should reinforce the card colour, not duplicate it.

---

## 6. Glossary discipline

The terminology source of truth is the glossary / ubiquitous-language file the user supplied when invoking this skill (see SKILL.md → Required inputs). The path varies per project — never assume a hardcoded location. Read the glossary in full before drafting any row whose verdict turns on what a term means.

When the input documents disagree:

- **Don't pick one silently.** Quote both source forms verbatim (e.g. "FR_X14 references TermA; NFR-Y03 references TermB") and tag the row with an `AMB-` prefix.
- **Don't normalise.** Two specs using different names for the same concept is a clue that two teams used different vocabulary — preserve both, don't collapse to one.
- **Check the glossary first.** Variants the glossary already lists as synonyms are *not* `AMB-` — they're declared equivalences. Variants the glossary doesn't mention *are* `AMB-` until the user confirms.
- **Use the glossary's preferred form** in your own narrative prose (subtitles, intros, why-columns), but keep the source forms inside quoted spec citations.

If no glossary was supplied, default every terminology mismatch to `AMB-` and note the absence in the report's intro so reviewers know the analysis was done without one.

---

## 7. Provenance

Every row in the gap table should be traceable. The minimum is:

- A **source citation** in the *Gap* column (`FR_M19`, `RFP §5`, `NFR-I03`, `WS5-01_Quote Creation.bpmn line 312`, `FeatureSpec §Accrual`).
- A **why-it-matters** sentence framed for the bid team or BSC, not the dev team.
- An **owner pill** that points at the only party who can resolve it.

If any of those three are missing, the row is not ready.

---

## 8. Row ↔ arch-box coupling (individual reports)

The gap-register table and the three architecture-summary boxes are two views of the same data. They must stay in sync — readers skim the arch boxes first, then jump to the table for detail. A row in the table with no matching bullet in the arch boxes (or vice versa) is a bug.

The coupling rule, applied to *every* row added, removed, or re-severitied:

| Row state in gap-register | Bullet in arch box                     |
|----------------------------|----------------------------------------|
| Severity Critical / High / Medium / Low (open) | One bullet in `box-gap` ("✗ Missing — Must Be Raised") referencing the gap ID |
| Implied / inconsistent (`card-implied` exists upstream) | One bullet in `box-implied` ("~ Implied / Inconsistent") referencing the gap ID |
| Resolved (`sev-resolved`, `class="resolved"`) | Bullet moves to `box-confirmed` ("✓ BPMN ↔ Requirements Aligned") with the FR citation, or is removed if it was never confirmed |
| Severity changed | Bullet moves between boxes if the box-mapping changes |

Bullet format: `<li>Short title (G-04)</li>` — the gap ID in parentheses at the end so the reader can locate it in the table. Bullet titles should be copy-pasteable into Q&A items.

When you add a row, scroll to the arch-row and add the matching bullet *before* saving. When you remove or resolve a row, do the inverse. This is the single most common skipped step on report updates — treat it as part of the row, not a separate task.
