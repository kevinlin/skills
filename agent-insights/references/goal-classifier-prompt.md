# Goal Classifier

This classifier categorizes each session into one of nine work modes that best describes what the session is trying to accomplish.

## Task

Classify the GOAL of this agent session. Pick EXACTLY ONE of: Plan, Build, Fix, Understand, Test, Operate, Analyze, Orchestrate, or Communicate. Each label is a verb describing what the user is doing.

There is NO ‘Unclear’ option — pick the BEST fit from the nine, even when evidence is thin. If the session is short or ambiguous, pick the verb that best fits the small amount of evidence rather than abstaining.

Pick by DOMINANT activity, measured by volume of meaningful work, NOT by the user’s stated intent in turn 1. If a session opens with planning but then spends most turns writing code, that’s Build, not Plan. The triggering intent doesn’t decide the label — the bulk of the work does.

## Key distinctions:

- **Build vs Fix**: Build adds, evolves, refactors, optimizes WORKING code. Fix is reactive — the trigger is something broken.
- **Build vs Analyze**: Build = code is the deliverable for ongoing use. Analyze = code is INSTRUMENTAL; the artifact is an insight, chart, or model.
- **Build vs Test**: writing tests is Test. Fixing app code revealed broken by tests is Fix. Building test infrastructure itself is Build.
- **Build vs Operate**: shipped code is Build. Deploy / config / CI / env / monitoring is Operate.
- **Plan vs Understand**: Plan looks forward (designing). Understand looks at what exists.
- **Understand vs Analyze**: Understand is about code / systems / concepts. Analyze is about data.
- **Understand vs Fix**: investigation with no fix = Understand. Investigation that resolves into a code change to make broken behavior correct = Fix.
- **Orchestrate**: meta-AI work. Apps that happen to call an LLM are Build.
- **Communicate**: deliverable is human-readable words / slides. Pairs with codebase_context = ‘Not in a codebase’. 

## The options are below:

- **Plan**: Pre-implementation strategy. The user is figuring out HOW to do something before doing it: architecture, specs, design docs, tradeoff analysis, sequencing, scoping. The deliverable is a plan / spec / decision, NOT working code. If the session starts with planning but then transitions into building, classify by the dominant activity.
- **Build**: Write, refactor, migrate, or extend code. The user is producing or evolving code that is ITSELF the deliverable — a service, library, CLI, script, endpoint, component, ETL pipeline, configuration consumed by software. Subsumes new code, feature additions, refactors, optimizations, dependency updates, and migrations. Use Build whenever the primary output of the session is delivered or maintained code.
- **Fix**: Reactive fault diagnosis and bug fix. The session is triggered by code or behavior that is BROKEN — produces wrong output, errors, crashes, fails tests, returns the wrong thing, regresses an earlier behavior. The work is finding the cause and making it right. NOT this: code that works correctly but is slow / suboptimal / ugly (that’s Build). NOT this: writing tests for working code (that’s Test).
- **Understand**: Explore, investigate, root-cause-for-comprehension, audit-for-understanding. Primary output is KNOWLEDGE about a system, code, or concept — not a code change. Code review for understanding, tracing how a flow works, learning a new framework, investigating WHY something behaves a certain way without intent to change it, onboarding to a codebase. NOT this: investigation that resolves into a fix (that’s Fix). NOT this: data analysis (that’s Analyze). Hallmark: knowledge in the user’s head at the end, not code in the repo.
- **Test**: Test, code review, QA, security audit. Deliverable is VERIFICATION of correctness — writing new tests, fixing or extending the test suite, security or vulnerability review, QA / acceptance checking, formal-method-style verification. Includes test infra, fixtures, mocks, coverage tooling. NOT this: fixing application code revealed broken by tests (that’s Fix). NOT this: code review aimed primarily at learning the codebase (that’s Understand).
- **Operate**: Deploy, configure, monitor, on-call, CI/CD, env / dependency setup. The session works on the SCAFFOLDING around code rather than the code itself: Dockerfiles, k8s manifests, Terraform, GitHub Actions / CI workflows, deploy scripts, env-var management, package install, on-call paging, log triage, monitoring dashboards, infra provisioning, rolling out a release. NOT this: writing infra-as-code as part of building a new infra TOOL (that’s Build). Hallmark: operational / lifecycle work.
- **Analyze**: Data analysis, research coding, analytics. Primary output is analytical artifacts — numbers, tables, plots, reports, models — where any code is INSTRUMENTAL (one-shot scripts, notebooks, exploratory queries) rather than the deliverable. Examples: computing summary statistics, building plots, running a regression, exploring a dataset, training a one-off ML model for analysis, writing a SQL query for a report. NOT this: production ETL pipelines or recurring data services (that’s Build). NOT this: code review of analysis code (that’s Test or Understand). Hallmark: the artifact at the end is an INSIGHT, not running software.
- **Orchestrate**: Orchestrate Claude or other AI agents — meta-work where the deliverable is an AI artifact. Prompt engineering, designing agent workflows, building eval harnesses for LLMs, tuning agent behavior, debugging an agent, drafting agent system prompts, writing classifiers powered by Claude, building tool-use loops, constructing few-shot or many-shot examples. NOT this: writing application code that happens to call an LLM as a feature (that’s Build with an LLM/Agents domain). Hallmark: the session’s primary intellectual work is on the AI system itself.
- **Communicate**: Non-code knowledge work for a HUMAN AUDIENCE. The user is using agent as a general assistant to produce, refine, or work out PROSE / SLIDES / MESSAGES / NOTES intended for human readers: business writing (memos, emails, briefs, slides, reports), drafting / editing essays or narratives, synthesizing external research into a writeup, personal knowledge management (notes, summaries, journaling, organizing thinking), planning a meeting / trip / decision in prose, brainstorming captured as text, conversational math or finance done for a writeup. Hallmark: deliverable is words / slides / human-readable artifacts, NOT code, NOT analytical numbers, NOT AI-system tuning.

## Output
- Plan -> `planning_a_change`
- Build -> `building_something_new`
- Fix -> `fixing_something_broken`
- Understand -> `understanding_a_system`
- Test -> `testing_code`
- Operate -> `operating_software` 
- Analyze -> `analyzing_data`
- Orchestrate -> `orchestrating_agents_and_pipelines`
- Communicate -> `writing_docs_and_presentations`
- Others - `others` — anything that fits none of the above (but is still a real task)

## Reference

Anthropic Research: [Agentic coding and persistent returns to expertise](https://www.anthropic.com/research/claude-code-expertise)