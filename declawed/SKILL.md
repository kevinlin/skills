---
name: declawed
description: >
  De-slop pass for any text: mechanically scans for the statistical tells of
  AI writing (the "not X but Y" reflex, puffery, uniform cadence, …) and
  rewrites by meaning into the target register, tweet to academic paper.
  Use when the user says "declawed"/"deslop", asks to remove AI tells /
  humanize text / make it not sound like AI, names a specific tell to strip,
  or before publishing any agent-drafted prose.
metadata:
  version: 1.1.0
---

# Declawed

Strip every mark of AI writing from a text and make it good in its genre. Not "make it pass a detector" — make it read like a specific person with a specific point wrote it for a specific audience.

## Why this is a loop, not a style guide

The worst tells — above all the **"not X but Y"** family — are not vocabulary mistakes. They are emergent properties of how LLMs generate text: preference tuning rewards balanced, contrastive, comprehensive-sounding framing, so the contrast move is baked into the model's priors. Two consequences drive this skill's architecture:

1. **You cannot reliably see your own slop.** The same priors that produce the pattern make it invisible on re-read. Detection must be mechanical — regex against a fixed catalog — never "does this look AI to me?"
2. **Rewriting reintroduces slop.** Ask a model to remove "it's not just X, it's Y" and it produces "this is less about X than Y" — the same move in a wig. So every rewrite gets re-scanned, and the loop runs until the scan is clean.

Workflow: **Scan → Diagnose → Rewrite by meaning → Re-scan → (repeat) → Register check.**

## Phase 0: Fix the target

Before touching the text, establish:

- **Genre and venue** — academic article, tweet, reddit post, LinkedIn, email, blog, docs, marketing. Genre decides which tells are fatal and what "good" means; see [references/tones.md](references/tones.md). If it's stated or obvious from the text, use it. If not, default to general prose (neutral register, plain and specific), note the assumption, and proceed. Only stop to ask when the genre would flip which tells are fatal (reddit forbids the bold and bullet essays that docs rely on) and you genuinely can't tell from the text.
- **Audience and stance** — who reads it, and what the author actually claims. Slop is what fills the space where a claim should be; you cannot remove it without knowing the claim.
- **Constraints** — length limits, required citations, house style.

## Phase 1: Mechanical scan

Run [scripts/scan.py](scripts/scan.py) against the text. It loads the catalog from [references/slop-patterns.md](references/slop-patterns.md) — the single source of truth — and reports both the regex matches and the structural checks below, as a finding table:

```bash
python3 scripts/scan.py draft.txt      # scan a file
pbpaste | python3 scripts/scan.py      # scan piped or clipboard text
```

If the text lives only in the conversation and you can't write it to a temp file, apply each pattern in [references/slop-patterns.md](references/slop-patterns.md) by hand, line by line.

The finding list gives line/sentence, matched pattern, and tell category. `scan.py` already computes the structural checks that regex can't fully catch (cadence, formatting — sections 5–6 of the catalog); when you scan by hand, run those sections yourself.

Report the findings to the user as a short table before rewriting (category, count, worst example).

## Phase 2: Rewrite by meaning, not by frame

Go finding by finding. The cardinal rule: **never fix a pattern by paraphrasing the pattern.** Fix it by deciding what the sentence actually asserts, then asserting that. Phase 2 is done when every finding in the Phase 1 table has received one of the treatments below — none skipped, none half-fixed.

### The "not X but Y" family — three-way triage

Every negative parallelism gets exactly one of these treatments:

1. **The negation is a strawman** (nobody believes X). Delete the X half entirely and assert Y directly, with whatever evidence the text has.
   - *"It's not just a tool, it's a fundamental shift in how teams work"* → *"Teams that adopted it stopped holding standups within a month."*
2. **The contrast is real** (people genuinely hold X). Then earn it: name who holds X, say concretely why Y beats it. A real contrast survives being made specific; slop doesn't.
3. **The sentence asserts nothing** (the contrast is decoration on an empty claim). Delete the whole sentence. Most cases are this one.

Banned escape hatches — these are the same move and count as new findings: "less about X than Y", "X matters, but Y matters more", "the real X is Y", "the question isn't X, it's Y", "X? Y." (rhetorical-question variant), and the em-dash variant "— not X, but Y".

### Everything else

- **Puffery and inflated vocabulary** (pivotal, seismic, testament, tapestry, landscape, delve…): replace with the plain word, or with the concrete fact the puffery was hiding. "Plays a vital role in" → "does".
- **Rule-of-three lists**: keep the strongest item, cut the rest — unless all three carry distinct information, in which case keep them and break the rhythm (different lengths, different syntax).
- **False ranges** ("from X to Y"): if you can't name a meaningful midpoint between X and Y, it's not a range — name the two things or cut one.
- **Hedged both-sidesing** ("it's worth noting", auto-counterpoints, "while X, it's also true that Y"): commit. One opinion, stated, owned. A counterpoint stays only if the author genuinely concedes it.
- **Uniform cadence**: vary deliberately. Follow a long sentence with a short one. Fragments are legal. Don't apply a formula (alternating long/short is its own tell) — read the paragraph aloud and break wherever the rhythm is metronomic.
- **Low specificity**: replace "many companies" / "studies show" / "recent research" with the actual names, numbers, and dates — **only from the source text, the conversation, or verifiable research you actually do**. Never invent specifics. If the author needs to supply one, leave a marked placeholder: `[ADD: which study?]`.
- **Stock skeleton**: kill throat-clearing openers ("In today's fast-paced world…"), summary conclusions ("In conclusion… Ultimately…"), and engagement-bait endings ("What do you think?"). Start where the point starts; stop when it's made.

### Overcorrection is also slop

- No fake typos, forced slang, or manufactured "voice". Humanizer-tool output is its own genre of slop.
- Em dashes are not banned. Humans use them. The tell is density and the double-dash "— not X, but —" move; the thresholds live in catalog section 5.
- Don't trade precision for personality in academic or technical text. There, de-slopping means cutting puffery and committing to claims — not adding attitude.
- Preserve the author's meaning, claims, and facts exactly. This is a style pass, not a content edit. Flag, don't silently fix, anything that looks factually wrong.

## Phase 3: Verify loop

Re-run the full Phase 1 scan **on your rewritten text**. Expect your own rewrite to contain new tells — the model writing it has the same priors that created them.

A clean pass is not zero regex hits. The catalog is deliberately aggressive, and some hits are legitimate in context: a contrast you genuinely earned in Phase 2, "robust" in a sentence that reports an actual benchmark, an em dash a human would reach for. Clean means every remaining hit has been through Phase 2 triage and consciously kept, and the rewrite introduced no new untriaged tells. Send each new hit back through triage and loop until a pass surfaces nothing left to fix.

Cap at 4 passes. If a pattern survives 4 passes, rewrite that sentence from scratch starting from its bare claim ("what fact or opinion is this sentence for?").

## Phase 4: Register check

Check the clean text against its genre profile in [references/tones.md](references/tones.md): right length, right formality, right person, genre-specific tells gone (e.g. on reddit: no bold, no bullet essay; in academic prose: no first-person hot takes added). Then the final test — read it aloud. Anywhere you wouldn't say it to the actual audience, rewrite that sentence.

Deliver two things: the rewritten text, then a change log in this shape:

```
Changes
- <category>: <n> fixed (<how — deleted / made specific / plain word>)
- Cadence: <what you varied, or "unchanged">
- Verify passes: <n>
- Flagged for author: <any [ADD: …] placeholders you left, or "none">
```

## Worked example

A short LinkedIn-flavored paragraph, run through the whole loop.

**Input:**

> In today's fast-paced world, effective communication isn't just important — it's absolutely pivotal. Great leaders don't just talk; they listen, they empathize, and they inspire. It's worth noting that the best teams are built not on talent, but on trust.

**Scan (Phase 1):**

- Stock opener — "In today's fast-paced world"
- Negative parallelism — "isn't just important — it's absolutely pivotal", "don't just talk", "built not on talent, but on trust" (3)
- Puffery — "pivotal"
- Rule-of-three — "listen, they empathize, and they inspire"
- Hedging — "It's worth noting that"

**Triage + rewrite (Phase 2):** The opener asserts nothing, so cut it. "isn't just important, it's pivotal" decorates an empty claim; cut it and state the actual point. The triplet collapses to the one verb that carries weight. "not on talent, but on trust" is a real contrast, so earn it as a plain positive claim instead of the negation frame. "It's worth noting" is throat-clearing; drop it.

**Output:**

> Good leaders listen more than they talk. Under pressure, what holds a team together is trust; talent alone won't.
