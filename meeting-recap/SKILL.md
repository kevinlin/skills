---
name: meeting-recap
description: Turn a meeting into a governed recap. A recording becomes a speaker-attributed transcript (local MOSS-Transcribe-Diarize, with optional voice recognition against clips cut from the meeting, and names confirmed against content). Slides and whiteboard photos become light-theme figures. Then a blunt internal recap in Markdown plus a standalone HTML companion, the meeting's new terms merged into the project glossary, and an independent verifier subagent pass before anything is promoted. Use this whenever the user wants a meeting transcribed with speaker identification, a recap, minutes, notes or a summary of a meeting (from a recording, a transcript, whiteboard photos, or their own memory), a whiteboard or slide re-drawn for a recap, a client-safe or sanitised copy of a recap, or a recap verified or promoted. Trigger even when they just drop an .m4a/.mp3 from a meeting folder and say "transcript with speakers", or paste a transcript and say "recap this". Not for YouTube videos or live captioning.
allowed-tools: Read, Glob, Grep, Bash(ffmpeg:*), Bash(ffprobe:*), Bash(rsvg-convert:*)
permissions:
  - env
  - file_read
  - file_write
  - shell
metadata:
  version: 1.2.0
---

# Meeting recap

Turn one meeting into a set of deliverables the team can rely on:

- `<Slug>-transcript.md`: who said what, when, with an honest account of how sure the speaker labels are.
- `diagram/F<n>_<slug>.svg` + `@2x.png`: light-theme re-drawings of what was shown or drawn.
- `<Slug>-recap.md` + `<Slug>-recap.html`: the internal recap and its standalone companion page.
- Glossary updates and a verifier report, then promotion when the user says so.

Recordings are messy and transcripts are confident. Most of this skill exists to stop a fluent, wrong document from reaching people who will act on it.

## Before you start

1. **Read the workspace rules**: `CLAUDE.md` / `AGENTS.md` at the workspace root. They usually define the folders (often `Input/` read-only, `Output/` free, `Artefacts/` governed), the glossary location, names that must never be written, the distribution banner, and what "promote" means. Workspace rules win over this skill.
2. **Read the context**: the glossary, the stakeholder list or org chart (spelling authority for names), and the two or three most recent recaps for this engagement. Their tone, sections and open questions are the baseline you're continuing from.
3. **Name the meeting from its folder**, not from the wording of the request: `YYYYMMDD_Slug` (e.g. `20261009_Team-structure-kickoff`). Work in `Output/Meetings/<YYYYMMDD_Slug>/`, or `meetings/<YYYYMMDD_Slug>/` if the workspace has no convention. Two-part meetings get a subfolder per part.
4. **Confirm what you can't know**, in one batch: who was in the room, who joined online, who was expected but absent, the user's own role if they're in a figure, and which stages they want. Never infer attendance from names spoken in the audio.

Scripts live in this skill's `scripts/` folder (written `<skill>/scripts/` below). They're stdlib Python and need `ffmpeg`, plus `rsvg-convert` for figures. Transcription also needs a local MOSS venv (setup in `references/diarization.md` §1).

## 1. Transcript (when there's a recording and no transcript yet)

Read `references/diarization.md` first. It has the full procedure and the reasons behind each rule. The shape:

```
prep (30-min chunks) → transcribe (local MOSS, labels S01, S02… per chunk) → runs + anchors
→ [optional] enrolment clips on self-identifying content → identify → confirm mapping with the user
→ name → fix → header.md + body.md
```

- Runs locally, so nothing is billed and the audio stays on the machine. If the MOSS venv isn't installed, tell the user what's missing (§1 of the reference). Run `transcribe` in the background and tell the user the expected wait.
- **MOSS separates voices but doesn't know who they are.** Every name needs two kinds of evidence: voice scores propose, the content confirms, the user decides. `identify` is optional. Without it, map labels from content anchors and the user's confirmation alone.
- **The worst failure is a wrong enrolment clip**, because it produces a fluent, wrong transcript: a confident name on every turn of someone else's label. Cut clips on content only that person could say. Treat "no proposal", `too close` and `mixed` as results, not as failures to force through. Read both ends of the talk-time table.
- Corrections from the user ("0:07:24-0:07:40 is Chen") become `overrides` in `meeting.json`, followed by a re-run from `name`. Never hand-edit the transcript body.
- Finish with the transcript header (`references/diarization.md` §6) and `method.md`. Then write a short report: the talk-time table, how each name was settled, the unattributed share, Unattributed turns that need a name (as questions), names and terms not confirmed, and the MOSS run time from `moss/runs.jsonl`.

**No recording?** Reconstruct from the whiteboard photos and the user's memory. Interview them one question at a time, free recall before specific prompts, and show the raw photo before any re-drawn figure so the figure doesn't steer their memory. Keep verbatim notes in `interview-notes.md`. Every claim in the recap then carries a provenance tag (`[Board]`, `[Name]`, `[Checked]`, `[Inferred]`) instead of a timestamp, and Status says "Reconstructed. No recording."

## 2. Figures (when slides, whiteboards or a structure deserve one)

Read `references/diagrams.md`. Light theme, 12px minimum, solid = on the source, dashed = from the transcript. Copy `scripts/svgkit.py` into `diagram/_src/`, write `_figs.py` there, render the `@2x.png` files, and look at every PNG. Ask the user about unreadable words instead of guessing. If they invoke a diagram skill that defaults to dark (baoyu-diagram does), keep its layout rules and override its colours and type scale as the reference shows. A screenshot of a page or tool shown in the meeting can go in as-is, as a snapshot figure (`references/html-companion.md`), instead of being re-drawn.

## 3. The recap

Read `references/recap-template.md` and follow it. In short:

- Line one is the internal banner, followed by the metadata table, the Who table, then **The short version**: 6-9 bold-lead bullets, decisions and conflicts first.
- Topic sections follow the meeting's order. Every factual claim gets a timestamp (or a provenance tag), and interpretation goes in **Our reading.** paragraphs.
- **Where sources disagree** names contradictions with earlier recaps, our documents and the glossary. Then Open questions and Next steps with owners.
- Use canonical glossary terms. Carry `(unconfirmed)` markers, and never write a banned name, even inside a quote.
- Attribution doubts in the transcript header carry over: don't quote a thinly attributed line as a named person's position.

If the `declawed` skill is available, run it on the prose, then check that no timestamp, tag or term was lost in the rewrite.

## 4. Glossary sync

Read `references/glossary-sync.md`. Harvest the meeting's new and changed terms, merge them into the workspace's single glossary in its existing format, flag collisions, and record the changes in the recap's "Changes to our own records" section. If the glossary is governed, show the diff and wait for approval before saving. Never write a separate `UBIQUITOUS_LANGUAGE.md`.

## 5. HTML companion

Read `references/html-companion.md`. Hand-write `_src/body.html` from the finished `.md` using the component vocabulary there, then:

```sh
python3 <skill>/scripts/build_html.py _src/body.html <Slug>-recap.html --title "<Short name>" --description "<One sentence>"
```

This fills `assets/recap-shell.html` (the settled styling: fonts, themes, sticky contents, figure lightbox) and inlines each figure. Don't restyle it unless the user asks. If you have a browser tool, check the page in light and dark mode and at a 390px width: wide tables are what usually cause horizontal scrolling. Keep the `.md` and `.html` in step by hand. They carry the same claims.

## 6. Verify before anyone calls it done

1. Run the mechanical checks and save the evidence:
   ```sh
   python3 <skill>/scripts/check_recap.py <Slug>-recap.md --transcript <Slug>-transcript.md \
     --ban "<banned name>" > check.txt
   python3 <skill>/scripts/check_recap.py <Slug>-recap.md --transcript <Slug>-transcript.md --evidence > evidence.txt
   ```
   Fix every FAIL first.
2. Spawn a **fresh** subagent (general-purpose, read-only) with the prompt in `agents/recap-verifier.md`, its `{{…}}` inputs filled in with real paths. It must not inherit the context that wrote the recap. Independence is the point. Run it in the **foreground**, so its verdict comes back in the same call. Backgrounded verifiers have gone silent: one round never reported, and the recap sat waiting for hours.
3. Fix what it finds, then spawn a fresh verifier for a scoped re-check, listing the fixes and asking it to look for regressions in the touched lines. Repeat until it returns `PASS`. Real runs have taken two or three rounds (9, then 5, then 0 defects). If a round comes back without a verdict, spawn one replacement. If that fails too, stop and report the recap as not verified, with the last defect list. Changes to figures or to what the user told you need the user's OK.
4. If your environment can't spawn subagents, do a separate verification pass yourself: re-read the sources cold and work through the same checklist. Tell the user it was self-verified, which is weaker.

Tell the user how many rounds it took and what the defects were, briefly.

## 7. Promote (only on an explicit request)

Promote only when the user says "promote", "publish", "save as artefact", "finalize", or moves the files themselves. Never offer it as done before the verifier passes.

- Copy the deliverables only: recap `.md` and `.html`, `diagram/` (with `_src/`), `captured-image/`. Interview notes, plans, `_src/body.html` and the transcription run stay in `Output/`. Enrolment clips (`refs/`) and voice samples (`ident/`) are biometric data: they never get promoted.
- Ask before writing into a governed folder, compare the copies byte for byte, and re-run `check_recap.py` on the promoted copy. Links that worked from `Output/` often break one level over: one published recap still points at spot-check files left behind.
- Repoint inbound links, such as the glossary's Sources line. Never delete anything you didn't create; if something in the target looks stray, say so.

## Client-safe copy (on request)

Use the rules at the end of `references/recap-template.md`: Markdown only, no figures, no timestamps or transcript references, no metadata or footer, quotes paraphrased, contradictions reworded as "Points to confirm". End with a grep sweep for leaks and a short list of things the user should decide before sending.

## Report back

Keep the final message short:

- What exists and where.
- The transcript's attribution numbers.
- Verifier rounds.
- Open questions that need the user, and what's waiting for their approval: glossary diff, promotion, figure changes.
