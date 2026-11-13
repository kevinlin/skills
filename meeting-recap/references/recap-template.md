# Recap template

The internal recap is written for our own team first: blunt, every claim traceable, decided and undecided kept apart. A client-safe copy is derived from it later, on request (last section).

`{{US}}` is our firm and `{{CLIENT}}` the client organisation. `{{rel}}` is the relative path back to the workspace root. Drop `<!-- optional -->` blocks that don't apply.

## Template

```markdown
**Internal to {{US}}. Not for {{CLIENT}} distribution.**

# {{Project}}: {{meeting, lower case}} with {{key person}}, {{D Mon YYYY}}

| | |
|---|---|
| Status | Draft. Built from {{the machine transcript / recall / N slides / N whiteboard photos}}. {{What was checked and by whom; what was not}} |
| Date | {{D Month YYYY}}, {{in the office / online}}, {{duration}} |
| Companion | [{{Slug}}-recap.html](<{{Slug}}-recap.html>) |
| Vocabulary | [Glossary.md](<{{rel}}/Glossary.md>), {{unchanged / updated from this session; see §n}} |
| Source | [transcript](<…>) · [{{slides}}](<…>) · [{{whiteboard}}](<…>) · [recording](<…>) |

Related: [{{earlier meeting}}, {{D Mon}}](<…>) · [{{earlier meeting}}, {{D Mon}}](<…>)

| Who | Side | Role in this session |
|---|---|---|
| {{Full name}} | {{CLIENT}} | {{Title}}. {{What they did in this session}} |
| {{Full name}} | {{US}} | {{Title}}. {{What they did in this session}} |

{{Who was expected but absent ("discussed in the third person"). Timestamps like (0:18:34) point into the transcript. How far the speaker labels and wording can be trusted.}}

<!-- optional: no recording -->
**Reading the tags.** Every claim names its source. **[Board]**: on the whiteboard. **[{{Name}}]**: {{Name}}'s recall on {{date}}. **[Checked]**: looked up by us. **[Inferred]**: our reading, not checked with anyone.

---

## 1. The short version

- **{{Takeaway as one full sentence.}}** {{Evidence in one or two sentences, a short "quote" where the exact words matter}} ({{h:mm:ss}}). See §{{n}}.
<!-- 6-9 bullets. Decisions, conflicts and blockers first. Must stand on its own. -->

## 2. How the session ran

1. {{What opened it}} ({{h:mm:ss}}–{{h:mm:ss}}).
2. {{What was shown or drawn}} (§3, §4).
3. {{How it closed}} (§{{n}}).

## 3. {{Topic, or the finding itself}}

![{{Alt text}}](diagram/F1_{{slug}}.svg)

*Figure 1: {{What it shows}}, re-drawn. {{What was added from the discussion and how it's marked}}. [Original {{slide/photo}}](<captured-image/{{Source-Name}}.png>).*

- **{{Claim as a sentence.}}** {{Detail}} ({{h:mm:ss}}).
- **{{Claim.}}** {{Speaker}}: "{{short quote}}" ({{h:mm:ss}}).

## 4. {{Argued topic}}

{{Speaker}} ({{h:mm:ss}}–{{h:mm:ss}}):

> "{{The statement everything else hangs off.}}"

**Our reading.** {{Interpretation, kept apart from what was said, and what would make it binding.}}

<!-- optional: the meeting revisits something we wrote -->
## {{n}}. What this changes in our {{D Mon}} {{draft}}

| # | Our draft, {{D Mon}} | {{Person}}, {{D Mon}} | Status | What to do |
|---|---|---|---|---|

## {{n}}. Where sources disagree

| # | One source | The other | Status |
|---|---|---|---|
| 1 | {{Source A, date: claim}} | {{Source B, date: claim}} | {{Newer source wins; update X / Open / Ask {{person}}}} |
| {{last}} | Transcript: {{terms as heard}} | {{Best guess}} | Read any quoted line against the audio before it leaves {{US}} |

## {{n}}. Changes to our own records

Made on {{D Mon YYYY}}.

- **Glossary.** New: **{{Term}}**, **{{Term}}**. Updated: **{{Term}}** ({{why}}). {{n}} new flagged ambiguities.
- **Not changed:** {{record}} still says {{X}}. Proposed for {{Owner}}'s approval.

## {{n}}. Open questions

| # | Question | Why it matters |
|---|---|---|
| 1 | {{Question?}} | {{What depends on the answer}} |

## {{n}}. Next steps

- **{{Owner}}:** {{action, specific enough to tick off}}.
- **{{Client person}}:** {{what they committed to}}.

---

*Written on {{D Mon YYYY}} from {{sources}}. {{Reliability: % unattributed, the pair most likely to be swapped, what was spot-checked.}} Figures re-drawn; sources in [diagram/_src/README.md](<diagram/_src/README.md>). Terms follow [Glossary.md](<{{rel}}/Glossary.md>). Internal only.*
```

## How to fill it

- **Sections follow the meeting**, one `##` per topic in the order it came up. Headings are short and can state the finding ("One front end per domain"). 140-310 lines for a 40-120 minute meeting.
- **Every factual claim is traceable.** A timestamp `(h:mm:ss)`, a range `(0:42:04–0:46:44)`, or several `(0:09:11, 0:36:50)`, before the full stop. Lines checked against the audio get `(0:24:31, re-checked)`. Two-part meetings use `(P1 0:54:53)`. No recording: a provenance tag on every paragraph instead.
- **Quotes only where the exact words matter**: short fragments inline, the one statement a section hangs on as a blockquote. Mark mishearings (`heard as "Sonic 5.5"`). Keep colloquial wording in the internal recap and flag any line that must not reach the client.
- **Keep what was said apart from what we think.** Interpretation goes in **Our reading.** paragraphs. Unclear items go in "Not explained:" bullets. Status words: Agreed, Firm, Open, Proposed, Check, "{{Person}}'s call".
- **Name contradictions, don't resolve them quietly.** Between two speakers, between this meeting and an earlier recap, between the meeting and our own documents or glossary. Numbers that don't add up get one blunt line ("20 plus 5 is 25, not 35.").
- **Names**: full names in the Who table, first names in the body, "we/our" for our side. Spellings come from the stakeholder list or org chart, not the transcript.
- **Figures** are numbered in reading order. Each caption says what it was re-drawn from, what was added from the discussion, and links the raw image.
- Uncertain attributions from the transcript header (thin labels, unresolved pairs) carry into the recap: don't quote a thinly attributed line as a named person's position.
- Run the `declawed` skill on the prose if it's available, then re-check that no timestamp or term was lost in the rewrite.

## Client-safe copy (only when asked)

When the user wants a version to email the client, write `Output/Meetings/Sanitised/{{YYYYMMDD_Slug}}.md`, Markdown only:

- **Remove**: the internal banner, metadata table, Related line and footer. Remove every timestamp, `re-checked`/`heard as` note and transcript or model reference, and all figures (mail filters block SVG). Remove talk-time shares, judgemental role notes, Our-reading strategy lines, internal process and politics, sensitive third-party names and the transcript-garble row. Usually remove the internal next steps too.
- **Change**: "The short version" becomes "Summary". "Where sources disagree" becomes "Points to confirm" (`# | Topic | Position from the session | Proposed action`), reworded so no row pins an inconsistency on a named client person. Paraphrase colloquial quotes and soften blunt verbs. Spell dates out in full.
- **Keep**: section order and numbering, the Who table with neutral roles, open questions, `See §n` references.
- Every **(unconfirmed)** term must be confirmed or removed before it reaches a client document, and banned names stay out even inside quotes.
