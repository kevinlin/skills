---
active_profile: auto
---

<!--
  Specification convention reference used by the spec-lint skill.

  This file is the canonical naming + structure rule set. It lives in two places:

  1. spec-lint/references/convention.md      — the version bundled with the skill.
                                               Updated when the skill itself is updated.
  2. <spec_root>/meta/convention.md          — the local copy seeded by spec-lint into
                                               the project. This is the per-project
                                               source of truth; edit it to customize
                                               folder names, supported artifact types,
                                               allowed exceptions, the active profile,
                                               etc.

  When spec-lint runs:
  - If <spec_root>/meta/convention.md is missing, the bundled version is copied in.
  - If both exist and differ, the local copy wins for linting decisions and a notice
    is added to the report so the human can choose to refresh.

  The frontmatter `active_profile` controls profile selection:
  - `auto`       (default) — spec-lint detects the profile from filesystem signals.
  - `default`    — the house style described in §3.
  - `kiro`       — Kiro IDE convention (§4).
  - `superpowers`— Superpowers plans convention (§5).
  - `openspec`   — OpenSpec specs + changes convention (§6).
  - `spec-kit`   — GitHub spec-kit numbered-feature convention (§7).
  - `bmad`       — BMad Method planning + implementation artefacts (§8).
  - `gsd`        — GSD `.planning/` workspace convention (§9).

  Multiple profiles can coexist in a single repo (e.g., Kiro for new features and the
  default style for legacy specs). When `active_profile: auto` and more than one
  signal matches, spec-lint lints each profile independently and surfaces both in the
  report.

  Edit the local copy freely. Do not edit this bundled copy from inside a project.
-->

# Specification File Structure and Naming Convention

Spec-driven development produces a small, well-known set of artefacts: requirements (or specs), design (or architecture), plans (or tasks), and execution state. **What** each artefact contains is broadly the same across toolkits; **how** they are named and laid out on disk varies a lot. This file describes seven layouts the spec-lint skill recognises out of the box, plus the rules used to detect and lint each one.

The convention defines **file structure, naming, and intent**. It does not prescribe the body content of each spec — feature templates, acceptance-criteria formats, and decision logs are deliberately out of scope.

---

## 1. Profiles Overview

A **profile** is a named bundle of conventions that fit one toolkit or workflow. Picking the right profile lets spec-lint:

- Walk the right filesystem root.
- Recognise the right filenames as `requirements`, `design`, `plan`, `task`, `index`, or `meta`.
- Apply the right naming rules and anti-patterns.
- Trace coverage along the right layers (which design covers which requirements, which plan covers which design).

Seven profiles ship with the skill:

| # | Profile | Origin | One-line summary |
|---|---|---|---|
| §3 | `default` | This project's house style ("zapac") | One folder per module under `docs/specs/`; files named `<artifact>_<topic>.md`. |
| §4 | `kiro` | [Kiro IDE](https://kiro.dev/docs/specs/) | One folder per feature under `.kiro/specs/`; fixed filenames (`requirements.md`, `design.md`, `tasks.md`, `bugfix.md`). |
| §5 | `superpowers` | [obra/superpowers](https://github.com/obra/superpowers) | Single date-prefixed plan files under `docs/superpowers/plans/`. |
| §6 | `openspec` | [Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) | Source-of-truth specs at `openspec/specs/<domain>/spec.md` plus change folders at `openspec/changes/<change>/`. |
| §7 | `spec-kit` | [github/spec-kit](https://github.com/github/spec-kit) | Numbered feature folders `specs/###-feature-slug/`, fixed artefact names, `.specify/memory/constitution.md` for project rules. |
| §8 | `bmad` | [BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD) | Planning vs implementation split under `_bmad-output/`; `PRD.md`, `architecture.md`, `epics/`, `sprint-status.yaml`. |
| §9 | `gsd` | [Get Shit Done](https://gsd-build-get-shit-done.mintlify.app) | `.planning/` workspace with uppercase core docs (`PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md`) and numbered phase/task files. |

Profiles are **not mutually exclusive**. Spec-lint can detect and lint several at once if a project is mid-migration or pairs (say) Kiro for product specs with `default` for ADRs.

---

## 2. Detecting the Active Profile

When `active_profile: auto`, spec-lint scans the repository root and matches each profile's signal set. The first signal listed for a profile is enough to confirm a match.

| Profile | Primary signal (existence implies a match) | Secondary signals |
|---|---|---|
| `kiro` | `.kiro/specs/` directory | `.kiro/steering/{product,tech,structure}.md`, `bugfix.md` files |
| `openspec` | `openspec/specs/` or `openspec/changes/` directory | `openspec/AGENTS.md`, `openspec/project.md` |
| `spec-kit` | `.specify/memory/constitution.md` | `specs/###-*/spec.md` numbered folders, `specs/*/contracts/` |
| `bmad` | `_bmad-output/` directory | `_bmad-output/planning-artifacts/PRD.md`, `_bmad-output/implementation-artifacts/sprint-status.yaml` |
| `gsd` | `.planning/PROJECT.md` | `.planning/{REQUIREMENTS,ROADMAP,STATE}.md`, `.planning/phases/##-*/` |
| `superpowers` | `docs/superpowers/plans/` directory containing date-prefixed `.md` files | `skills/` directory at repo root with `SKILL.md` files |
| `default` | `docs/specs/`, `docs/spec/`, `specs/`, or `spec/` directory | Files matching `<artifact>_<topic>.md` patterns |

**Resolution rules:**

1. If exactly one profile matches, use it.
2. If multiple profiles match, lint each one independently and tag findings with the profile name. Surface the multi-profile state as an `info` finding so the human can decide whether to consolidate.
3. If no profile matches, ask the user. Do not invent a location.
4. To override detection, set `active_profile:` in the local `<spec_root>/meta/convention.md` frontmatter to a specific profile name (or to `auto` to re-enable detection).

Project-level overrides:

- `README.md` or `CLAUDE.md` may name the spec root explicitly (e.g., "design docs in `docs/specs/`"). An explicit pointer always wins over auto-detection.
- A README that names a different folder than the detected profile's canonical root takes precedence; the report should note the mismatch as `info`.

---

## 3. `default` Profile — House Style

This is the project's home-rolled convention. Use it when no toolkit has been adopted, or when migrating off one.

### 3.1 Core rules

1. All specification files live under a single `<spec_root>` directory. Most projects use `docs/specs/`; spec-lint resolves the actual root automatically.
2. The root contains **project-level** specs (overall requirements, overall design, navigation index, and tooling artefacts).
3. Each module or feature has **one folder** under `<spec_root>`.
4. Module and feature folder names use **kebab-case**.
5. Module-level spec files follow the pattern `<artifact-type>_<topic>.md` where `<artifact-type>` ∈ {`requirements`, `design`, `plan`}.
6. Use exactly **one underscore** between the artifact type and the topic. Use **kebab-case** inside the topic.
7. Plan files should link back to the requirements (by ID or section) and design they implement.
8. Do not use generic or transient names (`notes.md`, `todo.md`, `draft.md`, `final.md`, `wip.md`, `temp.md`, `v2.md`).
9. Do not include dates in filenames except in `meta/` artefacts (e.g., dated lint reports).
10. Generated tooling artefacts (lint reports, indices, conventions copies) live under `<spec_root>/meta/`.

### 3.2 Artifact types and intent

| Artifact | Purpose | Where it lives |
|---|---|---|
| **`requirements.md`** (root) | Project-level acceptance criteria, numbered. The contract for what the product does. | `<spec_root>/requirements.md` |
| **`design.md`** (root) | Project-level architecture: tech stack, multi-process layout, cross-cutting decisions. | `<spec_root>/design.md` |
| **`index.md`** (root) | Navigation map of every design and plan grouped by module. The single jump-off point. | `<spec_root>/index.md` |
| **`requirements_<topic>.md`** | Module-internal full requirement spec when the root summary is too coarse. Maps each section back to root requirement IDs. | `<spec_root>/<module>/` |
| **`design_<topic>.md`** | Module-level architecture: components, data model, decisions, resolved issues. | `<spec_root>/<module>/` |
| **`plan_<topic>.md`** | Implementation plan for one module *or* one sub-feature. Multiple plans per module are normal. | `<spec_root>/<module>/` |
| **Supporting files** (`*.json`, `*.yaml`, `*.png`) | API contracts, schemas, mock-ups referenced from a spec. Same folder as the spec that consumes them. | `<spec_root>/<module>/` |
| **`meta/`** | Generated tooling artefacts (lint reports, conventions copies, generated indices). Safe to delete and regenerate. | `<spec_root>/meta/` |

A module always has at least one of {`design_<topic>.md`, `plan_<topic>.md`}. A folder containing only `requirements_<topic>.md` is a sign the design has not been written yet.

### 3.3 Naming decision table

| Need | Location | Filename | Example |
|---|---|---|---|
| Spec navigation index | `<spec_root>/` | `index.md` | `docs/specs/index.md` |
| Project requirements | `<spec_root>/` | `requirements.md` | `docs/specs/requirements.md` |
| Project design | `<spec_root>/` | `design.md` | `docs/specs/design.md` |
| Module requirements (full spec) | `<spec_root>/<module>/` | `requirements_<module>.md` | `workspace-as-folder/requirements_workspace-as-folder.md` |
| Module design | `<spec_root>/<module>/` | `design_<module>.md` | `app-ux/design_app-ux.md` |
| Module implementation plan | `<spec_root>/<module>/` | `plan_<module>.md` | `workspace-packs/plan_workspace-packs.md` |
| Sub-feature plan inside a module | `<spec_root>/<module>/` | `plan_<sub-feature>.md` | `app-ux/plan_keyboard-shortcuts.md` |
| API contract / schema | `<spec_root>/<module>/` | `<contract-name>.{json,yaml}` | `opencode-integration/opencode-api.json` |
| Generated lint report | `<spec_root>/meta/` | `lint-report-YYYY-MM-DD.md` | `meta/lint-report-2026-05-09.md` |
| Local convention reference | `<spec_root>/meta/` | `convention.md` | `meta/convention.md` |

### 3.4 Folder naming rules

Each module or feature lives in exactly one folder: `<spec_root>/<module-or-feature>/`.

Allowed: lowercase letters, hyphens between words (`workspace-as-folder/`, `chat-ux/`), stable product or architecture names.

Disallowed: spaces, underscores, dots, camelCase, PascalCase, dates (`2026-05-feature/`), trailing-version markers (`feature-v2/`, `feature-old/`). Iterate by editing the existing folder; preserve history through git.

### 3.5 File naming rules

Pattern: `<artifact-type>_<topic>.md`.

- `<artifact-type>` is exactly one of `requirements`, `design`, `plan`.
- `<topic>` describes the module, feature, or implementation slice.
- Exactly one underscore between type and topic; kebab-case inside the topic.

**Anti-patterns**

| Anti-pattern | Example | Fix |
|---|---|---|
| Hyphen between type and topic | `plan-keyboard-shortcuts.md` | `plan_keyboard-shortcuts.md` |
| Underscore inside the topic | `plan_keyboard_shortcuts.md` | `plan_keyboard-shortcuts.md` |
| Multiple underscores as separator | `plan__keyboard-shortcuts.md` | `plan_keyboard-shortcuts.md` |
| Generic / transient name | `notes.md`, `todo.md`, `draft.md` | `<artifact>_<topic>.md` |
| Phase or version in filename | `plan_phase1.md`, `plan_v2.md` | Meaningful topic; preserve history via git |
| Bare `plan.md` in a module folder | `workspace-packs/plan.md` | `workspace-packs/plan_workspace-packs.md` |
| Typo in topic | `plan_todo-panel-in-sidebard.md` | `plan_todo-panel-in-sidebar.md` |
| Mixed casing | `plan_KeyboardShortcuts.md` | `plan_keyboard-shortcuts.md` |

Existing legacy files that already use underscores inside the topic may remain temporarily; flag as `warn`, not `error`, so cleanup can be batched.

### 3.6 Layer mapping (for reverse consistency)

| Layer | File |
|---|---|
| Requirements | Closest `requirements_<topic>.md` walking up to `<spec_root>/requirements.md`. |
| Design | Closest `design_<topic>.md` walking up to `<spec_root>/design.md`. |
| Plan | Each `plan_<topic>.md`. |
| Tasks | Inline checkboxes inside the matching plan. |
| State | Task checkboxes; no separate state file. |

### 3.7 Example tree

```text
docs/specs/
├── index.md                              # navigation map
├── requirements.md                       # project-level ACs
├── design.md                             # project-level architecture
├── meta/
│   ├── convention.md                     # local copy of this file
│   └── lint-report-2026-05-09.md         # generated by spec-lint
├── app-ux/                               # module with many sub-feature plans
│   ├── design_app-ux.md
│   ├── plan_about-panel.md
│   ├── plan_arena.md
│   ├── plan_keyboard-shortcuts.md
│   ├── plan_theme-support.md
│   └── plan_user-feedback.md
├── workspace-packs/                      # module with one design + one plan
│   ├── design_workspace-packs.md
│   └── plan_workspace-packs.md
├── workspace-as-folder/                  # module with module-internal requirements
│   ├── requirements_workspace-as-folder.md
│   ├── design_workspace-as-folder.md
│   ├── plan_workspace-as-folder.md
│   ├── plan_file-preview-panel.md
│   └── plan_unify-file-click-behavior.md
└── opencode-integration/                 # module with a supporting API contract
    ├── design_opencode-integration.md
    ├── opencode-api.json
    └── plan_sidecar-opencode-rewrite.md
```

---

## 4. `kiro` Profile — Kiro IDE

Kiro organises specs as one folder per feature, each with three (or four) fixed-name markdown files.

### 4.1 Spec root

`<repo_root>/.kiro/specs/`. Optional steering docs live at `<repo_root>/.kiro/steering/`.

### 4.2 Folder + file rules

- One folder per feature: `.kiro/specs/<feature-name>/`.
- Feature folder names are **kebab-case** (e.g., `auth-flow/`, `team-invites/`).
- Files inside a feature folder use **fixed lowercase names**:
  - `requirements.md` — feature acceptance criteria. (For bugfix specs, `bugfix.md` replaces `requirements.md`.)
  - `design.md` — architecture and decisions for the feature.
  - `tasks.md` — implementation checklist.
- No `<artifact>_<topic>.md` pattern; the topic is encoded in the **folder name**.
- Steering docs at `.kiro/steering/`: `product.md`, `tech.md`, `structure.md` (optional).

### 4.3 Required artefacts

A complete feature spec has all three of `requirements.md` (or `bugfix.md`), `design.md`, `tasks.md`. A bugfix spec swaps `requirements.md` for `bugfix.md` but otherwise behaves the same.

### 4.4 Layer mapping

| Layer | File |
|---|---|
| Requirements | `<feature>/requirements.md` (or `<feature>/bugfix.md`) |
| Design | `<feature>/design.md` |
| Plan / tasks | `<feature>/tasks.md` |
| State | Task checkboxes inside `tasks.md` |
| Project context | `.kiro/steering/{product,tech,structure}.md` |

### 4.5 Anti-patterns

- Renaming the canonical files (`reqs.md`, `arch.md`, `todo.md`) — Kiro tooling reads the fixed names.
- camelCase or PascalCase feature folder names (`AuthFlow/` → `auth-flow/`).
- Putting design notes inside `requirements.md` or vice versa — each file has a defined role.
- Mixing `requirements.md` and `bugfix.md` in the same folder — pick one based on the spec type.

### 4.6 Example tree

```text
.kiro/
├── specs/
│   ├── auth-flow/
│   │   ├── requirements.md
│   │   ├── design.md
│   │   └── tasks.md
│   ├── team-invites/
│   │   ├── requirements.md
│   │   ├── design.md
│   │   └── tasks.md
│   └── login-button-bug/
│       ├── bugfix.md
│       ├── design.md
│       └── tasks.md
└── steering/
    ├── product.md
    ├── tech.md
    └── structure.md
```

---

## 5. `superpowers` Profile

Superpowers treats each plan as a single self-contained markdown file under a flat `plans/` directory.

### 5.1 Spec root

`<repo_root>/docs/superpowers/plans/`. (The path is conventional; some projects use `plans/` at the repo root.)

### 5.2 Folder + file rules

- All plans live in a single flat directory.
- Each plan filename is **`YYYY-MM-DD-<feature-name>.md`** — date prefix in ISO format, kebab-case feature slug.
- The plan file is self-contained — it includes the requirement summary, design notes, and task checklist inline.
- No separate `requirements.md` / `design.md` / `tasks.md`; all layers collapse into one document.

### 5.3 Required artefacts

One file per plan. The file is expected to contain inline sections for **Goal / Context**, **Design / Approach**, and **Tasks** (or equivalents).

### 5.4 Layer mapping

| Layer | Where it lives |
|---|---|
| Requirements | "Goal" / "Context" section inside the plan file |
| Design | "Approach" / "Design" section inside the plan file |
| Plan / tasks | "Tasks" / "Steps" section inside the plan file |
| State | Task checkboxes inside the same file |

Reverse-consistency checks degrade to **intra-document** checks: the plan file must contain task entries for each design item it lists, and each task should map to a stated goal. Cross-file coverage does not apply.

### 5.5 Anti-patterns

- Missing or non-ISO date prefix (`feature-x.md` → `2026-05-09-feature-x.md`).
- camelCase or snake_case in the slug (`2026-05-09-FeatureX.md` → `2026-05-09-feature-x.md`).
- Splitting one plan across multiple files in this directory — Superpowers expects one file per plan.
- Date that doesn't match the file's git history (drift between filename date and actual creation date).

### 5.6 Example tree

```text
docs/superpowers/
└── plans/
    ├── 2026-04-12-auth-flow.md
    ├── 2026-04-30-team-invites.md
    └── 2026-05-09-keyboard-shortcuts.md
```

---

## 6. `openspec` Profile

OpenSpec separates **source-of-truth specs** (the current product behaviour) from **change proposals** (in-flight work). Both live under a single `openspec/` root.

### 6.1 Spec root

`<repo_root>/openspec/`.

### 6.2 Folder + file rules

- **Specs (source of truth):** `openspec/specs/<domain>/spec.md`. One folder per product domain (`auth/`, `billing/`, `notifications/`); each contains a single `spec.md`.
- **Changes (proposals in flight):** `openspec/changes/<change-name>/` containing:
  - `proposal.md` — what changes and why.
  - `design.md` — architecture decisions for the change.
  - `tasks.md` — implementation checklist.
  - `specs/<domain>/spec.md` — the **proposed updated spec** for affected domains; merges into `openspec/specs/` when the change ships.
- **Archive:** completed changes are moved to `openspec/changes/archive/YYYY-MM-DD-<change-name>/...` (preserving the same internal layout).
- **Project context:** `openspec/AGENTS.md`, `openspec/project.md` (optional).
- Folder names are **kebab-case**; filenames are **fixed**.

### 6.3 Required artefacts

A change folder has at minimum `proposal.md` and `tasks.md`. `design.md` is required when the change introduces non-trivial architectural decisions. `specs/<domain>/spec.md` is required for every domain whose contract is changing.

### 6.4 Layer mapping

| Layer | Active change folder | Source of truth |
|---|---|---|
| Requirements | `changes/<change>/proposal.md` and `changes/<change>/specs/<domain>/spec.md` | `specs/<domain>/spec.md` |
| Design | `changes/<change>/design.md` | — |
| Plan / tasks | `changes/<change>/tasks.md` | — |
| State | Move to `changes/archive/YYYY-MM-DD-<change>/` when complete |

Reverse consistency:

- Each `changes/<change>/design.md` must cover everything in the same change's `proposal.md` and the diffs in its `specs/<domain>/spec.md`.
- Each `changes/<change>/tasks.md` must cover the design.
- After archive, `specs/<domain>/spec.md` should reflect what was proposed in the archived change.

### 6.5 Anti-patterns

- A change folder without a `proposal.md` — proposals are the entry point.
- Editing `openspec/specs/<domain>/spec.md` directly instead of via a change folder.
- Archive folders missing the `YYYY-MM-DD-` date prefix or using the wrong format.
- Domain folders under `specs/` that contain anything other than `spec.md` plus referenced assets.

### 6.6 Example tree

```text
openspec/
├── AGENTS.md
├── project.md
├── specs/
│   ├── auth/
│   │   └── spec.md
│   └── billing/
│       └── spec.md
└── changes/
    ├── add-passkey-support/
    │   ├── proposal.md
    │   ├── design.md
    │   ├── tasks.md
    │   └── specs/
    │       └── auth/
    │           └── spec.md
    └── archive/
        └── 2026-04-15-billing-tax-rules/
            ├── proposal.md
            ├── design.md
            ├── tasks.md
            └── specs/
                └── billing/
                    └── spec.md
```

---

## 7. `spec-kit` Profile — GitHub spec-kit

GitHub's spec-kit numbers each feature folder and uses a fixed set of artefact filenames.

### 7.1 Spec root

`<repo_root>/specs/`. Project-wide rules live at `<repo_root>/.specify/memory/constitution.md`.

### 7.2 Folder + file rules

- One folder per feature: `specs/###-feature-slug/`.
  - `###` is a zero-padded sequence number (`001`, `002`, …).
  - `feature-slug` is **kebab-case**.
  - Examples: `specs/001-create-taskify/`, `specs/002-realtime-collaboration/`.
- Files inside a feature folder are **fixed lowercase names**:
  - `spec.md` — feature spec (acceptance criteria, scope).
  - `plan.md` — implementation plan / architecture.
  - `research.md` — exploratory notes that informed the plan.
  - `data-model.md` — entities, schemas, and relationships.
  - `quickstart.md` — minimal walk-through for the feature.
  - `tasks.md` — implementation checklist (added late in the workflow).
  - `contracts/` — sub-folder of API or interface contracts (`*.openapi.yaml`, `*.proto`, etc.).
- Project rules: `.specify/memory/constitution.md` — project-wide principles that all specs must respect.

### 7.3 Required artefacts

Early-stage feature folders may have only `spec.md`. A complete feature folder has `spec.md`, `plan.md`, `data-model.md`, and `tasks.md`. `research.md`, `quickstart.md`, and `contracts/` are added as needed.

### 7.4 Layer mapping

| Layer | File |
|---|---|
| Project context | `.specify/memory/constitution.md` |
| Requirements | `specs/###-<slug>/spec.md` |
| Design | `specs/###-<slug>/plan.md`, `data-model.md`, `contracts/` |
| Plan / tasks | `specs/###-<slug>/tasks.md` |
| State | Task checkboxes inside `tasks.md` |
| Supporting research | `specs/###-<slug>/research.md`, `quickstart.md` |

Reverse consistency: `plan.md` + `data-model.md` + `contracts/` must collectively cover `spec.md`. `tasks.md` must cover everything in `plan.md`.

### 7.5 Anti-patterns

- Missing or non-numeric prefix (`feature-slug/` → `001-feature-slug/`).
- Non-padded numbers (`1-feature/` → `001-feature/`) — pick a width and stick to it (typically 3 digits).
- Reusing a number for two different features.
- camelCase / PascalCase / snake_case in the slug.
- Renaming the canonical files (`requirements.md` instead of `spec.md`, `architecture.md` instead of `plan.md`).
- Skipping `.specify/memory/constitution.md` — the constitution is the project-level guardrail spec-kit assumes is present.

### 7.6 Example tree

```text
.specify/
└── memory/
    └── constitution.md

specs/
├── 001-create-taskify/
│   ├── spec.md
│   ├── plan.md
│   ├── research.md
│   ├── data-model.md
│   ├── quickstart.md
│   ├── tasks.md
│   └── contracts/
│       └── tasks-api.openapi.yaml
└── 002-realtime-collaboration/
    ├── spec.md
    ├── plan.md
    └── data-model.md
```

---

## 8. `bmad` Profile — BMad Method

BMad separates **planning artefacts** from **implementation artefacts** and treats stories as the unit of execution.

### 8.1 Spec root

`<repo_root>/_bmad-output/`.

### 8.2 Folder + file rules

- **Planning artefacts:** `_bmad-output/planning-artifacts/`
  - `PRD.md` — product requirements document. (Note: **uppercase** by convention.)
  - `architecture.md` — system architecture. (Lowercase.)
  - `epics/` — folder of epic-level breakdowns; story files live here per epic, often as `epic-<n>-story-<m>.md` or similar.
- **Implementation artefacts:** `_bmad-output/implementation-artifacts/`
  - `sprint-status.yaml` — execution state across sprints.
  - Optional generated outputs (test reports, deployment logs).
- **Project context:** `_bmad-output/project-context.md` (optional, repo-wide context shared across PRD / architecture / epics).
- Folder names use **kebab-case**; filenames use the mixed casing shown above (`PRD.md` uppercase, `architecture.md` lowercase).

### 8.3 Required artefacts

A complete planning bundle has `PRD.md`, `architecture.md`, and at least one epic file under `epics/`. Implementation needs `sprint-status.yaml`. `project-context.md` is optional but recommended.

### 8.4 Layer mapping

| Layer | File |
|---|---|
| Project context | `_bmad-output/project-context.md` |
| Requirements | `_bmad-output/planning-artifacts/PRD.md` |
| Design | `_bmad-output/planning-artifacts/architecture.md` |
| Plan / tasks | Story files under `_bmad-output/planning-artifacts/epics/` |
| State | `_bmad-output/implementation-artifacts/sprint-status.yaml` |

Reverse consistency: `architecture.md` must cover the requirements in `PRD.md`. Stories under `epics/` collectively cover `architecture.md`. `sprint-status.yaml` references the active stories.

### 8.5 Anti-patterns

- Renaming `PRD.md` to lowercase or to `prd.md` — BMad tooling expects uppercase.
- Mixing planning and implementation artefacts in the same folder.
- Missing `sprint-status.yaml` while stories are in flight (state drift).
- Epic files outside the `epics/` folder.
- Multiple `PRD.md` files (BMad assumes one canonical PRD per output bundle).

### 8.6 Example tree

```text
_bmad-output/
├── project-context.md
├── planning-artifacts/
│   ├── PRD.md
│   ├── architecture.md
│   └── epics/
│       ├── epic-1-onboarding.md
│       ├── epic-1-story-1.md
│       └── epic-1-story-2.md
└── implementation-artifacts/
    └── sprint-status.yaml
```

---

## 9. `gsd` Profile — Get Shit Done

GSD uses a `.planning/` workspace with uppercase project-level docs and numbered phase folders. State is tracked explicitly in a top-level `STATE.md`.

### 9.1 Spec root

`<repo_root>/.planning/`.

### 9.2 Folder + file rules

- **Top-level core docs (uppercase):**
  - `PROJECT.md` — overall project description.
  - `REQUIREMENTS.md` — project requirements.
  - `ROADMAP.md` — phased plan of work.
  - `STATE.md` — current execution state across phases / tasks.
  - `config.json` — GSD configuration (optional).
- **Phase folders:** `.planning/phases/<NN>-<phase-slug>/`
  - `<NN>` is a zero-padded phase number (`01`, `02`, …).
  - `<phase-slug>` is kebab-case (e.g., `01-foundation/`, `02-auth/`).
  - Inside each phase folder, files use a numbered prefix:
    - `<NN>-RESEARCH.md` — phase-level research notes.
    - `CONTEXT.md` — context shared by tasks in the phase.
    - `<NN>-<TT>-PLAN.md` — task plan, where `<TT>` is the task number within the phase.
    - `<NN>-<TT>-SUMMARY.md` — task summary written after execution.
    - `<NN>-VERIFICATION.md` — phase-level verification report.
- Filenames are **uppercase** for the artefact type (`PLAN`, `SUMMARY`, `RESEARCH`, `VERIFICATION`, `CONTEXT`); the surrounding numbers are lowercase digits.

### 9.3 Required artefacts

Project level: `PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md`. Each phase: at least one `<NN>-<TT>-PLAN.md`. `CONTEXT.md`, `<NN>-RESEARCH.md`, `<NN>-VERIFICATION.md`, and `<NN>-<TT>-SUMMARY.md` are added through the phase lifecycle.

### 9.4 Layer mapping

| Layer | File |
|---|---|
| Project context | `.planning/PROJECT.md` |
| Requirements | `.planning/REQUIREMENTS.md` |
| Roadmap (high-level plan) | `.planning/ROADMAP.md` |
| Phase research | `.planning/phases/<NN>-*/<NN>-RESEARCH.md` |
| Phase context | `.planning/phases/<NN>-*/CONTEXT.md` |
| Task plan | `.planning/phases/<NN>-*/<NN>-<TT>-PLAN.md` |
| Task summary | `.planning/phases/<NN>-*/<NN>-<TT>-SUMMARY.md` |
| Phase verification | `.planning/phases/<NN>-*/<NN>-VERIFICATION.md` |
| State | `.planning/STATE.md` |

Reverse consistency:

- `ROADMAP.md` covers `REQUIREMENTS.md`.
- Each phase's task `*-PLAN.md` files collectively cover the phase's slot in `ROADMAP.md`.
- `STATE.md` references the currently active phase / task.
- A phase's `*-VERIFICATION.md` covers the tasks listed in that phase's `*-PLAN.md` files.

### 9.5 Anti-patterns

- Lowercase top-level docs (`requirements.md` → `REQUIREMENTS.md`).
- Missing or out-of-sync `STATE.md` while work is in flight.
- Phase folders without numeric prefix (`foundation/` → `01-foundation/`).
- Task files without phase + task number prefix (`PLAN.md` → `01-01-PLAN.md`).
- `*-SUMMARY.md` written before the corresponding `*-PLAN.md` is complete.
- Reusing a phase or task number across folders.

### 9.6 Example tree

```text
.planning/
├── PROJECT.md
├── REQUIREMENTS.md
├── ROADMAP.md
├── STATE.md
├── config.json
└── phases/
    ├── 01-foundation/
    │   ├── 01-RESEARCH.md
    │   ├── CONTEXT.md
    │   ├── 01-01-PLAN.md
    │   ├── 01-02-PLAN.md
    │   ├── 01-01-SUMMARY.md
    │   └── 01-VERIFICATION.md
    └── 02-auth/
        ├── 02-RESEARCH.md
        ├── CONTEXT.md
        └── 02-01-PLAN.md
```

---

## 10. Cross-Profile Layer Mapping

This is the same table viewed across all profiles, useful when a project mixes them or when migrating between them.

| Layer | `default` | `kiro` | `superpowers` | `openspec` | `spec-kit` | `bmad` | `gsd` |
|---|---|---|---|---|---|---|---|
| **Project context** | `requirements.md` (root) | `.kiro/steering/{product,tech,structure}.md` | — | `openspec/project.md` | `.specify/memory/constitution.md` | `_bmad-output/project-context.md` | `.planning/PROJECT.md` |
| **Requirements** | `requirements.md` / `requirements_<topic>.md` | `requirements.md` (or `bugfix.md`) | "Goal" section in plan file | `specs/<domain>/spec.md`, change `proposal.md` | `spec.md` | `PRD.md` | `REQUIREMENTS.md` |
| **Design / architecture** | `design.md` / `design_<topic>.md` | `design.md` | "Approach" section in plan file | `changes/<change>/design.md` | `plan.md`, `data-model.md`, `contracts/` | `architecture.md` | phase `*-PLAN.md` |
| **Plan / tasks** | `plan_<topic>.md` | `tasks.md` | "Tasks" section in plan file | `changes/<change>/tasks.md` | `tasks.md` | story files under `epics/` | numbered `*-PLAN.md` |
| **Execution state** | task checkboxes | task checkboxes inside `tasks.md` | task checkboxes inside plan file | archive folder `changes/archive/YYYY-MM-DD-<change>/` | task checkboxes inside `tasks.md` | `sprint-status.yaml` | `STATE.md`, `*-SUMMARY.md`, `*-VERIFICATION.md` |
| **Index / registry** | `index.md` (or `requirements.md` / `README.md`) | folder listing under `.kiro/specs/` | filename listing under `plans/` | `openspec/AGENTS.md` + folder listings | folder listing under `specs/` | bundle layout under `_bmad-output/` | `ROADMAP.md` + `STATE.md` |

When linting a multi-profile repo, run each profile's checks against its own root and emit findings tagged with the profile.

---

## 11. Customizing for a Project

The copy at `<spec_root>/meta/convention.md` is the **per-project source of truth**. Edit it freely:

- **Lock the active profile.** Set `active_profile:` in the frontmatter (e.g., `kiro`) to skip auto-detection.
- **Change spec root.** Spec-lint resolves the root from the README first; tighten this in your local copy if the default probe order is wrong.
- **Add allowed artifact types.** For the `default` profile, add (e.g.) `runbook_<topic>.md` or `adr_<topic>.md` to §3.2 / §3.3.
- **Tighten or relax topic-naming rules.** For example, ban abbreviations or require a glossary entry per topic.
- **Restrict module folder names.** For the `default` profile, fix the allowed list of module folders if you want a closed set.
- **Add project-specific anti-patterns.** Patterns you have seen in past reviews ("never put a screenshot inline; use `assets/`").
- **Drop profiles you do not use.** Trim §4-9 down to the profile(s) you want to enforce; spec-lint will only consider what the local copy describes.

When `spec-lint` runs and detects that the local copy differs from the bundled version, it surfaces an `info` finding so you can decide whether to refresh from the skill or keep your customizations.
