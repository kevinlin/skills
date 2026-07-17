---
name: code-review-expert
version: 1.0.0
description: "Expert code review with a senior engineer lens — covers architecture, SOLID principles, security vulnerabilities, performance, error handling, testing gaps, and API contract changes. Use this skill whenever the user asks to review code, check changes, audit a diff, look over a PR, find bugs in their work, or wants feedback on code quality. Also trigger when the user says things like 'review my changes', 'check this before I push', 'what do you think of this code', 'any issues with this?', 'code review', 'look this over', or 'is this ready to merge'. Works with any programming language and any size of change."
---

# Code Review Expert

## Overview

Perform a structured, senior-engineer-level review of code changes. Adapt your depth and focus based on what actually changed — a 5-line bug fix gets a focused review, while a 500-line feature branch gets a broader architectural pass.

Default to review-only output. Do not implement fixes unless the user explicitly asks.

## Severity Levels

| Level | Name | Description | Action |
|-------|------|-------------|--------|
| **P0** | Critical | Security vulnerability, data loss risk, correctness bug | Must fix before merge |
| **P1** | High | Logic error, major design issue, performance regression | Should fix before merge |
| **P2** | Medium | Code smell, maintainability concern, missing tests | Fix now or create follow-up |
| **P3** | Low | Style, naming, minor suggestion | Optional improvement |

## Workflow

### 1. Scope the changes

Determine what's being reviewed:

- **Default (unstaged + staged changes)**: Run `git diff --stat` and `git diff` to see what changed. If empty, check staged changes with `git diff --cached --stat` and `git diff --cached`. If still empty, ask the user what they want reviewed.
- **Specific files or commits**: If the user points to files or a commit range, scope to that.
- **Branch/PR review**: If the user mentions a PR or branch, diff against the target branch (e.g., `git diff main...HEAD`).

Use the Grep and Glob tools to find related code, callers, and contracts when you need more context around the changes.

**Adapt review depth to change size:**

- **Small (< 50 lines)**: Review everything in detail, check surrounding context for ripple effects.
- **Medium (50-300 lines)**: Group by logical area, prioritize critical paths (auth, data, money).
- **Large (300+ lines)**: Summarize by file/module first, then deep-dive on high-risk areas. Tell the user what you focused on and what you skimmed.

### 2. Focus on what matters

Before working through checklists, consider what kind of code changed and prioritize accordingly:

- **Auth, payments, data writes, network boundaries** → Security is top priority. Load `references/security-checklist.md`.
- **Business logic, algorithms, data transformations** → Correctness and edge cases. Load `references/code-quality-checklist.md`.
- **Class/module restructuring, new abstractions** → Design principles. Load `references/solid-checklist.md`.
- **Config, infrastructure, CI/CD** → Secrets exposure, permission changes, unintended side effects.
- **Tests only** → Test quality, coverage gaps, flaky patterns.

Only load reference files relevant to the changes. A CSS tweak doesn't need the security checklist. A one-line fix doesn't need SOLID analysis.

### 3. Review the code

Work through these areas based on relevance — not every review needs every section:

**Correctness & Logic**

- Does the code do what it claims? Follow the logic path end-to-end.
- Edge cases: null/empty inputs, zero/negative values, boundary conditions, concurrent access.
- Error handling: are failures caught at the right level? Are errors informative, not swallowed or leaking internals?

**Security** (especially for code touching auth, user input, data, or network)

- Load `references/security-checklist.md` for detailed checks.
- Injection (SQL, command, template), XSS, SSRF, path traversal.
- Auth/authz gaps, missing tenant checks, secrets in code or logs.
- Race conditions in concurrent or distributed code.

**Design & Architecture**

- Load `references/solid-checklist.md` when reviewing structural changes.
- Is the code in the right place? Does it respect existing module boundaries?
- Are abstractions earned (solving a real problem) or speculative?
- Will this be straightforward to modify when requirements change?

**Performance**

- N+1 queries, unbounded loops or collections, missing pagination.
- Expensive operations in hot paths (regex compilation in loops, repeated parsing).
- Memory: unbounded growth, large object retention, loading entire files into memory.

**Testing**

- Do the changes include tests? New logic and bug fixes should have them.
- Do existing tests still make sense after the changes?
- Are there important code paths that aren't tested?
- Test quality: are assertions meaningful, or do tests just confirm the code runs?

**API & Contract Changes**

- Breaking changes to public APIs, interfaces, shared types, or data formats?
- Backwards compatibility: will existing callers, clients, or consumers break?
- Are changes documented where needed (changelog, migration notes)?

**Dead Code** (flag only what you spot — don't hunt for it)

- Code made unreachable by this change.
- Unused imports, variables, or functions introduced or left behind.
- If removal is non-trivial, reference `references/removal-plan.md` for a structured approach.

### 4. Present findings

Structure your review like this:

```markdown
## Code Review Summary

**Scope**: X files, Y lines changed
**Assessment**: [APPROVE / REQUEST_CHANGES / COMMENT]

---

## Findings

### P0 - Critical
(none or list)

### P1 - High
1. **[file:line]** Brief title
   - What's wrong and why it matters
   - Suggested fix

### P2 - Medium
2. **[file:line]** Brief title
   - ...

### P3 - Low
...

---

## Testing Gaps
(if applicable — what should be tested but isn't)

## Additional Notes
(optional — context, patterns observed, things worth monitoring)
```

**When everything looks good**: Don't just say "LGTM." State what you checked, note areas you couldn't fully verify, and mention any risks worth monitoring post-merge.

### 5. Offer next steps

After presenting findings, ask how to proceed:

```markdown
---
**How would you like to proceed?**
1. **Fix all** — I'll implement all suggested fixes
2. **Fix P0/P1 only** — Address critical and high priority issues
3. **Fix specific items** — Tell me which ones
4. **Done** — Review complete, no changes needed
```

Do NOT implement changes until the user confirms. This is a review-first workflow.

## Resources

| File | When to load |
|------|-------------|
| `references/solid-checklist.md` | Structural changes, new classes/modules, refactoring |
| `references/security-checklist.md` | Auth, user input, data access, network, crypto |
| `references/code-quality-checklist.md` | Business logic, error handling, performance, boundaries |
| `references/removal-plan.md` | When flagging significant dead code needing a removal plan |
