# meeting-recap

Turns one meeting into a set of deliverables the team can rely on. The set is a speaker-attributed transcript, light-theme figures re-drawn from slides and whiteboards, an internal recap in Markdown with a standalone HTML companion, and glossary updates. An independent verification pass runs before anything is promoted.

It came out of about ten recaps on a real client engagement. Most of what's in here is a rule someone learned the hard way. One wrong voice clip gave a client architect's whole walkthrough to someone else, fluently. Diagram skills default to a dark theme with 8px labels. A recap linked files that broke when it was promoted.

## What you need

- Python 3 (stdlib only), `ffmpeg`/`ffprobe`, and `rsvg-convert` (`brew install librsvg`) for figure PNGs.
- For transcribing recordings: a local [MOSS-Transcribe-Diarize](https://github.com/OpenMOSS/MOSS-Transcribe-Diarize) venv, plus `speechbrain` in it for the optional voice recognition. Setup is in `references/diarization.md` §1. Audio stays on the machine, and there's no API key.
- JetBrains Mono installed locally, so figure PNGs render with the right font widths.

## How it runs

| Stage | Output | Gate |
|---|---|---|
| Transcript | `<Slug>-transcript.md`, `method.md`, `identify.json` | Cast confirmed before the run; label-to-name mapping confirmed before `name` |
| Figures | `diagram/F<n>_<slug>.svg` + `@2x.png`, `captured-image/` | Unreadable words asked, not guessed |
| Recap | `<Slug>-recap.md` | |
| Glossary sync | edits to the workspace's single `Glossary.md` | Diff approved when the glossary is governed |
| HTML companion | `<Slug>-recap.html` | |
| Verify | `check.txt`, `evidence.txt`, verifier report | Loops until `PASS` |
| Promote | copy into the governed folder | Only on an explicit "promote" |

## Files

- `SKILL.md`: the workflow the agent follows.
- `references/diarization.md`: the transcription pipeline and its failure modes.
- `references/recap-template.md`: the recap skeleton, writing rules, and the client-safe copy rules.
- `references/diagrams.md`: the light-theme figure spec and workflow.
- `references/glossary-sync.md`: the glossary format and the merge procedure.
- `references/html-companion.md`: the HTML body vocabulary for the shell.
- `agents/recap-verifier.md`: the prompt for the independent verifier subagent.
- `scripts/diarize.py`: the transcription pipeline (prep, transcribe, anchors, runs, clip, identify, name, fix, spotcheck). Stdlib; shells out to the MOSS venv.
- `scripts/embed.py`: ECAPA speaker embeddings for `identify`. Runs in the MOSS venv, not stdlib Python.
- `scripts/svgkit.py`: figure helpers. Copied into each meeting's `diagram/_src/`, and they refuse text under 12px.
- `scripts/build_html.py`: fills `assets/recap-shell.html` with a body and inlines the figures.
- `scripts/check_recap.py`: mechanical checks (links in the `.md` and the `.html`, figures, banned names, timestamps, HTML slots) and the timestamp evidence file the verifier reads.
- `tests/`: `python3 tests/test_diarize.py` (naming rules, plus an offline round trip against a stand-in MOSS venv) and `python3 tests/test_check_recap.py`.
- `evals/`: the skill-up suite the SkillGantry evaluate gate runs, on synthetic fixtures (recap from a transcript, verify planted defects, client-safe copy). Edit `evals/fixtures/src/`, then run `python3 evals/fixtures/build_manifests.py`; `bash evals/fixtures/scripts/selftest.sh` checks the judges.

Up to 1.0.1 the transcript stage ran on OpenAI's `gpt-4o-transcribe-diarize`, which shuts down on 26 Feb 2027. Transcripts made with it stay valid.
