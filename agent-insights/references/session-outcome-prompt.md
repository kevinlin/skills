# Session outcome (judged success)

This classifier judges whether the user, overall, accomplished what they set out to do. It first identifies the user’s primary objective in the session and then judges the outcome.

## Task

Judge the OUTCOME of this agent session — did the user accomplish what they set out to do?

Pick EXACTLY ONE of: Succeeded, Partially Succeeded, Failed, or No clear goal. There is NO ‘Cannot Judge’ option — pick the best fit from the four, even when evidence is thin.

This facet measures ONE THING: the outcome (succeeded / partially succeeded / failed / no clear goal). It does NOT measure how verifiable the outcome was — verifiable wins (commits, test passes, explicit ‘ship it’) and inferred wins (clean ending with no complaint) both belong in ‘Succeeded’. Verifiable failures (errors, explicit ‘didn’t work’) and inferred failures (looping agent, silent abandonment) both belong in ‘Failed’.

This is a TWO-STEP judgment — do both steps before you output a label:

**Step 1 — Identify the user’s PRIMARY OBJECTIVE.** 
Read the whole transcript and infer what the user was trying to accomplish overall. This is usually set by the first few user messages but may evolve over the session. If the user had multiple sub-tasks, pick the most significant one (or the only unifying one). Some sessions have no clear objective — pure exploration, chat, open-ended ‘what do you think’ — in which case the objective is genuinely absent and the answer is ‘No clear goal’.

Long sessions evolve through phases (plan → execute → verify). Identify the dominant operational objective by what the bulk of the session WORK serves, not by the first message’s framing alone. If the user opens with a planning question (‘can you suggest a plan?’, ‘how would you approach this?’) BUT the session then pivots to executing on the planned work, the goal IS the planned work — pick that. ‘No clear goal’ is reserved for sessions that stay exploratory throughout, with no execution phase. If the agent committed code, ran a successful build, or produced a final artifact, the goal is whatever produced that artifact.

**Truncation note:** if the transcript shows a `[TRANSCRIPT TRUNCATED FOR LENGTH]` marker, the cut is NOT outcome evidence — it just means there was more content than fit. Default to the strongest signal you can see in the visible head + tail. If neither side is visible, judge from the trajectory: clean / agent-on-task → Succeeded; loop / error / complaint → Failed; mixed → Partially Succeeded.

**Step 2 — Judge the OUTCOME.** 
Read the whole transcript and decide which label best describes what happened, using whichever signals are available — hard or soft.

Signals pointing toward SUCCEEDED (any of these — hard or soft): • A git commit / PR open / PR merge that matches the objective • A test suite passing on the change, or a command running successfully to completion producing the requested output • Explicit user affirmation — ‘thanks’, ‘ship it’, ‘perfect’, ‘this works’, ‘exactly right’ • The final artifact exists and the user doesn’t complain • The session ends cleanly with the agent having done what was asked, no errors, no complaints, no goal-reframing

Signals pointing toward FAILED (any of these — hard or soft): • User explicitly says it didn’t work / is wrong / nevermind / ‘this is broken’ • Final tool calls error out and are not recovered • Tests fail at the end • The agent loops, gives up, or apologizes without fixing • The user abandons mid-task in a way that signals the goal was not met

Pick the label that best fits: • Succeeded — outcome signals point toward the goal being met. The modal short CC session that ends cleanly with the agent having done what was asked belongs here. Don’t downgrade just because no commit or test confirmed it. When the transcript is thin and you cannot tell from explicit signals, default to Succeeded if the trajectory is clean and the agent is on-task. • Partially Succeeded — some sub-tasks done, others not; user accepted reduced scope; outcome is genuinely mixed. • Failed — outcome signals point toward the goal NOT being met, whether by explicit error/complaint or by quiet abandonment / looping / clearly-fell-short work. When the transcript is thin and you cannot tell from explicit signals, pick Failed only if the trajectory looks broken (errors, looping, complaints). • No clear goal — no operational objective in the first place; success frame doesn’t apply. DO NOT confuse ‘the agent worked competently’ with ‘the user’s goal was achieved’. The agent can write clean code that does the wrong thing. Judge OUTCOME vs. goal, not agent quality.

## Options

The options are below:
- **Succeeded**: The user’s primary objective was accomplished. Use this whenever the best read of the transcript is that the user got what they wanted — whether that judgment rests on HARD signals (a git commit matching the work, a test passing, a PR opened/merged, the user saying ‘thanks’ / ‘perfect’ / ‘ship it’, a command running to completion with output matching the objective, an artifact the user confirms) or SOFTER signals (the agent produced what was asked, the session ended cleanly, the user did not push back). This bucket folds together the modal short CC session that ended without complaint AND the longer session that ended with explicit verification — both are ‘Succeeded’.
- **Partially Succeeded**: Some but not all of the primary objective was achieved. The user accepted a reduced scope, moved goalposts mid-session, acknowledged one piece worked and another didn’t, or the agent made progress on parts of the task but hit a wall on a specific sub-task. Use when the outcome is genuinely mixed — neither a clean success nor a clean failure.
- **Failed**: The user’s primary objective was NOT achieved. Use this whenever the best read of the transcript is that the user did not get what they wanted — whether that judgment rests on HARD signals (final commands errored out and weren’t recovered, tests failed at the end, the user explicitly said ‘this didn’t work’ / ‘nevermind’ / expressed frustration) or SOFTER signals (the agent looped or gave up, the work clearly fell short of the ask, the user abandoned mid-task in a way that signals the goal was not met). Like ‘Succeeded’, this folds verifiable and inferred failures into one outcome bucket.
- **No clear goal**: The user did not have a single discernible primary objective — exploratory chat, wandering conversation, open-ended ‘what do you think’ with no operational outcome requested. Success is not the right frame for this session. Use when the frame doesn’t apply.

## Reference

Anthropic Research: [Agentic coding and persistent returns to expertise](https://www.anthropic.com/research/claude-code-expertise)