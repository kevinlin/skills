---
name: spec-lint
description: >
  Lint the project's specification docs (requirements / design / plan / task markdown):
  orphan specs, dead cross-doc links, index and naming drift, empty sections, stale
  TODOs, and — most importantly — reverse consistency between layers (design must
  cover its requirements, plans must cover their design). Auto-detects which
  spec-driven framework is in use — Kiro IDE, Superpowers, OpenSpec, GitHub spec-kit,
  BMad Method, GSD, or a generic default profile — and applies that profile's rules.
  Use when the user asks to lint, audit, or health-check spec docs ("/spec-lint",
  "check the specs", "spec health check"), asks whether design covers requirements
  or plans match the design, reports orphan specs or broken spec links, or names a
  supported framework in a context that implies auditing its spec artefacts.
metadata:
  version: 1.2.0
---

# spec-lint: Multi-Profile Specification Doc Health Check

Lint specification markdown produced during a spec-driven workflow. The goal is a clean, navigable spec tree where:

- A root index (or equivalent registry) lists every spec file.
- Each layer is consistent with the layer above it (design covers requirements; plan covers design).
- Cross-doc links resolve.
- Naming, structure, and metadata follow the conventions of the toolkit in use.

## Supported Profiles

Seven built-in profiles:

| Profile | Root | Layer chain |
|---|---|---|
| `default` | `docs/specs/` (or `specs/`) | requirements → design → plan → tasks (checkboxes) |
| `kiro` | `.kiro/specs/` | requirements/bugfix → design → tasks |
| `superpowers` | `docs/superpowers/plans/` | inline per dated plan file: Goal → Approach → Tasks |
| `openspec` | `openspec/` | spec + proposal → design → tasks → archive |
| `spec-kit` | `specs/` | constitution → spec → plan + data-model → tasks |
| `bmad` | `_bmad-output/` | PRD → architecture → epics/stories → sprint-status |
| `gsd` | `.planning/` | REQUIREMENTS → ROADMAP → phase PLANs → VERIFICATION |

The full profile definitions — folder and file rules, naming anti-patterns, layer mappings, required artefacts — live in [`references/convention.md`](references/convention.md). Step 2 seeds a copy into the project at `<SPECS_ROOT>/meta/convention.md`; that local copy is the single source of truth for every check that follows. The rules are read from it, not restated here.

---

## Step 1: Detect Profile and Locate the Specs Root

### 1.1 Check for explicit pointers

Read the project's `README.md` and `CLAUDE.md` (root + `.claude/CLAUDE.md`). Look for explicit references such as "spec docs in X", "design documentation: X", "see `docs/specs/`", "openspec", "kiro specs", "bmad", etc. An explicit pointer always overrides auto-detection.

### 1.2 Probe for profile signals

If no explicit pointer, scan the repository for these signals (stop at first hit per profile):

| Profile | Primary signal (existence confirms match) | Secondary signals |
|---|---|---|
| `kiro` | `.kiro/specs/` directory | `.kiro/steering/{product,tech,structure}.md`, `bugfix.md` files |
| `openspec` | `openspec/specs/` or `openspec/changes/` directory | `openspec/AGENTS.md`, `openspec/project.md` |
| `spec-kit` | `.specify/memory/constitution.md` | `specs/###-*/spec.md` numbered folders |
| `bmad` | `_bmad-output/` directory | `planning-artifacts/PRD.md`, `implementation-artifacts/sprint-status.yaml` |
| `gsd` | `.planning/PROJECT.md` | `.planning/{REQUIREMENTS,ROADMAP,STATE}.md`, `.planning/phases/` |
| `superpowers` | `docs/superpowers/plans/` with date-prefixed `.md` files | `skills/` directory at repo root |
| `default` | `docs/specs/`, `docs/spec/`, `specs/`, or `spec/` directory | Files matching `<artifact>_<topic>.md` |

### 1.3 Resolution rules

1. **Exactly one match** → use that profile and its canonical root.
2. **Multiple matches** → lint each profile independently; tag all findings with the profile name. Surface the multi-profile state as an `info` finding.
3. **No match** → ask the user where specs live. Do not invent a location.
4. **Local override** → if `<SPECS_ROOT>/meta/convention.md` has `active_profile:` set to something other than `auto`, use that profile exclusively regardless of signals.

Record the resolved profile(s) and root(s) as `PROFILE` and `SPECS_ROOT` for the rest of the run. All paths in the report are relative to the relevant `SPECS_ROOT`.

---

## Step 2: Sync the Local Convention Reference

The skill ships with a canonical convention reference at `references/convention.md`. Mirror it into the project so humans (and other tools) reading the spec tree have a local, customizable copy of the rules.

1. Determine the `meta/` location:
   - For profiles with a clear root (`default`, `kiro`, `openspec`, `spec-kit`, `bmad`, `gsd`): `<SPECS_ROOT>/meta/`.
   - For `superpowers` (flat plans folder): `<plans-dir>/../meta/` (sibling to `plans/`).
   - If multiple profiles are active, pick the primary one (the one with most spec files) for the meta location.

2. Ensure the `meta/` directory exists. Create it if missing.

3. Decide what to do with `meta/convention.md`:
   - **Missing** → copy the bundled `references/convention.md` verbatim. Mention the seed in the lint report (`info`).
   - **Present and identical** → no action. Use the local copy as the rule set.
   - **Present but differs** → do **not** overwrite. Use the local copy as the rule set and add an `info` finding. Show a brief diff summary.

4. **Read the local copy.** Its profile definitions, naming patterns, anti-patterns, allowed artifact types, layer mappings, and decision tables are the authoritative input for Steps 3–5.

---

## Step 3: Inventory the Tree

Walk each detected `SPECS_ROOT` recursively — every `.md` file, plus registry files where the profile uses them (e.g. `sprint-status.yaml` for `bmad`, `config.json` for `gsd`).

Classify every file into the artefact classes the active profile defines in the local `convention.md` (its folder/file rules and layer-mapping table). Anything under `meta/` is `meta`; anything matching no rule is `other`.

Track for each file: relative path, class, parent folder, headings, outbound markdown links, inbound references (second pass).

Build a **folder map**: for each folder, record which classes are present and how complete the folder is relative to the profile's required artefacts.

The inventory is complete when every file under every `SPECS_ROOT` carries exactly one class and every folder appears in the folder map.

---

## Step 4: Verify the Root Index / Registry

Each profile has a different concept of "index". Check the right thing for each:

| Profile | Expected index/registry | What it must list |
|---|---|---|
| `default` | `SPECS_ROOT/index.md` (or `README.md`) | Every `design_*`, `plan_*`, `requirements_*` file |
| `kiro` | Directory listing (implicit) | Every feature folder has all required files |
| `superpowers` | Directory listing (implicit) | All plan files match date-prefix pattern |
| `openspec` | `openspec/AGENTS.md` or folder listing | All active changes; all domain specs |
| `spec-kit` | Folder listing under `specs/` | Numbered folders are sequential, no gaps |
| `bmad` | Bundle completeness | `PRD.md` + `architecture.md` + epics present |
| `gsd` | `ROADMAP.md` + `STATE.md` | Phases in ROADMAP match phase folders |

Lint checks for explicit-index profiles (`default`):

- **Root index exists.** Missing = `error`; auto-fix = scaffold it (Step 7).
- **Every spec file on disk is linked from the root index.** Missing = `warn` (orphan).
- **Every link in the index resolves.** Broken = `error`.

Lint checks for implicit-index profiles (`kiro`, `superpowers`, `spec-kit`, `bmad`, `gsd`):

- **Completeness**: each feature/change/phase folder contains the artefacts the profile requires (per the local `convention.md`). Missing artefacts = `warn` with a note about which file is expected.
- **Consistency**: registry files (like `ROADMAP.md` or `sprint-status.yaml`) reference all active work units.

---

## Step 5: Run the Lint Checks

Run all nine checks, in order, on every run — a check with nothing to report is clean, never skipped. Each check produces zero or more findings classified `error`, `warn`, or `info`. Tag each finding with the active profile when multiple profiles are active.

### 5.1 Naming convention (`warn`)

Apply the active profile's folder-naming and file-naming rules and its anti-pattern table from the local `convention.md`. Common to all profiles: flag generic/transient filenames (`notes.md`, `todo.md`, `draft.md`, `wip.md`) and typos.

### 5.2 Dead cross-doc links (`error`)

For every outbound link in every spec file, resolve relative to the source file. Flag:

- Target file does not exist.
- Anchor (`#section`) does not match a heading in the target file (slugify: lowercase, spaces → `-`, strip non-alphanumerics).
- Link points outside `SPECS_ROOT` but the file does not exist.

### 5.3 Orphan specs (`warn`)

A spec file is an orphan if it has zero inbound references from any other spec file *and* is not linked from the root index (for profiles that have an explicit index). Files under `meta/` are exempt.

For implicit-index profiles, "orphan" means a file that doesn't fit the profile's expected folder structure (e.g., a random `.md` file at the root of `.kiro/specs/` that isn't inside a feature folder).

### 5.4 Empty sections (`warn`)

Heading with no content under it before the next heading of equal-or-higher level. Skip intentional placeholder headings ("## TBD", "## Future Work") if the immediate next line is a one-line "TBD" — flag those as `info` instead.

### 5.5 Open-ended TODO markers (`info`)

Tokens `TODO`, `TBD`, `FIXME`, `XXX`, `???` in plan/design files. List each occurrence with file:line.

### 5.6 Frontmatter / required headings (`info`)

If at least one file in the tree uses YAML frontmatter, treat that as the project convention and flag siblings of the same class that lack frontmatter.

Profile-specific heading requirements (body content is out of `convention.md`'s scope, so these live here):
- **`default`**: plan files should have a **Goal** and either **File Structure** or **Tasks** section.
- **`kiro`**: `requirements.md` should have numbered acceptance criteria. `tasks.md` should have checkboxes.
- **`superpowers`**: plan files should have sections for Goal/Context, Design/Approach, and Tasks/Steps.
- **`gsd`**: `*-PLAN.md` files should have a clear task description and acceptance criteria.

### 5.7 Registry drift (`error` / `warn` / `info`)

For profiles with registry files, cross-check each registry against disk in both directions, using the active profile's required-artefacts and layer-mapping sections in the local `convention.md` (e.g. `ROADMAP.md`/`STATE.md` phase and task numbers for `gsd`, `sprint-status.yaml` stories for `bmad`, active changes in `openspec/AGENTS.md`):

- Registry entry points at a missing file or work unit = `error`.
- File or work unit absent from its registry, or an index row assigned to the wrong module/folder = `warn`.
- Cosmetic gaps (e.g., non-sequential `spec-kit` folder numbers) = `info`.

Root-index drift for `default` is already produced by Step 4.

### 5.8 Reverse consistency: design covers requirements (`warn`)

Trace the active profile's layer chain using the layer-mapping and reverse-consistency sections of the local `convention.md`: for each design-layer artefact, locate its upstream requirements-layer artefact(s), extract every requirement item, and check each is addressed in the design. For `superpowers` this is an intra-document check (the Approach/Design section covers the Goal/Context section).

Extraction heuristic: functional requirements are numbered items, checkboxed items, `### N.N` headings, or bullet lists under a "Requirements" / "Acceptance Criteria" heading.

The check is complete when every requirements-layer file in scope has been opened and each extracted item matched or reported as `warn`. Recall over precision: report borderline gaps and let the human dismiss false positives.

### 5.9 Reverse consistency: plan/tasks covers design (`warn`)

Same procedure one layer down: each plan/tasks-layer artefact must address every component and decision of its upstream design-layer artefact(s) per the profile's layer mapping (`gsd` adds: each phase's `*-VERIFICATION.md` covers that phase's `*-PLAN.md` files; `superpowers`: the Tasks/Steps section covers the Approach/Design section). Same completion criterion and recall-over-precision posture as 5.8.

---

## Step 6: Lint Report

Write the report to the `meta/` location determined in Step 2, named `lint-report-YYYY-MM-DD.md`. Overwrite if a same-day report already exists.

```markdown
# Spec Lint Report — YYYY-MM-DD

Profile(s): `<profile-name>` [auto-detected | locked via convention.md]
Specs root: `<SPECS_ROOT>`

## Summary

- Files scanned: N (by class breakdown)
- Profile completeness: X/Y expected artefacts present
- Errors: N
- Warnings: N
- Info: N
- Auto-fixed: N (if applicable)

## Convention Reference

- Path: `<meta/convention.md>`
- Status: present (in-sync with skill) | present (drifted from skill) | seeded this run
- Active profile: `<profile>`

## Root Index / Registry

- Path: `<index path or "implicit">`
- Status: present | missing | scaffolded | N/A (implicit index)
- Files linked: N / total spec files (for explicit-index profiles)
- Completeness: N/M folders have all required artefacts (for implicit-index profiles)

## Errors

### Dead links
- `<source file>:<line>` → `<target>` (not found)
- `<source file>:<line>` → `<target>#<anchor>` (anchor missing)

### Index / registry drift
- `<file>` exists but absent from root index.
- Index entry `<row>` points at `<missing path>`.
- Feature folder `<folder>` missing required `<file>`.

## Warnings

### Orphan specs
- `<file>`: no inbound references. Suggest linking from `<closest parent>`.

### Naming
- `<file>`: non-canonical name. Suggested rename: `<new name>`. Rule: `<profile> — <convention.md section>`.

### Reverse consistency — design ↔ requirements
- `<design file>` may not cover requirement `<id> <title>` from `<requirements file>`.

### Reverse consistency — plan ↔ design
- `<plan file>` may not cover design item `<section>` from `<design file>`.

### Empty sections
- `<file>:<heading>` has no content.

## Info

### Profile detection
- Detected profile(s): `<profile>` via signal `<signal path>`.
- Multi-profile note (if applicable): …

### Convention drift
- `meta/convention.md` differs from the skill's bundled version. Local copy was used for this run. Refresh from skill? (Diff summary: …)

### TODO markers
- `<file>:<line>`: TODO …

### Stub indicators
- `<file>`: heading `<TBD>` placeholder.

### Completeness gaps
- `<folder>`: missing `<expected-file>` (profile `<profile>` expects this artefact).
```

Sort findings within each subsection by file path, then line number.

---

## Step 7: Auto-Fix

Always show the report first. Then ask:

> "Auto-fix the safe items, walk through them one-by-one, or stop here?"

Safe to auto-fix without per-item confirmation:

- **Scaffold a missing root index** (for `default` profile): Create `SPECS_ROOT/index.md` with tables populated from the inventory. Pre-fill coverage columns with `TBD`.
- **Add missing rows to an existing root index** (for `default`): Append orphan files grouped by module folder. Mark new rows with `<!-- spec-lint:added -->`.
- **Add missing wiki-style cross-links**: Convert filename-only references to proper relative markdown links.
- **Create missing directories**: For profiles that expect a certain structure (e.g., `.kiro/steering/` or `meta/`), create empty directories.

Needs explicit per-item confirmation:

- Renaming files (changes git history; may break external links).
- Filling in empty sections.
- Resolving reverse-consistency gaps (authoring decisions).
- Creating stub artefact files (e.g., a missing `design.md` for a Kiro feature folder).
- Deleting anything. Lint never deletes files.

When auto-fixing, re-run the lint pass to confirm issues are resolved and update the report's *Auto-fixed* count.

---

## Operating Posture

- **Read-only over spec content.** The only writes without explicit approval are bookkeeping artefacts under `meta/`: seeding `meta/convention.md` (Step 2) and writing the dated lint report (Step 6). Both are idempotent and never modify a file the human has customized. Every other mutation — index scaffolding, link rewrites, renames, stub creation — goes through Step 7 approval.
- **Profile-aware.** Apply the rules of the detected (or locked) profile as defined in the local `convention.md`.
- **Recall over precision** on reverse consistency — report borderline gaps; the human dismisses false positives.
- **Idempotent.** Running spec-lint twice in a row produces the same report (modulo timestamp). Auto-fix outputs must not introduce new lint errors.
- **Scope: spec markdown structure only.** No code validation (typecheck, tests, `cargo check`); `UPDATE_LOG.md`, changelogs, and post-completion checklists are out of scope; profile migration (e.g., Kiro → default) is a separate task the user can request.
