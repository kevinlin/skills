# Slop Pattern Catalog

Detection patterns for the Declawed scan. Patterns are written for `grep -Ein` (extended regex, case-insensitive, line numbers) so they can be run literally against a file:

```bash
grep -Ein -f /dev/stdin draft.txt <<'PATTERNS'
<paste patterns from a section below, one per line>
PATTERNS
```

`scripts/scan.py` parses the regex out of the fenced blocks in sections 1-4 below and runs them for you, so this file is the single source of truth for the catalog — keep one pattern per line inside those fences and no prose. When the text only exists in conversation, apply each pattern by hand. A match is a *finding*, not an automatic deletion — every finding goes through the Phase 2 triage in SKILL.md. Density matters: one em dash is nothing; one em dash plus a negative parallelism plus "delve" in the same paragraph is a verdict.

## 1. Negative parallelism — the "not X but Y" family

The highest-priority category. LLMs reach for the negation-then-assertion move roughly once a paragraph; humans use it occasionally and deliberately.

```
not (just|only|merely|simply|solely) [^.;]{2,80}(but|it'?s| — )
isn'?t (just|only|merely|simply|about) 
it'?s not (a|an|the|that|about|just) [^.;]{2,80}(it'?s|but)
(is|was|are|were)n'?t about [^.;]{2,60}\. (it|this|that)'?s about
less about [^.;]{2,60}(than|and more about)
more than (just|a mere|simply) 
not because [^.;]{2,80}but because
the (question|point|issue|problem|goal|real [a-z]+) is(n'?t| not) (whether|about|just|if)
(doesn'?t|don'?t|didn'?t|won'?t) (just|merely|simply) [^.;]{2,80}(it|they|he|she|we) 
no [a-z]+, no [a-z]+(, no [a-z]+)?[,.]? just 
— not [^—.;]{2,60}, but 
not only [^.;]{2,80}but (also )?
we'?re not (just )?(talking about|looking at|dealing with)
gone are the days
(here|this)'?s the (thing|kicker|catch|twist)
```

Rhetorical-question variant (regex-resistant; check by hand): a one-line question immediately answered by a one-word or one-clause sentence. *"The result? Chaos."* / *"Sound familiar?"*

## 2. Puffery and inflated vocabulary

Single words and stock phrases that spike in LLM output. Each is fine in isolation; two or more per page is a finding. The fix is the plain word or the concrete fact the word was hiding.

```
\b(at the end of the day)\b
\b(boasts)\b
\b(commendable)\b
\b(compelling)\b
\b(cutting.?edge)\b
\bdeep(er)? dive\b
\bdefend(s|ing)?\b[^.;]{0,25}\bto (management|leadership|stakeholders?|(a |the |your )?clients?)\b
\b(delve|delving)\b
\belevate(s|d)? (the|your)\b
\bembark(s|ed|ing)? on\b
\bempower(s|ing|ment)?\b
\bever.?(evolving|changing)\b
\bfast.?paced (world|environment)\b
\bfoster(s|ing)?\b
\bfram(e|ed|ing) (it |this |that )?as\b
\bgame.?chang(er|ing)\b
\bharness(es|ing)? the\b
\b(holistic)\b
\b(in today'?s)\b
\b(intricate)\b
\b(landscape|realm|sphere) of\b
\bleverage(s|d)?\b
\b(mechanical floor)\b
\bmeticulous(ly)?\b
\bnavigat(e|ing) the\b
\b(operating loop)\b
\b(pivotal|paramount|crucial)\b
\bplays? a (vital|key|crucial|pivotal) role\b
\bresonate(s|d)?\b
\brich (cultural )?(heritage|history|tradition)\b
\b(robust)\b
\bseamless(ly)?\b
\b(seismic|monumental|transformative) (shift|change)\b
\bshowcas(e|es|ing)\b
\b(synergy)\b
\b(tapestry)\b
\b(testament|stands as)\b
\b(two|three|both|multiple|different|separate) lenses\b
\bunderscore(s|d)?\b
\bunlock(s|ing)? (the|your)\b
\b(unwavering)\b
\b(vibrant)\b
\b(when it comes to)\b
```

## 3. Hedging, both-sidesing, throat-clearing

The tell is reflexive balance: every claim gets a softener, every opinion gets a counterpoint. Commit or cut.

```
it'?s (worth|important) (to note|noting|to remember|to consider)
(that|it) (being )?said,
while (it'?s|this is) (true|important)
arguably
in many ways
to some (extent|degree)
on the other hand
at its core
in essence
essentially,
ultimately,
in conclusion
in summary
to sum(marize| up)
overall,
in the end,
needless to say
as (we|you) (can see|know|all know)
let'?s (dive|unpack|explore|take a (look|closer look))
whether you('re| are) [^.;]{2,60} or 
```

## 4. False ranges and rule-of-three

**False range** — a "from X to Y" with no actual spectrum between X and Y:

```
from [^.;]{3,50} to [^.;]{3,50}
```

**Rule of three** — LLMs default to triplets to make thin analysis look thorough. Regex only catches the simplest shape; check lists by hand too.

```
\b\w+, \w+, and \w+[.!?]
\b(\w+ \w+), (\w+ \w+), and (\w+ \w+)
```

Both regexes deliberately over-match — triage per SKILL.md Phase 2.

## 5. Punctuation and formatting

Em dash: not banned — humans use it. Findings are about **density** and the contrast move:

- More than ~1 em dash per 150 words.
- Two em dashes in one sentence.
- `— not X, but Y` (already in section 1).
- Em dash used for punchy emphasis where a comma works: `[a-z] — [a-z][^—]{1,25}\.$`

Other formatting tells (check by hand; most regexes here are layout-dependent):

- **Bold scattered through prose** like a textbook highlighting itself: `\*\*[^*]{2,40}\*\*` appearing more than ~once per 3 paragraphs of body prose.
- **"Term: definition" bullets**: `^[-*] +\*\*[^*]+:?\*\*:? ` — the signature LLM list shape.
- **Emoji headers/bullets** (🚀, ✅, 💡): needs PCRE, not `-E` — `LC_ALL=C.UTF-8 grep -Pn '^\s*[-*#]+\s.*[\x{1F300}-\x{1FAFF}\x{2600}-\x{27BF}]' draft.txt`.
- **Headers on short texts** — section headers on anything under ~400 words.
- **The tidy skeleton** — intro that previews three points, three matched sections, conclusion that restates them. Resolves too neatly; real writing has loose ends.
- **Numbered lists where a paragraph would do.**
- Curly quotes/apostrophes in a context where the author types straight ones (mixed within one text is the stronger tell).

## 6. Cadence and statistical shape

No regex; measure or eyeball.

- **Uniform sentence length** (the single strongest current tell): a run of 3+ consecutive sentences within ±4 words of each other, paragraph after paragraph of 18–24-word sentences. Quick measurement on a file:

  ```bash
  tr '\n' ' ' < draft.txt | sed 's/[.!?] /\n/g' | awk '{print NF}'
  ```

  Human prose mixes 4-word sentences with 30-word sentences. Variance should be obvious at a glance.
- **Uniform sentence shape**: every sentence opens subject-first; no fragments, no questions, no inversions.
- **Uniform paragraph length**: every paragraph 3–4 sentences.
- **Low specificity**: "many companies", "studies show", "experts agree", "recent research", "various factors" — generic where a human who knew the material would name names, numbers, dates. (Fix only with real specifics; never invented ones.)
- **No friction**: nothing colloquial, no aside, no opinion held without a softener, nothing that risks being disagreed with.

## 7. Genre-specific instant tells

Covered in detail in [tones.md](tones.md); the headline items:

- **Reddit/forums**: bold mid-comment, bullet-pointed comments, "Hope this helps!", perfectly balanced takes.
- **Tweets/X**: "🧵", "Let that sink in", line-broken one-clause-per-line cadence, ending on a question to drive engagement.
- **LinkedIn**: one-sentence paragraphs stacked vertically, "Agree?", the not-X-but-Y move (its natural habitat).
- **Academic**: "delve", "novel insights", puffed significance claims ("crucial implications for the field"), citation-free superlatives.
- **Email**: "I hope this email finds you well", restating the recipient's question back at them, three-paragraph symmetry for a one-line answer.
