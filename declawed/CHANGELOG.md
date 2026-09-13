# Changelog

## 1.2.1 — 2026-09-13

### Catalog updates (`references/slop-patterns.md`)

- Puffery: add "load bearing" and "the X that matters most".
- Negative parallelism:
  - Add "the two things it is not".
  - Replace the em-dash-only pattern with the generic `\bnot\b [^.;]{2,60},? but\b`, which also catches "not X but Y" with no dash or no comma.
  - Every pattern now starts with `\b`. The patterns that ended in a trailing space now end in `\b`, so sorting or whitespace trimming can't change what they match. This removes false hits such as "unless about", "more than justice", and "piano keys, no pedals, just".

## 1.2.0 — 2026-09-11

### General language layer

- `references/tones.md` has a new General language section. It applies to every tone except Marketing / landing copy.
  - Conclusions are full sentences that state their evidence and consequence ("Given X, Y, so Z"), not bare point form.
  - Grammar follows the core ASD-STE100 writing rules. Sentences have 25 words at most (20 in procedures), use active voice, and avoid -ing verb forms and phrasal verbs.
  - The rewrite uses the canonical terms from the first glossary it finds. It checks the conversation, then `UBIQUITOUS_LANGUAGE.md`, then `GLOSSARY.md`, `CONTEXT.md`, or `docs/**/glossary*`.
  - A genre profile overrides STE only in the listed carve-outs (reddit, tweet, academic, blog).
- The academic cadence rule now caps sentences at 25 words.
- `SKILL.md` looks for the glossary in Phase 0 and applies the new rules in Phase 2. Phase 4 checks them, and the change log gains a `Language:` line. Fragments are now allowed in marketing copy only.
- `scripts/scan.py` flags each sentence over 25 words as an `STE length` finding.
- New eval case `ste-context-glossary` tests the layer on a terse status email.

### Catalog (`references/slop-patterns.md`)

- Puffery: add "load bearing" and "the X that matters most".
- Negative parallelism:
  - Add "the two things it is not".
  - Replace the em-dash-only pattern with the generic `\bnot\b [^.;]{2,60},? but\b`, which also catches "not X but Y" with no dash or no comma.
  - Every pattern now starts with `\b`. The patterns that ended in a trailing space now end in `\b`, so sorting or whitespace trimming can't change what they match. This removes false hits such as "unless about", "more than justice", and "piano keys, no pedals, just".

## 1.1.2 — 2026-08-09

Add skill-spector baseline
