---
name: spec-compact
description: >
  Compact a spec plan (or design doc) markdown file after the implementation
  has shipped: strip the transient how — code snippets, step-by-step
  walkthroughs, file-by-file diffs — that the codebase now owns, keep the why —
  design decisions, key file references, changelog. Use when the user wants to
  compact, shrink, or trim a plan/spec file post-implementation, says the plan
  is bloated or too long now that the feature shipped, or invokes
  `/spec-compact`. Renaming files, fixing dead links, and index updates belong
  to `spec-lint`.
metadata:
  version: 1.1.0
---

# spec-compact: Post-Implementation Spec File Compaction

After a feature lands, the plan that guided it is usually 3–10× larger than future readers need. Code blocks, per-step walkthroughs, and `Verify:` command lists earned their keep during implementation but now duplicate what the codebase and git history carry. The rule that governs every decision below: **the codebase owns the how; the plan keeps the why** — plus pointers to where the how now lives.

Scope guard: naming, dead links, index drift, and reverse coverage belong to `spec-lint`. Surface them in the final report; the fix happens in a `spec-lint` run, keeping each diff single-purpose.

---

## Step 1: Resolve the Specs Root and Read Local Meta

Build a small map of the spec tree first, so the compaction can keep links to the sibling specs that own the long-term knowledge instead of restating them.

1. Identify the specs root, stopping at the first hit:
   - Read `README.md` and `CLAUDE.md` (root + `.claude/CLAUDE.md`) for an explicit pointer ("design docs in `docs/specs/`").
   - Probe in order: `docs/specs/`, `openspec/specs/`, `specs/`, `docs/spec/`, `spec/`.
   - Still none → ask the user where the specs live.
2. If `<SPECS_ROOT>/meta/convention.md` exists, read it — the per-project source of truth for artifact classes (`requirements`, `design`, `plan`, plus project extensions like `runbook` or `adr`). Compaction applies to **plan** and (when explicitly requested) **design** files only.
3. If `<SPECS_ROOT>/index.md` exists, read it to find the sibling `design_<topic>.md` for the input plan, the closest `requirements_<topic>.md` (and root `requirements.md`), and other plans in the same module folder.

Step 1 is done when you have recorded three values: the sibling design path, the closest requirements path, and sibling plan paths (each may be "none found"). If `meta/convention.md` or `index.md` are missing, proceed on filename and location alone and note the degraded context in the final report.

---

## Step 2: Validate the Input and Read the File

The user passes one spec file path. Verify before touching it:

1. The path resolves to a file inside `SPECS_ROOT`. If it points outside the spec tree, ask the user to confirm before proceeding.
2. The file's class is `plan` or `design` (per the convention). Refuse `requirements`, `index`, `meta`, or `other` files with one line:
   > "spec-compact only operates on `plan_*.md` and `design_*.md` files — `<file>` is a `<class>` file, which has different content lifetime semantics. Re-invoke with `--force` to override."

   On `--force`, proceed and apply the plan rules.
3. Compacting a `design_*.md` is allowed but more conservative: design docs are the long-term home for decisions and components, so the bar for removing content is higher than for plans.
4. Read the file fully. Note lines + bytes for the before/after summary.
5. Confirm the implementation has shipped. Any one heuristic suffices:
   - Files in the plan's Critical Files table exist on disk in the working tree.
   - `UPDATE_LOG.md` (or equivalent) mentions the feature.
   - The plan has a `## Changelog` / `## Status` section noting completion.
   - The user's prompt says it has shipped.
   - `git log --oneline -- <referenced-files>` returns commits.

   If all are silent, ask: "I can't tell whether this plan has shipped — compaction removes detail from the spec for good (only git preserves it). Confirm the implementation is complete?" Wait for an explicit yes.

---

## Step 3: Classify Every Section

Walk the file and put every `##` and `###` heading into exactly one bucket: **keep**, **thin**, **remove**, **hoist**, or **defer**. Step 3 is done when every heading in the file appears in the Step 4 report. Bias toward **keep**: a slightly-bloated plan costs little; a deleted irreplaceable rationale costs a lot.

Two principles govern the buckets:

- **Preserve the heading skeleton.** The bloat lives in section *bodies* — code blocks, exact diffs, per-step worklist prose — not in the structure. A reader looking for "Implementation Plan" should still find a section by that name; it is just a thin worklist now. Delete a whole section only when folding it into a sibling spec.
- **Hoist before folding.** When a section body is replaced by a link to a sibling spec (typically a plan that embeds a verbatim draft of its own `design_<topic>.md`), first lift the plan-specific subsections — cleanup lists, file-deletion tables, breaking-change notes — out to top-level `##` sections. They don't belong in the design and must not vanish with the wrapper.

### Classification rules

| Content | Action |
|---|---|
| `## Context` / `## Goal` (current state / why change / target state) | **Keep** verbatim — the most-read block in the file. Tense-shift to past post-shipping counts as tightening. |
| `## Design Decisions` / `## Approach` / `## Confirmed Design Choices` | **Keep** verbatim — the most expensive content to recreate. Exception: mirrored verbatim in the sibling design → keep it there, link from the plan. |
| Error-handling tables, decision matrices, taxonomy lists, IPC command tables | **Keep** verbatim — reference material, not implementation steps. |
| Architecture diagrams, ASCII layouts, Mermaid blocks | **Keep** verbatim — high signal per line. |
| Cross-doc links to `design_*.md`, `requirements.md#X.Y`, sibling plans | **Keep** — future readers should be one click from the canonical home of decisions and acceptance criteria. |
| Top-of-file requirement linkage ("Plan: X (Requirement 6 + 4.3.3)") | **Keep** — feeds `spec-lint`'s reverse coverage check. |
| Live TODOs naming follow-up work not yet done | **Keep**, under a `## Outstanding follow-ups` heading. |
| `## Changelog` / `## Status` / `## History` | **Keep**; prepend the new compaction entry (see below). |
| `## Implementation Plan` / `## Tasks` | **Thin**: keep the section heading and every `### Task N — <title>` heading; replace each task body with 1–3 sentences of past-tense intent (what was done and why). Lift interwoven design rationale into `## Design Decisions` (or the intent sentence itself) — rationale is never deleted. |
| `## Cleanup of the Old Implementation` / `## Removed` / `## Deprecations` / `## Breaking Changes` | **Thin** to a compact `path \| change` table: one row per deleted file or removed surface, 1-phrase reason. These are the breadcrumbs that tell a future reader "this used to exist". |
| `## Critical Files — Summary` table | **Thin**: one-line note per row; drop rows with no forward value (one-time config edits, files tweaked in passing, this plan's own doc rewrites). Collapse any separate `Files modified` worklist table into it. |
| Long code block defining a public type or data model (design artefact) | **Thin** to a 2–4 line schema sketch (field names + types) plus a link to the canonical file. |
| Repeated cross-references ("as described in Step 3 above") | **Thin**: resolve once and link, or drop if the target no longer exists post-compaction. |
| All other fenced code blocks (```ts, ```rust, ```sql, ```bash, …) | **Remove** — the compiled, versioned code is the source of truth; snippets rot and mislead. |
| `Steps:` bodies that are file-by-file diffs ("Replace X with Y", "Add field Z to `TaskConfig`") | **Remove** — the diffs are in git; the task heading + intent line carry the meaning. |
| Per-task `Files:` preambles (Modify X / Modify Y / Modify Z) | **Remove** — consolidate paths into the Critical Files table. |
| `Verify:` lines — project commands (`pnpm typecheck`, `cargo check`) and per-task test commands | **Remove** — project commands belong in `CLAUDE.md` / `AGENTS.md`; tests live in the repo. |
| Per-task test case-name lists ("tests: `does X`, `does Y`") | **Remove** — the test file is the record. If a name is the only trace of a behavioural intent, lift a one-line summary into the task intent first. |
| TODO / TBD / FIXME markers about work that was done | **Remove** — stale. |
| `[path](path)` link wrappers in prose that are broken or redundant | **Remove** the wrapper, keep the code-quoted path. |
| Section duplicating the sibling `design_<topic>.md` verbatim | **Hoist** plan-specific subsections, then replace the body with one line: "See [`design_<topic>.md`](…) for the canonical design." |
| Naming violations, dead links/anchors, index drift, missing requirement IDs or coverage columns, empty headings, reverse-coverage gaps | **Defer** to `spec-lint` — list in the final report only. |

### Changelog entry

Plan a changelog entry near the bottom of the file:

```markdown
## Changelog

- YYYY-MM-DD — **Compacted post-implementation.** Removed step-by-step tasks, file-by-file diffs, code snippets, and verification commands now that the feature has shipped. Preserved Goal, Design Decisions, Critical Files summary, and follow-ups. Original plan recoverable via git history.
```

Use the actual current date. Prepend to an existing `## Changelog`, keeping all old entries. If the plan uses `## Status` or `## History` instead, keep that section name and add the entry there in the same style.

---

## Step 4: Show the Compaction Plan and Confirm

Compaction is irreversible without git, so an explicit go-ahead is required even when the invocation sounds decisive ("compact this plan now"). Show this report in chat before writing anything:

```markdown
## Compaction plan for `<file>`

- Current size: N lines / M bytes
- Estimated post-compaction: ~P lines / Q bytes (~L% line, ~B% byte reduction)
- Sibling design (kept as link): `<path or "none found">`
- Closest requirements (kept as link): `<path or "none found">`

### Remove in full (folded into a sibling spec)
- `## <Heading>` — <reason; name the sibling target>

### Thin in place (heading kept, body replaced)
- `## <Heading>` — <what stays vs what goes>

### Keep verbatim
- `## <Heading>` — <one-line reason>

### Hoist (lift out of a removed wrapper)
- `### <Subheading>` (under `## <Wrapper>`) → top-level `## <Subheading>` — <why it is plan-specific>

### Defer to spec-lint
- <one line per finding, or "None observed">

Proceed? (yes / preview-file / preview-diff / abort)
```

Wait for the answer:

- **yes** → apply in place (Step 5).
- **preview-file** → write the compacted result to `<original>.compacted-preview.md`, report the path, and stop; the original stays untouched. Useful the first time on a contentious file.
- **preview-diff** → show the rewritten file body in chat, then ask again.
- **abort** → stop; confirm nothing was written.

---

## Step 5: Apply and Report

1. Write the file in place. Preserve any frontmatter block and the H1 (`# Plan: …`) untouched.
2. Lint the output: every code fence closed and link bracket matched; the changelog entry present; no duplicated `## Goal` / `## Context` / `## Design Decisions` headings from consolidation.
3. Print:

```markdown
## Compacted `<file>`

- Before: N lines / M bytes → After: P lines / Q bytes (L% line, B% byte reduction)
- Removed: <count> code blocks, <count> step-list sections, <count> file tables
- Kept: Goal/Context, Design Decisions, Critical Files, <other named sections>
- Changelog entry added: YYYY-MM-DD

### Suggested next steps
- Run `spec-lint` to refresh reverse-consistency coverage and handle any naming / index drift this run deferred.
- If you maintain `UPDATE_LOG.md`, the implementation entry there is now the authoritative narrative for the feature.
```

4. Leave the diff uncommitted — the user reviews it in their VCS tool and decides when to commit.

---

## Operating Posture

- **Single-file mutation.** The only write is to the file passed in (or its `.compacted-preview.md` sibling). Everything else — `meta/convention.md`, `index.md`, sibling design/requirements, `UPDATE_LOG.md`, release notes — is read-only context. Deleting or moving an obsolete plan is the user's call.
- **One invocation, one file.** For several plans, run once per file so each diff stays small and reviewable.
- **Idempotent.** A second run on the same file is (almost) a no-op; if a compaction changelog entry already exists, skip writing a duplicate.
- **Composable with `spec-lint`.** Typical flow: implement → ship → `spec-compact` the plan → `spec-lint` the tree to refresh coverage and surface anything the compaction made newly visible.
