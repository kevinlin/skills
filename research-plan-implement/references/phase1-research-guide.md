# Phase 1: Research Guide

This guide details the research phase — systematically exploring the codebase and documenting what you find.

## Mindset: Document, don't evaluate

Your job in this phase is to create a technical map of the relevant code. Describe what exists, where it lives, how it works, and how components connect. Save opinions, recommendations, and improvement ideas for the planning phase — mixing them in here muddies the research with premature conclusions.

This applies to you and all sub-agents you spawn.

## Process

### Step 1: Read user-mentioned files first

If the user references specific files, tickets, or documents, read them fully before doing anything else. Use the Read tool without `limit`/`offset` — partial reads miss important context that shapes the entire research direction.

Why this matters: these files contain the user's framing of the problem. Spawning sub-agents before understanding the user's perspective leads to unfocused exploration.

### Step 2: Decompose the research question

Break the user's query into distinct areas to investigate:

- Identify the components, patterns, or systems involved
- Consider how they might connect or interact
- Create a TodoWrite list to track each research area
- Decide which areas can be explored in parallel

### Step 3: Investigate the codebase

Spawn sub-agents scaled to the task's complexity (see "Adaptive Sub-Agent Usage" in SKILL.md). Key guidelines:

- **Start with locators** to find what exists, then use analyzers on the most promising findings
- **Run agents in parallel** when they're searching for different things
- **Keep prompts focused** — tell each agent what you're looking for, not how to search (they know their tools)
- **Remind agents to document, not evaluate** — they should describe what they find without suggesting changes

For tasks that also need external context (API docs, framework guides), use the **web-search-researcher** agent and ask it to include source links.

### Step 4: Synthesize findings

Wait for all sub-agents to complete before synthesizing — partial synthesis leads to incomplete or skewed conclusions.

When compiling results:
- Prioritize live codebase findings as the source of truth
- Include specific `file:line` references for all significant findings
- Connect findings across components to show how systems interact
- Note any gaps or areas that need further investigation

### Step 5: Gather metadata

Run the metadata script to collect git and date information:

```bash
<skill-path>/scripts/spec_metadata.sh
```

This collects: current datetime, git commit hash, branch name, repository name, and a filename-safe timestamp.

### Step 6: Generate the research document

Write a structured markdown document. Choose a sensible location based on the project's conventions (e.g., a `docs/research/` directory, or alongside related documentation).

**Filename format**: `YYYY-MM-DD-[ticket]-description.md`
- Include ticket number if one exists, omit if not
- Use kebab-case for the description portion

**Document structure**:

```markdown
---
date: [datetime with timezone]
researcher: [name or "AI"]
git_commit: [commit hash]
branch: [branch name]
repository: [repo name]
topic: "[research topic]"
tags: [research, relevant-component-names]
status: complete
---

# Research: [Topic]

## Research Question

[Original user query]

## Summary

[High-level findings answering the user's question]

## Detailed Findings

### [Component/Area 1]
- What it does and how it works ([file.ext:line](path))
- How it connects to other components

### [Component/Area 2]
...

## Code References

- `path/to/file.py:123` — What's there
- `another/file.ts:45-67` — What the code block does

## Architecture Notes

[Patterns, conventions, and design decisions found in the codebase]

## Open Questions

[Areas that need further investigation, if any]
```

### Step 7: Add permalinks (if applicable)

If on the main branch with commits pushed to a remote, replace local file references with GitHub/GitLab permalinks where appropriate.

### Step 8: Present findings

Share a concise summary with the user:
- Highlight the most important discoveries
- Include key file references for easy navigation
- Ask if they have follow-up questions

### Step 9: Handle follow-ups

If the user asks follow-up questions:
- Append to the same research document (don't create a new one)
- Add a `## Follow-up: [topic]` section
- Update the frontmatter `last_updated` field
- Spawn additional sub-agents as needed

## Guidelines

### Ordering matters

The step order exists for good reasons:
1. Read mentioned files first → gives you context to decompose well
2. Decompose before spawning agents → focused agents produce better results
3. Wait for all agents before synthesizing → avoids premature conclusions
4. Gather metadata before writing → no placeholder values in the document

### Path handling for thoughts/ directories

If the project uses a `thoughts/searchable/` directory (a read-only search mirror), strip only the `searchable/` segment from paths — preserve everything else:
- `thoughts/searchable/shared/research/api.md` → `thoughts/shared/research/api.md`
- `thoughts/searchable/{username}/notes.md` → `thoughts/{username}/notes.md`

### Keep the main agent focused on synthesis

Sub-agents do the deep file reading. The main agent's context budget is best spent on connecting findings, identifying patterns, and writing the research document — not on reading dozens of files directly.
