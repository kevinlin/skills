# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **agent skills repository**: 10 self-contained skills that each teach an AI coding agent (Claude Code/Cowork, Codex, Cursor, OpenCode, or any agent supporting the skills format) how to do one software-delivery job well. It is not an application: no root build system, no package manager, no top-level test suite. Individual skills ship their own helper scripts and eval suites.

- [versions.json](versions.json) is the complete list of skills.
- `README.md` is the human catalogue, grouped by delivery phase (Bid/Discover/Design, Build, Review/Verify, Maintain, Communicate/Deliver, Measure). Read it before assuming what a skill does.

The repo is public (github.com/kevinlin/skills), and its history is too. Nothing client-identifying goes in: no client names, documents, recordings or colleague names, in skills or in fixtures.

## Skill Anatomy

Each skill lives in its own top-level directory and follows the same shape:

- `SKILL.md`: the authoritative skill definition the agent loads. Changing it directly changes agent behavior when the skill triggers.
- `README.md`: human documentation (where present).
- `references/`: checklists, catalogues, templates the skill loads on demand.
- `agents/`: sub-agent definitions, for skills that fan out work (`research-plan-implement`, `code-review-expert`).
- `scripts/`: helper scripts the skill runs instead of improvising.
- `evals/`: the skill's eval suite (see below).
- `tests/`: unit checks or fixture generators (`meeting-recap/tests/test_*.py`, `agent-insights/tests/make_fixtures.py`).

### SKILL.md frontmatter

YAML frontmatter carries `name`, `description` (the trigger text; the agent matches user requests against it), and `metadata.version` (under `metadata`, not top level). Some skills add `blob_files:` listing binary assets shipped with the skill.

## Versioning invariant

Two places record every skill's version and must stay in sync:

1. `metadata.version` in the skill's `SKILL.md` frontmatter.
2. The skill's entry in [versions.json](versions.json) (the latest-version manifest).

When you change a skill's behavior, bump both. `versions.json` is how an installed copy checks whether it is current.

Commit messages follow `<skill> vX.Y.Z - <What changed>` for a release, or `<skill> - <What changed>` when the version doesn't move.

### Adding or removing a skill

Besides `versions.json`, three more places list skills explicitly and must be edited on add/remove (not on version bumps):

- `skills` array in `.claude-plugin/marketplace.json` (and the skill count in its `description`).
- `groupings` in `skills.sh.json` (the skills.sh catalogue grouping, by delivery phase).
- `README.md` catalogue, plus the skill count in this file.

### Twin repo

Most skills here are synced from `../zapac-agent-skills`, which is the working copy where skills are developed. Changes usually land there first and are copied here (commits say "Sync from zapac-agent-skills"). Some skills have drifted between the two (e.g. `html-diagram`), so diff before copying whole files, and strip anything client-identifying on the way in.

## Plugin distribution

The repo doubles as a Claude Code plugin marketplace. Two manifests live in `.claude-plugin/` (see the [plugin-marketplaces guide](https://code.claude.com/docs/en/plugin-marketplaces)):

- `marketplace.json`: catalog `ai-sdlc` with one plugin entry, `ai-sdlc-skills`. It uses `source: "./"` plus an explicit `skills` array listing every skill directory, rather than the default `skills/` scan. A new top-level skill directory won't ship through the plugin until it's listed there.
- `plugin.json`: plugin metadata (author, homepage, license). It carries no `version` on purpose: the plugin is git-hosted, so every commit counts as a new version (SHA-driven updates). A pinned `version` would have to be bumped on every release or installed copies never update.

Validate manifest changes with `claude plugin validate .` from the repo root. The no-version warning is expected; treat anything else as a real error.

## Evals and tests

Every skill except `code-review-expert` has an `evals/` suite:

- `eval.yaml`: the suite. Its header comment maps each behavior claimed by `SKILL.md` to the case that covers it. Keep that map current when you change behavior.
- `cases/*.yaml`: one case per scenario.
- `fixtures/`: synthetic workspaces plus judges (`scripts/judge_*.py` or `scripts/assert-*.sh`). Judges run the way skill-up runs them: copied into a temp dir as a file named `script`, with the case workspace as cwd and the agent's final reply in `EVAL_FINAL_MESSAGE`.

Judge self-tests (good and bad workspaces through every judge, prints `ok`):

```
python3 gap-analysis/evals/fixtures/scripts/selftest.py
bash meeting-recap/evals/fixtures/scripts/selftest.sh   # drives selftest.py; don't run that directly
```

Some fixtures are generated: `gap-analysis/evals/fixtures/build_fixtures.py` and `meeting-recap/evals/fixtures/build_manifests.py`. Self-tests run them with `--check`, so a stale fixture fails the self-test; regenerate after changing a builder.

Unit checks are plain scripts, no test runner:

```
python3 meeting-recap/tests/test_diarize.py
python3 meeting-recap/tests/test_check_recap.py
```

Eval suites should set `CLAUDE_CONFIG_DIR: .eval-claude-config` in `eval.yaml` so the eval agent doesn't load the operator's `~/.claude` config and skills. Only `gap-analysis` and `html-diagram` do so far.

`.gitignore` excludes `.claude/` but re-includes `*/evals/fixtures/**/.claude/`, so synthetic session fixtures are committed. Check `git status` after adding fixtures under a dot-directory.

## Scripts

Scripts use only the interpreter's standard library; no skill declares a dependency manifest. Notable ones:

- `agent-insights/scripts/agent_insights.py`: builds the usage report from local session logs.
- `declawed/scripts/scan.py`: mechanical scan for the tell catalogue.
- `research-plan-implement/scripts/spec_metadata.sh`: git metadata for spec frontmatter.
- `html-diagram/scripts/`: `build_gallery.py` regenerates the style gallery; `html_to_png.py` renders a diagram to PNG.
- `meeting-recap/scripts/`: `diarize.py` drives the local transcription pipeline, `check_recap.py` runs the mechanical recap checks, `build_html.py` and `svgkit.py` build the HTML companion and figures.

Exceptions to stdlib-only:

- `meeting-recap/scripts/embed.py` runs inside the separately installed MOSS venv (torch + speechbrain); `diarize.py` stays stdlib and shells out to it.
- `html-diagram/scripts/html_to_png.py` needs Playwright + Chromium (`pip install playwright && playwright install chromium`).

## Repository conventions

- **`*-workspace/` directories** are gitignored skill-creator evaluation workspaces. They are not skills: don't document, ship, or edit them as such.
- **`*.zip`** files are packaged skills (gitignored) for drag-and-drop into the Claude desktop app.
- **`AGENTS.md`** is a gitignored symlink to this file for other agents.
- **`assets/`** holds shared repo assets (the README hero diagram + its HTML source).
- PRs from contributors use Conventional Commits titles (squash-merged); see `CONTRIBUTING.md`. CI only runs dependency review and OpenSSF Scorecard, nothing skill-specific.

## Key patterns across skills

- **Approval gates**: multi-stage skills (`spec-coding`, `research-plan-implement`) require human approval between phases; the agent must not run ahead. Word a new gate for the one transition it guards, or it blocks users who enter at a later phase.
- **Sub-agents**: `research-plan-implement` fans out six specialized agents (codebase-locator/-analyzer/-pattern-finder, thoughts-locator/-analyzer, web-search-researcher) for parallel investigation.
- **Frequent Intentional Compaction (FIC)**: `research-plan-implement` front-loads understanding into markdown artifacts that carry context across sessions instead of bloating the conversation.
- **Output artifacts**: skills produce structured markdown/HTML (specs, plans, gap registers, reports) as the durable handoff between phases and sessions.
- **Local-only data**: `agent-insights` reads local session logs and emits local output; it sends nothing anywhere.

## Editing Guidelines

- `SKILL.md` is the source of truth for behavior. Edit it deliberately and bump the version in both places.
- A rule that only lives in a `references/` doc can be missed; if the agent must always follow it, state it in `SKILL.md`.
- Keep `references/` documents focused and structured; skills load them as context.
- When editing a skill, mirror its existing conventions rather than the repo average. Skills vary on purpose (some fan out sub-agents, some run scripts, some are pure prose).
