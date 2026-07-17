# agent-insights prompts

Prompts adapted from Claude Code's builtin `/insights` command, made tool-agnostic.

## 1. Facet extraction prompt (used by batch subagents)

Embed this verbatim in each facet-extraction subagent prompt, followed by the
transcript file list and output instructions (see SKILL.md):

```text
agent-insights facet extraction

Analyze each AI coding agent session transcript and extract structured facets.
Rate the OUTCOME and the USER's expertise from the user's turns and the session
trajectory — judge what the user achieved, NOT how competent the agent was.

CRITICAL GUIDELINES:

1. **goal_categories**: Classify the session's DOMINANT goal — one verb describing
   what the USER is doing — measured by the bulk of meaningful work, NOT by the stated
   intent of the first message. If a session opens with planning but spends most turns
   writing code, that's `building_something_new`, not `planning_a_change`.
   - Classify ONLY what the USER drives ("can you...", "please...", "I need...",
     "let's..."), not the agent's autonomous codebase exploration.
   - Pick EXACTLY ONE best-fit category and emit it with a count of 1, e.g.
     {"building_something_new": 1}. Do NOT invent free-text labels. Allowed categories
     (nine work modes + `others`):
     - `planning_a_change` — pre-implementation strategy: architecture, specs, design
       docs, tradeoff analysis, scoping. Deliverable is a plan/decision, not working code.
     - `building_something_new` — write, refactor, migrate, or extend code that is ITSELF
       the deliverable (service, library, CLI, component, ETL, config consumed by
       software). Subsumes new code, features, refactors, optimizations, dependency
       updates, migrations.
     - `fixing_something_broken` — reactive fault diagnosis and bug fix; the trigger is
       BROKEN behavior (wrong output, errors, crashes, failing tests, regressions). NOT
       working-but-slow/ugly code (that's building).
     - `understanding_a_system` — explore, investigate, audit for comprehension; output is
       KNOWLEDGE about code/systems/concepts, not a change. NOT investigation that resolves
       into a fix (that's fixing).
     - `testing_code` — write/extend tests, QA, security/vulnerability review; deliverable
       is VERIFICATION of correctness, incl. test infra/fixtures/mocks/coverage. NOT fixing
       app code revealed broken by tests (that's fixing).
     - `operating_software` — deploy, configure, monitor, CI/CD, env/dependency setup, infra
       provisioning, release rollout, log triage: the scaffolding around code, not the code.
     - `analyzing_data` — data analysis/analytics where any code is INSTRUMENTAL (one-shot
       scripts, notebooks, queries); the artifact is an insight/table/plot/model. NOT
       production ETL or recurring data services (that's building).
     - `orchestrating_agents_and_pipelines` — meta-AI work: prompt engineering, agent/
       subagent/skill/hook design, eval harnesses, tool-use loops, classifiers powered by
       an LLM. NOT app code that merely calls an LLM as a feature (that's building).
     - `writing_docs_and_presentations` — non-code knowledge work for a HUMAN audience:
       docs, READMEs, slides, reports, memos, emails, notes, synthesizing research into
       prose. Deliverable is words/slides, not code or analytical numbers.
     - `others` — a real task that fits none of the above.
   - Key distinctions when two could apply:
     - Build vs Fix: Build adds/evolves WORKING code; Fix is triggered by something broken.
     - Build vs Analyze: Build = code is the deliverable; Analyze = code is instrumental and
       the artifact is an insight.
     - Build vs Test: writing tests is Test; fixing app code that tests reveal broken is Fix.
     - Build vs Operate: shipped code is Build; deploy/config/CI/env is Operate.
     - Plan vs Understand: Plan looks forward (designing); Understand looks at what exists.
     - Understand vs Analyze: Understand = code/systems/concepts; Analyze = data.
     - Understand vs Fix: investigation with no change is Understand; investigation that
       resolves into a code change is Fix.
     - Orchestrate vs Build: meta-AI work is Orchestrate; an app that merely calls an LLM
       is Build.

2. **outcome**: Did the user accomplish what they set out to do? Judge in two steps.
   - Step 1 — identify the user's PRIMARY OBJECTIVE. Read the whole transcript; the
     objective is usually set in the first few user messages but may evolve. Long sessions
     move plan -> execute -> verify: the objective is what the bulk of the WORK serves, not
     the first message's framing. If they open with a planning question but pivot to
     executing it, the objective is the executed work.
   - Step 2 — judge the outcome from HARD or SOFT signals.
     - Toward succeeded: a commit/PR matching the work, tests passing, a command running to
       completion with the requested output, explicit affirmation ("thanks", "perfect",
       "ship it"), or the artifact exists and the user doesn't complain / the session ends
       cleanly with the agent on-task.
     - Toward failed: user says it didn't work / "nevermind" / shows frustration, final tool
       calls error out unrecovered, tests fail at the end, the agent loops or gives up, or
       the user abandons mid-task.
     - Thin transcript: default to `succeeded` if the trajectory is clean and on-task; pick
       `failed` only if it looks broken (errors, looping, complaints).
   - Judge OUTCOME vs the goal, NOT agent quality: clean code that does the wrong thing is
     not success. Pick EXACTLY ONE:
     `succeeded` | `partially_succeeded` | `failed` | `no_clear_goal`. Use `no_clear_goal`
     only for sessions that stay exploratory throughout, with no operational objective.

3. **user_satisfaction_counts**: Base ONLY on explicit user signals.
   - "Yay!", "great!", "perfect!" -> happy
   - "thanks", "looks good", "that works" -> satisfied
   - "ok, now let's..." (continuing without complaint) -> likely_satisfied
   - "that's not right", "try again" -> dissatisfied
   - "this is broken", "I give up" -> frustrated

4. **friction_counts**: Be specific about what went wrong.
   - misunderstood_request: agent interpreted incorrectly
   - wrong_approach: right goal, wrong solution method
   - buggy_code: code didn't work correctly
   - user_rejected_action: user said no/stop to a tool call
   - excessive_changes: over-engineered or changed too much

5. **expertise_level**: Rate the USER's demonstrated expertise in the domain/task of THIS
   session — command of its terminology, structures, and conventions — ONCE for the WHOLE
   conversation, from the user's turns only. Rate domain familiarity with the work AT HAND,
   NOT general intelligence, NOT the agent's performance, NOT task difficulty (a senior
   engineer can be a beginner at Rust or differential privacy). Weigh three CO-EQUAL signals
   together:
   - Setup specificity: does the framing use named entities/constraints that require domain
     knowledge to even reach for? Naming files/paths visible on screen is NOT domain
     knowledge — anyone using the agent does that.
   - Verification type: generic asks ("please double-check", "are you sure?") are epistemic
     humility, not expertise; targeted asks ("did you actually call commit()?", "what's the
     cardinality of that join?") require knowing WHAT to check.
   - Direction of correction: the agent correcting the user's terminology/mental model pulls
     DOWN (1-2); the user catching the agent's domain mistakes pulls UP (4-5); neither
     correcting the other is neutral.
   Emit exactly ONE value (default `2_beginner` only when there's nothing to go on, e.g. a
   warmup session):
   - `1_novice` — generic/imprecise framing, no domain names; verification absent or fully
     generic; doesn't notice wrong output; agent supplies basic domain concepts.
   - `2_beginner` — some correct terms used loosely; mostly generic verification; pushes back
     only on obvious errors; agent reframes the user at least once. A fluent technologist
     working OUTSIDE their domain lands here.
   - `3_intermediate` — precise at a directive level (names files, outputs, libraries) but
     doesn't engage methodology/tradeoffs; mix of generic and targeted checks; catches
     meaningful mistakes. A domain expert delegating a routine task can also land here.
   - `4_advanced` — structural domain knowledge NOT readable off the screen (a specific edge
     case, non-obvious constraint/invariant, version-specific behavior, known failure mode);
     moderately specific verification; catches at least one of the agent's domain mistakes;
     the agent doesn't have to correct the user's domain model.
   - `5_expert` — insider-only jargon/conventions, unprompted tradeoff discussion, surgical
     verification, authoritative corrections invoking specific technical reasoning,
     preemptive edge-case handling. Direction of correction is user->agent. "Insider talking
     to an equal," even in a short session.

6. If the session is very short or just a warmup (no real task — a greeting, a
   one-line test, an aborted start), use `warmup_minimal` as the ONLY goal_category
   key. This is a special marker, NOT one of the categories above, and it excludes
   the session from narrative analysis. Use `others` (not `warmup_minimal`) for real
   tasks that simply don't fit the nine named categories.

For EACH session, produce a JSON object matching this schema:
{
  "underlying_goal": "What the user fundamentally wanted to achieve",
  "goal_categories": {"<one category from guideline 1, or warmup_minimal>": 1},
  "outcome": "succeeded|partially_succeeded|failed|no_clear_goal",
  "user_satisfaction_counts": {"level": count, ...},
  "session_type": "single_task|multi_task|iterative_refinement|exploration|quick_question",
  "friction_counts": {"friction_type": count, ...},
  "friction_detail": "One sentence describing friction or empty",
  "expertise_level": "1_novice|2_beginner|3_intermediate|4_advanced|5_expert",
  "brief_summary": "One sentence: what user wanted and whether they got it"
}
```

The full Anthropic classifier prompts these rubrics distill — with every level/label
definition and worked distinction — live alongside this file:
`goal-classifier-prompt.md`, `session-outcome-prompt.md`, `expertise-classifier-prompt.md`.
Read them only when auditing or refining these rubrics; the distilled prompt above is
what runs during extraction.

## 2. Narrative sections (written by the main agent into narrative.json)

Ground every section in `aggregate.json` (especially `narrative_context.session_briefs`,
`narrative_context.friction_details`, `per_tool`, and `distributions`). Use second person
("you"). Don't invent events that aren't in the data. Write ALL of the following keys
into `narrative.json`:

### at_a_glance
A persona one-liner plus a 4-part coaching summary, 2-3 not-too-long sentences each.
Don't mention raw stats; the report shows numbers elsewhere. Honest but constructive.
```json
{"persona": "You are a <level> AI <user_type>.", "whats_working": "...", "whats_hindering": "...", "quick_wins": "...", "ambitious_workflows": "..."}
```
- persona: exactly the form `You are a <level> AI <user_type>.`
  - `<level>`: skill level with coding agents, judged from outcomes, friction, and the
    sophistication of workflows (plans, subagents, verification gates, custom commands).
    Pick one of: Beginner, Intermediate, Proficient, Expert.
  - `<user_type>`: the role the session content actually reflects — what the user works
    ON, not which tools they use. E.g. Software Engineer, Product Owner, Business
    Analyst, UI/UX Designer, AI Practitioner, Data Engineer, Technical Writer.
    Pick the single best fit; use "an" instead of "a" when grammar requires.
- whats_working: the user's distinctive style and impactful things they've done
- whats_hindering: (a) agent's fault (misunderstandings, bugs) and (b) user-side friction (thin context, environment issues)
- quick_wins: specific features or workflow techniques to try next
- ambitious_workflows: what to prepare for as models get more capable

### tool_comparison  (cross-tool: unique to agent-insights)
```json
{"narrative": "2-3 paragraphs on HOW usage differs across the agent tools found: which tool gets which kind of work, depth vs quick edits, where each shines or struggles. Use **bold** for key insights.", "key_difference": "One sentence on the most distinctive cross-tool pattern"}
```
Skip gracefully (one short paragraph) if only one tool was detected.

### project_areas
```json
{"areas": [{"name": "...", "session_count": N, "description": "2-3 sentences on what was worked on and how agents were used"}]}
```
4-5 areas. Skip internal agent-insights operations.

### interaction_style
```json
{"narrative": "2-3 paragraphs analyzing HOW the user interacts with coding agents: iterate quickly vs detailed upfront specs? Interrupt often or let the agent run? Include specific examples. Use **bold** for key insights.", "key_pattern": "One sentence summary"}
```

### what_works
```json
{"intro": "1 sentence of context", "impressive_workflows": [{"title": "3-6 words", "description": "2-3 sentences"}]}
```
3 impressive workflows.

### friction_analysis
```json
{"intro": "1 sentence", "categories": [{"category": "...", "description": "1-2 sentences incl. what to do differently", "examples": ["specific example with consequence", "another"]}]}
```
3 categories, 2 examples each.

### suggestions
```json
{
  "memory_file_additions": [{"addition": "A line to add to CLAUDE.md / AGENTS.md / .cursorrules", "why": "1 sentence grounded in sessions", "prompt_scaffold": "where to add it"}],
  "features_to_try": [{"feature": "...", "one_liner": "...", "why_for_you": "...", "example_code": "command or config to copy"}],
  "usage_patterns": [{"title": "...", "suggestion": "1-2 sentences", "detail": "3-4 sentences", "copyable_prompt": "a prompt to try"}]
}
```
2-3 items per list. For memory_file_additions, PRIORITIZE instructions the user repeated
across 2+ sessions; they shouldn't have to repeat themselves. For features_to_try, pick
features native to the tools the user actually uses (skills/hooks/MCP for Claude Code,
rules for Cursor, etc).

### new_use_cases
```json
{
  "intro": "1 sentence naming the top-used tool and the most frequent project area these ideas are grounded in",
  "use_cases": [{"title": "3-6 words", "description": "2-3 sentences: what to do and the payoff", "relevance": "1 sentence tying it to the user's most frequent project work", "copyable_prompt": "a ready-to-paste prompt for the top-used tool"}]
}
```
3-4 use cases. Rules:
- Ground in the user's TOP-USED tool (most sessions in `per_tool`) and their MOST
  FREQUENT project work (from `project_areas` / `narrative_context.session_briefs`).
- Each use case must be something the sessions show the user has NOT tried yet — check
  `goal_categories`, `session_types`, and the session briefs before proposing. Do not
  repeat anything already covered in `suggestions`.
- Prefer use cases native to the top-used tool's capabilities (e.g. subagents/skills/hooks
  for Claude Code, rules/background agents for Cursor).

### fun_ending
```json
{"headline": "A memorable QUALITATIVE moment - human, funny, or surprising. Not a statistic.", "detail": "Brief context about when/where"}
```
