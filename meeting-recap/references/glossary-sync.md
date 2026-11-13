# Glossary sync

The workspace keeps **one** glossary at its root (`Glossary.md`). The recap reads from it before writing and feeds what the meeting taught back into it afterwards. The same glossary also feeds the transcription prompt and the `fixes` list, so it pays to keep it current.

Never create a separate `UBIQUITOUS_LANGUAGE.md`. If the `ubiquitous-language` skill is available, borrow its judgement (opinionated canonical terms, tight definitions, domain terms only, conflicts flagged) but not its output path or its habit of rewriting the example dialogue. If no glossary exists, create `Glossary.md` in the format below and tell the user.

## Format

```markdown
# Glossary

{{Scope paragraph: what is live, what is withdrawn and where its terms went.}}

Sources: the [{{meeting}} ({{D Mon YYYY}})](<{{path to recap}}>), …, and the [{{newest meeting}} ({{D Mon YYYY}})](<…>).

Terms marked **(unconfirmed)** are our reading of the source material and still need {{CLIENT}} confirmation.

---

## {{Subdomain}}

| Term | Definition | Aliases to avoid |
|---|---|---|
| **{{Term}}** | {{What it is, 1-4 sentences}}. {{Speaker}}, {{D Mon}}: "{{short quote}}". | {{alias}}, {{alias}} ({{the different thing it means}}) |
| **{{Term}}** | {{What it is}}. The expansion is ours. **(unconfirmed)** | — |

---

## Relationships

- A **{{Term}}** has exactly one **{{Term}}**; …

## Example dialogue

> **Dev:** "{{question using the terms precisely}}"

> **Domain expert:** "{{answer that draws the boundary}}"

## Flagged ambiguities

- **"{{Word}}" is overloaded.** It means **{{A}}** in "{{phrase}}" and **{{B}}** in "{{phrase}}". Use **{{B}}** for the second sense.
- **{{Open question}}?** {{Speaker}}, {{D Mon}}: "{{quote}}". {{Rule to follow meanwhile}}. **(unresolved)**

---

## Superseded — {{old scope}} (withdrawn)

{{Dead vocabulary, verbatim, not maintained. Never use it with the client.}}
```

There's no date column. Provenance goes inline: `({{Speaker}}, {{D Mon}})`, `Firm since {{date}}`, `confirmed {{date}}`. Status markers are bold and in parentheses: `**(unconfirmed)**`, `**(unresolved)**`, or narrower forms like `**(unconfirmed spelling)**`. A marker goes with the term into every document that uses it.

## Procedure (after the recap draft exists)

1. **Load** the whole glossary: terms, alias columns, flagged ambiguities, the superseded appendix. Note any names the workspace instructions ban outright.
2. **Harvest candidates** from the recap, the transcript and the figure labels. Look for domain nouns, acronyms and their expansions, product and system names, named teams and roles, and phrases a speaker defines ("we call it…"). Also look for renames ("not X anymore") and mishearings likely to recur. Skip generic tech words, people's names and one-off phrasing.
3. **Classify** each candidate:
   - **Canonical match**: does the definition still hold? A new fact or a contradiction is an **update**.
   - **Alias match**: use the canonical term in the recap. If the speaker clearly meant something else, it's a **collision**.
   - **Superseded match**: never revive it. Flag it and use the live term.
   - **No match**: a **new** term.
4. **Decide canonical forms.** Be opinionated. Prefer the client's own word unless it's ambiguous or politically loaded. List every other spelling heard as an alias to avoid.
5. **Write rows** next to related terms in the best-fitting table (not appended at the end, not alphabetical). A new `##` subdomain only when four or more new terms fit nowhere else. Add `**(unconfirmed)**` when the expansion, spelling or reading is ours.
6. **Update in place.** Drop `(unconfirmed)` only when a client source confirmed it, and say who and when. When an alias turns out to be a distinct thing, move it out and add a flagged ambiguity: "This glossary used to list X as an alias of Y…".
7. **Flag ambiguities** for each collision, overloaded word, rename, or open disagreement between speakers: a bold verdict line, evidence with speaker and date, the rule to follow, a status marker if open.
8. **Relationships and dialogue.** Add relationship bullets for new structural facts. Append (don't rewrite) one dialogue exchange if the new terms need their boundary shown.
9. **Retire** killed terms with an italic `*Retired {{date}} ({{reason}})…*` note and move them to the superseded appendix.
10. **Sources**: append the meeting to the Sources sentence.
11. **Back-propagate** into the recap and figure labels: canonical terms everywhere, markers carried, banned names gone (even inside quotes).
12. **Record it in the recap.** The Vocabulary row says "updated from this session; see §n". The "Changes to our own records" section lists New / Updated / ambiguities. "Where sources disagree" gets a row for any glossary claim the meeting overturned.
13. **Gate**: if the glossary is governed (the workspace asks before edits to shared records), show the user the diff and wait for approval. Otherwise apply it and list the changes in your reply.
14. **Check**: H1 and table headers unchanged, every new term bold, no term in two tables, no alias that is also a live term, markers bold and in parentheses.
