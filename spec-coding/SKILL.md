---
name: spec-coding
description: >
  Guide users through spec-driven development — from goal clarification through
  requirements, design, task planning, and incremental execution. Use this skill
  whenever a user wants to build a new feature with upfront planning, asks for a
  structured development workflow, mentions "spec-driven", wants to create
  requirements or a design doc before coding, or invokes /spec-coding. Also
  trigger when a user has existing spec files (requirements.md, design.md,
  tasks.md) and wants to continue or execute tasks from them.
metadata:
  version: 1.0.0
---

# Spec-Driven Development

A workflow for building features specification-first. Instead of jumping straight
into code, you walk through five stages — each producing a concrete artifact that
the next stage builds on. This front-loaded planning catches design issues early
and produces better implementations.

## Stages

| Stage | Output | Purpose |
|-------|--------|---------|
| 1. Goal Confirmation | Shared understanding | Align on what we're building and why |
| 2. Requirements | `requirements.md` | Define *what* the system does (EARS format) |
| 3. Design | `design.md` | Define *how* it works technically |
| 4. Task Planning | `tasks.md` | Break the design into executable coding steps |
| 5. Execution | Working code | Implement tasks incrementally |

All spec artifacts live in `docs/specs/{feature-name}/` (kebab-case).

## Resuming a Workflow

Users often return to a workflow across multiple sessions. Before starting fresh,
check whether spec files already exist for the feature:

- If `tasks.md` exists with unchecked items → offer to resume at Stage 5 (Execution)
- If `design.md` exists but no `tasks.md` → offer to resume at Stage 4 (Task Planning)
- If `requirements.md` exists but no `design.md` → offer to resume at Stage 3 (Design)
- If no spec files exist → start from Stage 1

When resuming, read all existing spec files first to rebuild context, then confirm
with the user where they'd like to pick up.

## Approval Gates

Every stage that produces a document (Stages 2–4) follows the same rhythm:

1. Generate or update the document
2. Present it and ask if it looks good
3. If the user requests changes → revise and ask again
4. Only advance to the next stage after explicit approval

This matters because each document becomes the foundation for the next stage. A
requirements gap that slips through will propagate into the design and tasks. Take
the time to get each artifact right.

If during a later stage you or the user discover a gap in an earlier artifact,
offer to go back and fix it rather than working around it.

---

## Stage 1: Goal Confirmation

Establish a clear, shared understanding of what the feature should accomplish
before generating any documents.

Ask clarifying questions about:
- What problem the feature solves and for whom
- Expected behavior and outcomes
- Technical constraints or integration points
- Scope boundaries (what's explicitly *not* included)

Suggest refinements if the goal seems too broad — a well-scoped goal leads to
better requirements. Once you and the user agree on the goal, summarize it and
derive a `feature-name` (kebab-case) for the spec directory.

**Track progress** — create a TodoWrite list for the workflow stages:
```
- Goal confirmation (in_progress)
- Requirements gathering (pending)
- Design documentation (pending)
- Task planning (pending)
```

---

## Stage 2: Requirements Gathering

Translate the confirmed goal into structured requirements. Generate a first draft
based on what you already know rather than asking a long series of questions — the
user can iterate on a concrete document much faster than answering questions in
the abstract.

Create `docs/specs/{feature-name}/requirements.md` with this structure:

```markdown
# Feature Requirements: {Feature Name}

## Introduction

[Brief description of the feature and its purpose]

## Requirements

### 1. [Requirement Title]

**User Story:** As a [role], I want [feature], so that [benefit]

**Acceptance Criteria:**
1. WHEN [trigger/condition], THE SYSTEM SHALL [behavior]
2. WHERE [precondition], THE SYSTEM SHALL [behavior]
3. IF [condition], THEN THE SYSTEM SHALL [behavior]
```

The EARS (Easy Approach to Requirements Syntax) keywords — WHEN, WHERE, IF/THEN,
WHILE, SHALL — make requirements testable and unambiguous, which pays off during
task planning and implementation.

Consider edge cases, error scenarios, and non-functional concerns (performance,
security) in your initial draft. After presenting the document, suggest specific
areas that might need clarification to guide the user's review.

Stay focused on *what* the system should do — save *how* for the design stage.

---

## Stage 3: Design Documentation

Develop a technical design that addresses all requirements. This is where you
research the codebase, explore existing patterns, and make architectural
decisions.

**Research during design** — explore the codebase to understand:
- Existing patterns and conventions to follow
- Components that will be affected or extended
- Dependencies and integration points
- Similar features that can inform the approach

Use this research as context for the design. You don't need to create separate
research files — fold findings directly into the design document.

Create `docs/specs/{feature-name}/design.md` with these sections:
- **Overview** — what the design achieves at a high level
- **Architecture** — how components fit together
- **Components and Interfaces** — key abstractions and their contracts
- **Data Models** — schemas, types, state shapes
- **Error Handling** — failure modes and recovery strategies
- **Testing Strategy** — approach to validating the implementation

Include Mermaid diagrams where they clarify component relationships or data flow.
Highlight design decisions and their rationale — this context helps during
implementation and future maintenance.

---

## Stage 4: Task Planning

Break the design into a sequence of concrete coding tasks. Each task should be
something a developer (or coding agent) can pick up and execute independently.

Create `docs/specs/{feature-name}/tasks.md` as a numbered checkbox list:

```markdown
## Implementation Tasks

- [ ] 1. [Task description]
    - Details and context
    - References: Requirement 1.1, 1.2

- [ ] 2. [Task description]
    - [ ] 2.1 [Subtask if needed]
    - [ ] 2.2 [Subtask]
```

**Sequencing principles:**
- Each task should build incrementally on previous ones — no orphaned code that
  isn't wired into the system
- Prioritize test-driven development: write tests early, validate core
  functionality before building on it
- Reference specific acceptance criteria from requirements so nothing gets missed
- Keep tasks focused on code: writing, modifying, and testing. Exclude deployment,
  user testing, performance monitoring, and other non-coding activities

**What makes a good task:**
- Specifies which files or components to create/modify
- Is concrete enough to execute without additional clarification
- Scoped to a specific coding activity ("Implement the authentication middleware"
  not "Support authentication")
- Includes enough context to understand *why*, but delegates *how* to the design doc

After the user approves the tasks, let them know they can begin execution by
asking you to work through the task list or by invoking this skill again.

---

## Stage 5: Task Execution

Execute tasks from the approved task list one at a time with user review between
each task.

**Before executing any task**, read all three spec files (requirements.md,
design.md, tasks.md) to ensure your implementation aligns with the full context.
Implementing without this context leads to drift from the design.

**Execution flow:**
1. If the user doesn't specify a task, recommend the next unchecked one
2. If a task has subtasks, work through them in order
3. Focus only on the current task — don't implement ahead
4. Verify your implementation against the task's referenced requirements
5. When done, mark the task as checked in `tasks.md`
6. Stop and let the user review before moving on

**Answering questions** — the user may ask about tasks without wanting to execute
them (e.g., "what's the next task?" or "how complex is task 3?"). Respond with
information without starting execution.

Track individual task progress with TodoWrite:
```
- Task 2.1: [description] (in_progress)
- Task 2.2: [description] (pending)
```
