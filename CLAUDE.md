# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **agent skills repository** — 9 self-contained skills that teach an AI coding agent (Claude Code/Cowork, Codex, Cursor, OpenCode, or any agent supporting the skills format) how to do one software-delivery job well. It is not an application: no root build system, no package manager, no top-level test suite. Individual skills ship their own helper scripts.

`README.md` is the authoritative human catalogue — it lists all 9 skills grouped by delivery phase (Bid/Discover/Design, Build, Review/Verify, Maintain, Communicate/Deliver, Measure). Read it before assuming what a skill does.

## Skill Anatomy

Each skill lives in its own top-level directory and follows the same shape:

- `SKILL.md` — the authoritative skill definition the agent loads. Changing it directly changes agent behavior when the skill triggers.
- `README.md` — human documentation (where present).
- `references/` — checklists, catalogues, templates the skill loads on demand.
- `agents/` — sub-agent definitions, for skills that fan out work (`research-plan-implement`, `code-review-expert`).
- `scripts/` — helper scripts the skill runs instead of improvising.
- `tests/` — fixture generators (e.g. `make_fixtures.py` in `agent-insights`).

### SKILL.md frontmatter

YAML frontmatter carries `name`, `description` (the trigger text — the agent matches user requests against it), and `metadata.version`. Some skills add `blob_files:` listing binary assets shipped with the skill.

## Versioning invariant

Two places record every skill's version and must stay in sync:

1. `metadata.version` in the skill's `SKILL.md` frontmatter.
2. The skill's entry in [versions.json](versions.json) (the latest-version manifest).

When you change a skill's behavior, bump both. `versions.json` is how an installed copy checks whether it is current.

## Scripts

Several skills carry real helper scripts — the repo is not script-free:

- **Python** — `agent-insights/scripts/agent_insights.py`, `declawed/scripts/scan.py`, `research-plan-implement/scripts/spec_metadata.sh` (git metadata for frontmatter), and the `architecture-diagram/scripts/` pair (`build_gallery.py` regenerates the style gallery, `html_to_png.py` renders a diagram to PNG via a headless browser).

Skills declare no dependency manifests (no root `requirements.txt` / `package.json`) — scripts rely on the interpreter's standard library.

## Repository conventions

- **`*-workspace/` directories** (e.g. `agent-insights-workspace/`, `gap-analysis-workspace/`) are gitignored skill-creator evaluation workspaces. They are not skills — don't document, ship, or edit them as such.
- **`*.zip`** files are packaged skills (gitignored) for drag-and-drop into the Claude desktop app.
- **`assets/`** holds shared repo assets (the README hero diagram + its HTML source).

## Key patterns across skills

- **Approval gates** — multi-stage skills (`spec-coding`, `research-plan-implement`) require human approval between phases; the agent must not run ahead.
- **Sub-agents** — `research-plan-implement` fans out six specialized agents (codebase-locator/-analyzer/-pattern-finder, thoughts-locator/-analyzer, web-search-researcher) for parallel investigation.
- **Frequent Intentional Compaction (FIC)** — `research-plan-implement` front-loads understanding into markdown artifacts that carry context across sessions instead of bloating the conversation.
- **Output artifacts** — skills produce structured markdown/HTML (specs, plans, gap registers, reports) as the durable handoff between phases and sessions.
- **Local-only data** — the Measure skill (`agent-insights`) reads local session logs and emits local output; it sends nothing anywhere.

## Editing Guidelines

- `SKILL.md` is the source of truth for behavior — edit it deliberately and bump the version in both places.
- Keep `references/` documents focused and structured; skills load them as context.
- When editing a skill, mirror its existing conventions rather than the repo average — skills vary intentionally (some fan out sub-agents, some run scripts, some are pure prose).
