# Phase 2: Planning Guide

This guide details the planning phase — transforming research findings into an actionable implementation plan through interactive collaboration with the user.

## Mindset: Plans are executable specifications

A good plan is precise enough that someone (or an AI agent) could implement it without asking clarifying questions. Every decision should be made, every file change identified, every success criterion testable. If you catch yourself writing "TBD" or "decide later", stop and resolve it now.

## Process

### Step 1: Load context and verify understanding

1. **Read the Phase 1 research document fully** — no limit/offset. This is your foundation.

2. **Read any other referenced files** — tickets, requirements, related documents.

3. **If gaps exist**, spawn targeted sub-agents to fill them. Use the same agent types from Phase 1, focused on specific unknowns.

4. **Present your understanding** to the user:
   ```
   Based on the research, I understand we need to [summary].

   Key findings relevant to planning:
   - [Finding with file:line reference]
   - [Constraint or pattern discovered]

   Questions that need human judgment:
   - [Specific question that code can't answer]
   ```

   Only ask questions you genuinely can't resolve by reading code.

### Step 2: Design interactively

Planning is a conversation. Don't write a full plan in one shot — iterate on the approach first:

1. **If the user corrects a misunderstanding**, verify the correction in the codebase before proceeding. Don't just accept corrections blindly — trust but verify.

2. **Present design options** with concrete pros and cons grounded in what the research found.

3. **Get alignment on approach** before committing to details — changing direction after writing a detailed plan wastes time.

4. **Propose a phase structure**:
   ```
   Proposed phases:
   1. [Phase name] — [what it accomplishes]
   2. [Phase name] — [what it accomplishes]
   3. [Phase name] — [what it accomplishes]

   Does this ordering and granularity make sense?
   ```

### Step 3: Write the plan

Once the user approves the structure, write the detailed plan. Save it alongside the research document or in the project's preferred location.

**Filename format**: `YYYY-MM-DD-[ticket]-description.md` (same convention as research docs)

**Plan template**:

````markdown
# [Feature/Task Name] Implementation Plan

## Overview

[What we're implementing and why, in 1-2 sentences]

## Current State

[What exists now, based on research. Key constraints and patterns to work within.]

## Desired End State

[What the system should look like after implementation. How to verify it.]

## What We're NOT Doing

[Explicitly out-of-scope items — prevents scope creep during implementation]

## Implementation Approach

[High-level strategy and reasoning for the chosen approach]

## Phase 1: [Descriptive Name]

### Overview
[What this phase accomplishes and why it comes first]

### Changes Required

#### 1. [Component/File]
**File**: `path/to/file.ext`
**Changes**: [Summary of what changes and why]

```[language]
// Key code to add/modify (when specificity helps)
```

### Success Criteria

#### Automated Verification
- [ ] Tests pass: `[project test command]`
- [ ] Build succeeds: `[project build command]`
- [ ] Linting clean: `[project lint command]`

#### Manual Verification
- [ ] [Observable behavior to check]
- [ ] [Edge case to test manually]

**After automated verification passes, pause for manual confirmation before proceeding.**

---

## Phase 2: [Descriptive Name]

[Same structure...]

---

## Testing Strategy

### Automated Tests
- [What to test and key edge cases]

### Manual Testing
1. [Specific verification step]
2. [Another step]

## Migration Notes

[If applicable — how to handle existing data, backwards compatibility, etc.]

## References

- Research document: `[path]`
- Related files: `[key files with line references]`
````

### Step 4: Review and iterate

1. **Present the plan location** and ask for review:
   ```
   Plan created at [path].

   Please review:
   - Are the phases properly scoped?
   - Are success criteria specific enough?
   - Any missing edge cases?
   ```

2. **Incorporate feedback** — add phases, adjust approach, clarify criteria as needed.

3. **Continue until the user is satisfied** with the plan.

## Guidelines

### Separate automated from manual verification

This separation matters because automated checks can be run by the implementation agent independently, while manual checks require the user to pause and test. Mixing them creates ambiguity about when to pause.

**Automated**: commands that produce pass/fail output (`make test`, `npm run lint`, `go vet ./...`)
**Manual**: things requiring human judgment (UI behavior, performance feel, UX quality)

Use whatever test/build/lint commands the project already uses — don't prescribe specific tooling.

### Resolve all open questions

A plan with unresolved questions forces the implementation agent to guess, and guesses compound into costly rework. If you hit an unknown:
- Research it (spawn a sub-agent if needed)
- Ask the user for a decision
- Don't proceed until it's resolved

### Be skeptical but practical

- Question vague requirements — "improve performance" isn't actionable
- Identify risks and edge cases early
- But don't over-engineer: match the plan's complexity to the task's actual complexity
- Include "What We're NOT Doing" to set clear boundaries

### Common phase patterns

**Database changes**: Schema/migration → Store methods → Business logic → API → Client
**New features**: Data model → Backend logic → API endpoints → UI
**Refactoring**: Document current behavior → Incremental changes → Maintain compatibility
