---
name: agent-insights
description: Generate a cross-tool usage insights report from locally stored AI coding agent sessions (Claude Code, Claude Cowork, GitHub Copilot for VS Code/CLI/JetBrains, Cursor, Codex, Kiro, Antigravity, OpenCode) over the last N days, default 30. Use when the user invokes /agent-insights, asks for insights, analytics, or a report on their agent sessions, asks how they're using their coding agents or what's working or causing friction, wants to compare their coding agent tools, or asks what their AI coding patterns look like, even when they don't say "report".
metadata:
  version: 1.6.0
---

# agent-insights

Cross-tool version of Claude Code's builtin `/insights`. Everything runs locally;
no session data leaves the machine.

`SKILL_DIR` below means this skill's directory; `SCRIPT` means
`python3 <SKILL_DIR>/scripts/agent_insights.py`. All intermediate files live in
`~/.agent-insights/` (override with `--data-dir` on every subcommand, e.g. for tests).

## Arguments

One optional argument: number of days to analyze. Default 30, clamp to 1..365.
Non-numeric input: tell the user, then proceed with 30.

## Pipeline

### Step 0 — Detect runtime

```bash
SCRIPT detect
```

Detects whether this skill is running on the host machine (where the user's agent logs
live) or inside a **sandboxed runtime** such as Claude Cowork, whose Bubblewrap container
does not mount the host filesystem. Reads the JSON result:

- If `sandboxed` is `false`, continue to Step 1.
- If `sandboxed` is `true`, the host machine's agent log directories are **not reachable**
  from this runtime. Do **not** run a full report from here: it would be empty or cover
  only the sandbox's own session. Instead, tell the user:
  - the detected `runtime` and `confidence`, and the `signals` that fired;
  - the `recommendation` verbatim (run `/agent-insights` from a non-sandboxed agent with
    direct host access, e.g. Claude Code in the terminal);
  - `reachable_sources` (what little, if anything, is visible from inside the sandbox).

  Then stop, unless the user explicitly asks to analyze only what is reachable inside the
  sandbox — only then proceed to Step 1.

### Step 1 — Scan

```bash
SCRIPT scan --days <N>
```

Discovers sessions across all supported tools, filters to the window, dedupes,
drops non-substantive sessions (no user messages or < 1 active minute) and prior
insight-analysis sessions, caches per-session metadata, and prepares truncated
transcripts for sessions that don't have cached facets yet (max 50 per run; re-runs
only pay for new sessions).

Output (stdout JSON): `runtime` (same shape as Step 0, repeated here as a safety net),
`sources_detected`, `sessions_kept`, `per_tool`, `facet_extractions_needed`,
`facet_extractions_deferred` (uncached sessions beyond the 50-per-run cap), and
`batches` (each with `transcript_files` and an `output_file`).

- Exit code 2 with an error message means zero sessions were found across every
  source. Report that to the user and stop; nothing to analyze. If the error's
  `runtime.sandboxed` is true, the cause is the sandboxed runtime (Step 0) — relay its
  `recommendation` instead of a generic "no sessions" message.
- Tell the user what was detected (tools + session counts) before continuing.

### Step 2 — Facet extraction (skip when `facet_extractions_needed` is 0)

Read `<SKILL_DIR>/references/prompts.md` (section 1) for the facet extraction prompt.

**If the running agent supports subagents** (e.g. Claude Code's Task tool, Cursor):
spawn one general-purpose subagent **per batch, all in parallel in a single message**.
Each subagent prompt must contain:

1. The facet extraction prompt from prompts.md, verbatim.
2. The batch's `transcript_files` list. Each file starts with a `=== SESSION <session_key> ===` header.
3. Output instructions: read every transcript file; write ONE JSON array to the batch's
   `output_file` (use the Write tool), where each element is
   `{"session_key": "<from the file header>", "facets": {<facet object per the schema>}}`;
   return only a count of sessions processed.

**If the running agent does not support subagents** (e.g. OpenCode): do NOT attempt a
parallel subagent run. Process the batches yourself in the main context, **one batch at
a time, sequentially**: for each batch, read its transcript files, apply the facet
extraction prompt, and write the same JSON array (shape as in item 3 above) to the
batch's `output_file` before moving on to the next batch.

In either mode, if a batch fails or produces invalid JSON, retry it once; on second
failure continue without that batch (those sessions still count in the deterministic
stats).

### Step 3 — Aggregate

```bash
SCRIPT aggregate --days <N> --analysis-model "<your model id>"
```

Pass `--analysis-model` with the model **you** (the main agent running this skill) are
currently executing as. Use the base model id without context-window or runtime suffixes
(e.g. `claude-opus-4-8`, not `claude-opus-4-8[1m]`). This records which model produced the
analysis (facets + narrative) so reports can be benchmarked against an agreed standard
model. It is the analyzing model, distinct from the per-session models found in the scanned
logs. If you genuinely cannot determine your own model id, omit the flag (it records
`unknown`).

Validates and ingests the facet batch files into the cache, then merges all cached
sessions in the window into `~/.agent-insights/aggregate.json` (also printed to stdout):
`version` (the skill's `metadata.version`), `analysis_model`, totals (incl. total
`skill_invocations`), per-tool breakdown (sessions, messages, hours, tool calls, skill
invocations, models used),
goal/outcome/satisfaction/friction/expertise_level/model/skills_used distributions, and
`narrative_context` (session briefs + friction details) for the next step. Skill
invocations are counted deterministically during the scan (no facet extraction): the
`Skill` tool in Claude Code / Cowork logs, plus leading `/name` slash commands in Cursor
and OpenCode user messages (where skills are invoked as slash commands). Names merge
across tools, so `/spec-lint` and the `spec-lint` skill count as one.

If the scan reported `facet_extractions_deferred` > 0, only part of the window has
facets. Loop Steps 1-3 until deferred is 0 — each round's scan prepares batches for
the next 50 uncached sessions (already-cached ones cost nothing) — so the narrative
is grounded in the full window. Then continue.

### Step 4 — Narrative

Read `<SKILL_DIR>/references/prompts.md` (section 2) and follow it: it defines every
narrative section's key and shape, plus the grounding rules. Using the aggregate
output from Step 3, write ALL of those sections to `narrative.json` in the data dir
(`~/.agent-insights/narrative.json` unless `--data-dir` was overridden). Also set a
top-level `version` key, copied from the aggregate's `version` value, so the narrative
file records the skill release that produced it.

### Step 5 — Render

```bash
SCRIPT render
```

Produces a self-contained HTML report at
`~/.agent-insights/report-YYYY-MM-DD_<days>-days.html`, where `<days>` is the analyzed
window taken from the aggregate (file mode 0600; it contains transcript snippets). The
report header shows the skill `version` (read from the aggregate). Prints the path.

### Step 6 — Tell the user

Output, in this order:

1. A stats line: `N sessions · N user messages · Nh · across <tools detected>` plus the
   date range.
2. The At a Glance summary: the `persona` one-liner from `at_a_glance` first
   ("You are a <level> <user_type>."), then the four parts as short markdown
   sections: What's working / What's hindering you / Quick wins / Ambitious workflows.
3. The report path, suggesting `open <path>` to view it.
4. One line inviting the user to dig into any section.

## Notes

- The scan prints adapter warnings to stderr; surface them to the user only if a tool
  they expected is missing from `sources_detected`.
- Storage locations, format details, and parsing caveats per tool:
  `<SKILL_DIR>/references/data-sources.md` (read when debugging a missing/empty source).
- Requires Python 3 (stdlib only). If `python3` is unavailable, stop and tell the user.
