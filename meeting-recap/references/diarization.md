# Diarization: recording to speaker-attributed transcript

Everything here runs through `scripts/diarize.py` from the meeting's run directory. MOSS-Transcribe-Diarize does the transcription, timestamps and speaker separation in one local pass and labels voices `S01`, `S02`, …. Optional voice recognition (`identify`, SpeechBrain ECAPA) proposes which label is which person. Names go on only after content and the user agree. Each rule below cost a real meeting a wrong transcript or a wasted hour before it was written down.

## Contents

1. Setup
2. The run, step by step
3. Naming the labels
4. Reading the result
5. Text quality: fixes and spot-checks
6. Transcript header
7. Time, failures and privacy

## 1. Setup

One-off install, outside any workspace (about 3 GB with torch). It goes in `~/.local/share`, not `~/.cache`: cleaners empty `~/.cache`, and this is an installed tool.

```sh
git clone https://github.com/OpenMOSS/MOSS-Transcribe-Diarize.git ~/.local/share/moss-transcribe-diarize/repo
cd ~/.local/share/moss-transcribe-diarize/repo
uv venv --python 3.12 .venv && source .venv/bin/activate
uv pip install -e ".[torch-runtime]" --torch-backend=auto
uv pip install speechbrain          # only for identify
```

- `diarize.py` stays stdlib Python and shells out to that venv. `MOSS_VENV` overrides where it looks (default `~/.local/share/moss-transcribe-diarize/repo/.venv`).
- `MOSS_MODEL` is a Hugging Face id (the default, downloaded on first use) or a local folder. A local folder must be a complete snapshot: weights plus `chat_template.jinja` and the three `*_moss_transcribe_diarize.py` files. Model folders exported by other apps have shipped without those and fail with "does not appear to have a file named configuration_…" or "does not have a chat template".
- `MOSS_DEVICE` defaults to `mps` on Apple silicon (about 4x faster than CPU), `auto` elsewhere. `MOSS_VLLM_URL` sends inference to a vLLM server on a CUDA box instead.
- `ffmpeg` and `ffprobe` on PATH.
- If the venv or model is missing, tell the user what to install. Don't install it into their workspace.
- Take the meeting's identity (date, slug, parts) from the recording's path, not from the wording of the request. Requests get copy-pasted from the last meeting.
- Get the **cast from the user**, never from the audio: who was in the room, who joined online, who was expected but absent, who barely spoke. A spoken name identifies the person being addressed or discussed, not someone present. One transcript gave a colleague's turns to someone who wasn't there because his name came up.
- Write `meeting.json` in the run directory:

```json
{
  "cast": ["Ana", "Ben", "Chen"],
  "anchors": ["my team", "I joined", "our firm"],
  "hotwords": ["Client Connect", "MFE", "RTK Query", "JWE"],
  "speakers": {},
  "fixes": [],
  "overrides": []
}
```

`cast` spellings are the canonical ones from the stakeholder list or org chart. `hotwords` are product and domain terms and acronyms from the glossary, the stakeholder list and slides shown in the meeting; the cast is added to them automatically. `speakers` stays empty until section 3. `fixes` fills in during section 5.

## 2. The run, step by step

```sh
D=<skill>/scripts/diarize.py
python3 $D prep "<path to recording>"     # audio-16k.mp3 + chunks/c0.mp3, c1800.mp3, ...
python3 $D transcribe                     # MOSS per chunk -> moss/c*.json   (background it)
python3 $D runs                           # talk time per label + clean 3-10 s runs
python3 $D anchors > anchors.txt          # <<< marks segments where a name or anchor is spoken
python3 $D clip Ana 0:28:10               # enrolment clips, cut from this meeting (section 3)
python3 $D identify                       # optional: voice scores per label -> identify.json
#   ... confirm the mapping, write it to meeting.json "speakers" ...
python3 $D name body-named.md             # labels -> names, overrides applied
python3 $D fix body-named.md body.md
cat header.md body.md > <Slug>-transcript.md
```

- **`prep` cuts 30-minute chunks.** MOSS's labels are only consistent within one request, so a longer chunk would be nicer, but a single pass over a 66-minute meeting stopped mid-word at 0:47. It exited 0 with a valid-looking file, ran 40 minutes and used 20 GB. With chunks, labels are per chunk (`c0-S02`, `c1800-S02`) and each one is named separately. The same person usually has a different label in each chunk. `--chunk 0` (one request) is fine for meetings under about 40 minutes. `prep` refuses a directory that already holds results, so old output is never reused against re-cut audio.
- **Run `transcribe` in the background and tell the user the expected wait.** On an M5 Pro (MPS) a 30-minute chunk takes about 14 minutes, so a one-hour meeting takes about half an hour. A 3-minute excerpt took 29 s, half of it model load. `moss/runs.jsonl` records the audio length and wall time of every attempt. Put them in `method.md`.
- `transcribe` checks the result covers the chunk. A run that stops early is a failure, not a short meeting: the `.err` file says where it stopped. Re-run with `--max-new-tokens` raised, or re-prep with a smaller `--chunk`. If the recording really ends in a long silence, say so in `method.md`. Don't shorten the audio to make the check pass.
- Expect worse separation in a room than online. Similar voices at similar distance from one mic are the ones that blur.

Record the exact commands, the enrolment clip table (name, start, the words that anchor it), the identify table and any findings in `method.md` in the run directory. The transcript header links to it.

Two-part meetings (a morning and an afternoon sitting) get one run directory per part and their own transcripts. Don't merge them, and don't touch a folder another session is working in.

The transcript stays in the run directory. If the workspace keeps transcripts next to their recordings (often a read-only `Input/` folder), ask before copying it there.

## 3. Naming the labels

MOSS knows that `S03` is one voice. It does not know who that is. Naming is where a fluent, wrong transcript comes from, so every name needs two kinds of evidence: **the voice scores propose, the content confirms, the user decides.**

### Content evidence (always)

Read `anchors.txt` and the `runs` output. Look for turns only that person could say: "This is based on my ideation" about their own diagram, an answer straight after "What about your local setup, Priya?", someone describing their own team's setup. A name spoken aloud usually identifies the person being *addressed*, not the speaker. A reply to a named question is weak on its own: "Sam, do you have time after?" was answered by someone else.

Without voice recognition, this is the whole method, chunk by chunk (`c0-S02` and `c1800-S02` are unrelated): propose a mapping from anchors, show the user the label table with talk-time shares and two or three anchor quotes per label, and wait for them to confirm.

### Voice evidence (`identify`, optional)

- **Enrolment clips come from this meeting**, cut with `clip <Name> <start>` (2-10 s, 9.5 s default) on content only that person could say. Use `runs` to find clean single-voice stretches near the anchor. Two or three clips per person from different moments beat one. Clips from another recording are untrusted: a different room and mic moves the scores more than a different voice does.
- **A wrong enrolment clip is the most expensive mistake in this pipeline, and it looks like success.** A clip of the wrong voice doesn't produce "Unknown". It produces a confident, wrong name on every turn of somebody's label. Cut it on content, then check that the clip's own label is the one it matches.
- If someone only speaks in short bursts and has no usable clip, leave them unenrolled. Never invent a clip.
- `identify` scores up to 12 segments per label, spread across the meeting, and leaves out overlapped speech. It proposes a name only when the mean score clears the threshold, beats the runner-up by the margin, and at least three quarters of the sampled segments agree. Otherwise it says why: `below threshold`, `too close: Ana 0.52 vs Chen 0.49`, or `mixed: Ana 8/12, Ben 4/12`.

The defaults (threshold 0.45, margin 0.10, agreement 0.75) were checked on one real in-office meeting, five people on one room mic. On that meeting every one of 15 labels got the right name. Correct names scored 0.52-0.76, the best wrong name 0.39, and a person whose clips were removed scored at most 0.23 against everyone else, so they stayed unnamed. Two engineers from one team were the closest pair at 0.35-0.39 cross-score. Expect a different room or a phone line to move these numbers. If a label you're confident about scores just under the threshold, show the user the table rather than lowering `--threshold` until it passes.

Reading the `identify` table:

- **No proposal is a result, not a failure.** An unenrolled person, a guest on a phone line, or two similar voices should come out unnamed. Leave the label `Unattributed` unless content settles it.
- **`mixed` means MOSS put two voices under one label.** No mapping fixes that. Name the label after the majority only if the user agrees. Then list the dissenting stretches (`dissent` in `identify.json`) and add an override for each one the words settle. Leave the rest flagged in the header.
- **The same name proposed for two labels** is usually one person whom MOSS split into two voices (they moved, or switched from laptop to room mic). It can also be a clip that matches too broadly. Check the content of both labels before mapping both.
- **Check both ends of the talk-time table** against what you know about who was there and their role. A name holding far too much talk time took someone else's label. A name holding almost nothing probably has the wrong clip.
- Voice scores are evidence about a sample, not about every segment. A label the user confirms can still carry someone else's short interjections. That's what the overrides and the header caveats are for.

Then put the confirmed mapping in `meeting.json` `"speakers"` and run `name`. Labels you leave out become `Unattributed`.

**Hand overrides go in `meeting.json`, not into the markdown.** Each one is `[start, end, "Name", "why"]`. Use one only where the words settle who is speaking (someone talking *about* X, or being answered by X), or where the user confirms it. Edits to `body*.md` don't survive the next `name`. When the user corrects an attribution ("0:07:24-0:07:40 is Chen"), add an override and re-run `name` onwards.

`name` ends by listing Unattributed turns of 5 s or more. Put the ones that carry content to the user as questions ("0:17:07, 'Okay. So two questions.': who is this?"), in one batch.

## 4. Reading the result

- Talk time in `runs`, `identify` and `name` is summed from segments, so pauses inside a turn don't count.
- **Unattributed** covers labels nobody could name, labels under 6 s that `identify` couldn't score, and anything you chose not to name. Report its share and what's in it, and don't guess it away.
- Compare the label count to the cast. More labels than people usually means MOSS split someone (see above), or picked up a voice from a video or a speakerphone. Fewer labels than people means it merged two voices. That's the `mixed` case, and the merged person's lines carry someone else's name until overrides fix them.

## 5. Text quality: fixes and spot-checks

- MOSS spells acronyms as spaced capitals ("R T K query", "M F E"). `name` rejoins them ("RTK query"), but leaves "I I guess" alone.
- `fix` applies `meeting.json` `fixes` (regex, replacement) and reports hits per rule. It's free to re-run. Every rule must be a mishearing **seen in this recording**. Audit rules inherited from an earlier meeting against this cast. One old rule rewrote a first name into a similar-sounding one and would have renamed a real attendee; another would have invented someone who wasn't there.
- A fix is for a mishearing you're sure of: the glossary, the slides or the stakeholder list name the real term, and the sentence leaves no doubt. Scope each rule to the phrase you saw ("clock code"), never to a common word on its own. Rules like `contractors → contract` or `Jess → Jest` rewrite correct speech elsewhere, and Jess may be a person. When you're unsure, leave it as heard and list it under "Names and terms not confirmed". A dozen solid rules beat fifty guesses: nobody can check a guess without the audio.
- Hotwords help MOSS spell terms but can also pull a near-sound towards them. `spotcheck out.md 0:25:55-0:26:30@label` re-transcribes a window. Add `--no-hotwords` when the disputed term is a hotword, so the hint can't bias the answer. If the two still disagree, leave it marked unresolved and say which source would settle it.

## 6. Transcript header

`header.md` goes on top of `body.md`. It contains:

1. Line one: the distribution note if the workspace uses one ("Internal to <Firm>. Not for <Client> distribution.").
2. A title with the date and "(machine transcript)".
3. Metadata table: Status (e.g. "Draft, machine transcript. Speaker labels checked against content anchors, text not checked line by line"), Date, Owner, Companion, Vocabulary (link to the glossary), Source (link to the recording, its duration, in-room/online, mic setup), Method (link to `method.md`).
4. Who was in the room, with organisation, plus links to any slides or whiteboard photos shown.
5. "Rough order": 4-8 time-boxed blocks (`0:05-0:16, topic.`), each one or two sentences.
6. "Read the attribution with care": the talk-time table, how each name was settled (voice score and consistency, content anchor, user confirmation), labels left unnamed and why, every hand override with who confirmed it, and passages where the label is thin.
7. "Names and terms not confirmed": every name or term heard but not verified, with its timestamp and how it was heard.

## 7. Time, failures and privacy

- Nothing is billed, but a long meeting takes a while. Tell the user the expected wait before starting, and report at milestones (`transcribe` prints one line per chunk). Don't post a "still waiting" message every minute.
- Failed chunks write `moss/<chunk>.json.err` with the reason, never a broken `.json`, and the command exits non-zero. Fix the cause, then re-run the **same** command: finished chunks are skipped.
- `anchors`, `runs`, `identify` and `name` refuse a run that's missing chunks, so a partial run fails loudly instead of naming half a meeting.
- **Audio stays on the machine** with the default local setup. `MOSS_VLLM_URL` sends it to that server. If the server isn't the user's own, ask before using it. The ECAPA model is downloaded once from Hugging Face. Audio never goes there.
- **Enrolment clips and voice embeddings are biometric data.** Cut them from this meeting for this meeting only. Keep `refs/` and `ident/` in the run directory, never promote them, and don't build a voice library across meetings unless the people in it have agreed to that.
