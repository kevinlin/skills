# Phase 3: Implementation Guide

This guide details the implementation phase — executing the plan phase-by-phase with verification at each step.

## Mindset: Plans are guides, not scripts

Follow the plan's intent, but use judgment when reality differs. The plan was written based on research, but codebases evolve and details can surprise you. When something doesn't match, communicate clearly rather than silently improvising.

## Getting started

1. **Read the plan fully** — no limit/offset. Understand the complete scope.
2. **Read the research document** and any referenced requirements.
3. **Check for existing checkmarks** (`- [x]`) — these indicate previously completed work. Trust them; pick up from the first unchecked item.
4. **Create a TodoWrite list** with tasks from the current phase.

If no plan path is provided, ask for one.

## Process

### 1. Execute one phase at a time

Focus on the current phase only:

- Make all changes specified for that phase
- Follow existing code patterns and conventions in the project
- Include tests alongside implementation
- Run quick spot checks as you go (does it compile? do basic tests pass?)
- Mark TodoWrite items complete as you finish them

### 2. Run automated verification

After completing a phase's changes, run every automated check from the plan's success criteria:

- Execute each command and verify it passes
- Fix all failures before proceeding — don't defer broken tests
- Use the Edit tool to check off passing items in the plan file (`- [ ]` → `- [x]`)

### 3. Pause for manual verification

After automated checks pass, stop and present this to the user:

```
Phase [N] Complete — Ready for Manual Verification

Automated checks passed:
- [List what passed]

Please perform the manual verification steps from the plan:
- [ ] [Manual step 1]
- [ ] [Manual step 2]

Let me know when manual testing is complete to proceed to Phase [N+1].
```

**Exceptions:**
- If the user asked you to do multiple phases (e.g., "implement phases 1-3"), skip intermediate pauses but still run automated verification for each phase. Pause after the last one.
- Don't check off manual verification items until the user confirms they pass.

### 4. Handle plan-reality mismatches

When the plan doesn't match what you find in the code:

```
Issue in Phase [N]:
Expected: [what the plan says]
Found: [actual situation]
Why this matters: [impact on the approach]

Options:
1. [Adaptation A]
2. [Adaptation B]

How should I proceed?
```

Don't improvise large deviations without approval. The plan was carefully designed — if something doesn't work, there's likely a reason worth discussing rather than silently working around.

Small, obvious adaptations (like a slightly different function name) are fine to handle without asking.

### 5. Manage context for long plans

For plans with 4+ phases, context windows fill up. After completing each phase:

- Add a brief implementation note to the plan file (what was done, any deviations)
- This creates a compact record that survives context compaction
- Future phases can load the plan and immediately see what happened

## Resuming interrupted work

If the plan has existing checkmarks:
- Trust that completed work is done — don't re-verify unless something seems wrong
- Pick up from the first unchecked item
- Read any implementation notes from previous phases to understand current state

## Common patterns

### Running verification commands

Use the project's own commands. Look for a Makefile, package.json scripts, or similar:

```bash
# Prefer project-level commands
make test          # or npm test, pytest, go test ./...
make lint          # or npm run lint, ruff check .
make build         # or npm run build, go build ./...
```

### Updating plan checkboxes

```markdown
# Before (use Edit tool):
- [ ] Tests pass: `make test`

# After:
- [x] Tests pass: `make test`
```

### Communicating progress

After each phase:
```
Phase [N] completed and verified.

Changes made:
- [Brief summary]

All automated checks passing. Ready for manual verification.
```

## Key principles

- **Read context fully before starting** — partial understanding leads to partial implementations
- **One phase at a time** — completing a phase before starting the next catches integration issues early
- **Fix failures immediately** — deferred failures compound and become harder to diagnose
- **Communicate mismatches** — the user's judgment matters more than your guesses about intent
- **Keep momentum** — balance thoroughness with forward progress
