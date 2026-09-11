# Tone Guide

What "good" means per genre, what tells are fatal there, and what the de-slopped text should sound like. Use in Phase 0 (fix the target) and Phase 4 (register check). Two universal rules first:

1. **Voice comes from commitment, not decoration.** A text sounds human when it asserts specific things a specific person believes, at the level of detail only someone who did the work would know. Slang, typos, and "personality" sprinkled on top do not produce this and read as humanizer-tool output.
2. **Match the author, not a persona.** If the user supplied earlier writing or a draft with their own phrasing in it, keep their words wherever they survive the scan. De-slopping someone into a generic "casual" voice is just different slop.

## General language (every tone except Marketing / landing copy)

These rules apply on top of every genre profile below, except Marketing / landing copy. Where a profile conflicts, STE wins unless the profile is listed under **Genre carve-outs**.

### Context: full sentences, not point form

- Write full sentences. A bare conclusion ("Migrated the Customer DB. 30% faster.") gives the reader no reason to believe it.
- For a conclusion, claim, or recommendation, use this shape: `Given <context | evidence>, <conclusion>, so <consequence | artefact>.`
  - Before: "Migrated the Customer DB. 30% faster."
  - After: "Given the load test on the new Customer DB, queries run 30% faster, so the reporting job now fits in its nightly window."
- For a procedure step, use the STE form and put the condition first: `If <condition>, <instruction>.`
- Use the shape for conclusions only, not for every sentence. Change the connector ("because", "since", "when") and the clause order. If one sentence goes above the 25-word cap, split it into two. When every sentence is "Given X, Y, so Z", the text shows the uniform-shape tell ([slop-patterns.md](slop-patterns.md) section 6).
- The "so" clause must name a concrete effect or artefact: a file, a number, or a next step. If the source has none, remove the clause. Do not fill it with puffery ("so teams move faster").
- Take the evidence and the consequence from the source or the conversation only. If one is missing, leave `[ADD: evidence?]`.
- Lists stay where the genre permits them (docs). Each list item is a full sentence.

### ASD-STE100 Simplified Technical English

Apply the core writing rules of ASD-STE100 (Issue 9, January 2025). The STE dictionary is copyrighted, so this skill does not include it.

- **Words**: use one word for one meaning, and use the same word for the same thing everywhere in the text. Use the simplest common word. Technical names and technical verbs are permitted; the ubiquitous language (below) supplies them.
- **Verbs**: use the imperative, simple present, simple past, or future. Do not use -ing verb forms (they are permitted in technical names). Do not use phrasal verbs ("set up" → "configure", "find out" → "learn"). Use the active voice. Use the passive voice only in descriptive text, and only when the actor is unknown or not important.
- **Noun clusters**: 3 words at most. Break a longer cluster with a preposition ("database migration test report" → "report of the database migration test").
- **Sentences**: one topic per sentence. Do not remove articles or "that" to make a sentence shorter. Procedures: 20 words at most, one instruction per sentence, imperative, condition first. Descriptive text: 25 words at most.
- **Paragraphs**: one topic per paragraph, topic sentence first, 6 sentences at most.
- The word caps are a maximum, not a target. Change the sentence length below the cap, because uniform cadence is still a tell.

### Ubiquitous language

Before the rewrite, look for the project's glossary in this order:

1. Terms that the conversation defines.
2. `UBIQUITOUS_LANGUAGE.md` in the working directory or the repository root (the `ubiquitous-language` skill writes this file).
3. `GLOSSARY.md`, `CONTEXT.md`, or `docs/**/glossary*`.

- If you find a glossary, use its canonical terms. Replace each "alias to avoid" with its canonical term, and use one term for each concept.
- If you find no glossary, skip this rule and write "none found" in the change log. Do not make a glossary.
- Universal rule 2 ("match the author") still applies to domain terms: keep the author's domain terms unless the glossary replaces them. Change the author's general words to STE words.

### Genre carve-outs

A genre profile overrides STE only in these cases:

- **Reddit**: the author's contractions and their own hedges ("iirc").
- **Tweet / X post**: lowercase is permitted. Keep the "Given … so …" clauses only if they fit in the character limit.
- **Academic**: passive voice where the venue expects it.
- **Blog / newsletter / essay**: first person and digressions are permitted. Sentences still stay at 25 words or fewer.

## Academic article / paper

- **Goal**: precise claims, honest hedges, dense information. Formality stays; puffery goes.
- **Fatal tells here**: "delve", "novel", inflated significance ("crucial implications", "paradigm shift"), rule-of-three in abstracts, negative parallelism in intros ("X is not merely a tool but a fundamental…"), em-dash chains.
- **De-slop moves**: replace significance puffery with the actual finding and effect size. Hedges must be calibrated, not reflexive — "may" because the evidence is genuinely uncertain, not as seasoning. Keep passive voice where the venue expects it; do not inject first person or attitude. Numbers, conditions, and citations beat adjectives.
- **Cadence**: keep each sentence at 25 words or fewer (STE cap); the tell is uniformity, not length. Vary clause structure.

## Tweet / X post

- **Goal**: one idea, said like a person, under the limit.
- **Fatal tells here**: "🧵", "Let that sink in", "Read that again", one-clause-per-line stacking, ending on an engagement question, hashtag clusters, the not-X-but-Y move compressed into 200 characters.
- **De-slop moves**: cut to the single claim. Lowercase is fine if that's the author's habit. No setup ("Hot take:") — just the take. A tweet that states an opinion without insurance reads human; a tweet that balances itself does not.

## Reddit post / comment

- **Goal**: reads like a knowledgeable person typing in a text box, because that's what reddit is.
- **Fatal tells here** (reddit users are the most slop-sensitive audience on the internet): **any** bold in a comment, bullet-point essays, headers, "Hope this helps!", "Great question!", symmetric pro/con framing, em-dash density, perfect paragraphing.
- **De-slop moves**: plain paragraphs, contractions, direct answers first. Mild hedges are human here ("iirc", "I might be wrong but") — but only the author's own. Concrete personal detail ("ran into this on a 2019 Outback") is the strongest human marker; never fabricate it, ask the author or drop it.

## LinkedIn post

- **Goal**: professional but specific. The platform's native style is so slop-adjacent that the bar is: would a colleague forward this without cringing?
- **Fatal tells here**: stacked one-line paragraphs, "Agree?", "Let's connect", broetry rhythm, negative parallelism (this is its natural habitat — scan twice), rule-of-three value statements, "I'm humbled to announce".
- **De-slop moves**: write actual paragraphs. Lead with the concrete event or number, not the lesson. One lesson max, stated once, not echoed in a closer.

## Email

- **Goal**: shortest text that's still warm enough for the relationship.
- **Fatal tells here**: "I hope this email finds you well", restating the recipient's email back to them, three symmetric paragraphs wrapping a one-line answer, "Please don't hesitate to reach out".
- **De-slop moves**: answer in the first sentence. Greeting and sign-off match the existing thread's register. Cut every sentence whose only job is politeness padding except one, if the relationship needs it.

## Blog post / newsletter / essay

- **Goal**: a person with a view, walking the reader through it.
- **Fatal tells here**: "In today's fast-paced world" openers, intro-that-previews-three-sections skeleton, "In conclusion", bold-scattered prose, section headers every two paragraphs, engagement-bait closers.
- **De-slop moves**: open inside the subject (a scene, a number, a claim). Let structure follow the argument instead of a template — real essays have asymmetric sections and loose ends. First person and digressions are allowed; they are how essays sound human. Keep headers only when the piece is long enough to need navigation.

## Marketing / landing copy

- **Goal**: concrete benefit, named audience, zero filler.
- **Fatal tells here**: "seamless", "unlock", "empower", "game-changing", "effortless", rule-of-three feature triplets, false ranges ("from startups to enterprises"), every header a not-X-but-Y.
- **De-slop moves**: replace each abstraction with the mechanism or the number ("Set up in 4 minutes" beats "seamless onboarding"). One verb per claim. Specificity is the whole game; if no specifics exist, that's a product-marketing problem the text can't fix — say so.

## Technical docs / README

- **Goal**: the reader gets unblocked fast.
- **Fatal tells here**: "robust", "powerful", "blazingly fast" without benchmarks, "simply"/"just" before steps that aren't, marketing voice in reference material, emoji section headers.
- **De-slop moves**: imperative mood, exact commands, exact versions, expected output. Adjectives almost to zero. Lists are fine here — docs are the one genre where "Term: definition" bullets are legitimate structure, so don't strip them; strip the puffery inside them.

## Academic-adjacent: cover letters, statements, grant prose

- **Goal**: claims about the author backed by evidence, in formal register.
- **Fatal tells here**: "passionate", "deeply committed", "unique perspective", testament/tapestry vocabulary, rule-of-three trait lists, every paragraph ending with a not-X-but-Y synthesis.
- **De-slop moves**: every trait claim becomes an event ("I led X, which produced Y"). Keep formality; cut self-puffery. The reader has read ten thousand of these — only specifics differentiate.
