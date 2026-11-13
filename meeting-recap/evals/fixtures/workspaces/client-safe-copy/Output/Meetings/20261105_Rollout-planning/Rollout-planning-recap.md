**Internal to Northwind Consulting. Not for Harbour Freight distribution.**

# Tidewater: rollout planning with Ingrid and Tomasz, 5 Nov 2026

| | |
|---|---|
| Status | Draft. Built from the machine transcript. Speaker labels checked against the stakeholder list; wording not checked against the audio. |
| Date | 5 November 2026, in the office and online, 25 minutes |
| Companion | [Rollout-planning-recap.html](<Rollout-planning-recap.html>) |
| Vocabulary | [Glossary.md](<../../../Glossary.md>), updated from this session; see §8 |
| Source | [transcript](<../../../Input/Meetings/20261105_Rollout-planning/Rollout-planning-transcript.md>) |

Related: [Tidewater scope kickoff, 29 Oct](<../../../Artefacts/Meetings/20261029_Tidewater-scope-kickoff/Tidewater-scope-kickoff-recap.md>)

| Who | Side | Role in this session |
|---|---|---|
| Ingrid Solheim | Harbour Freight | Head of Depot Operations. Raised the peak freeze and argued for Eastgate in wave one. |
| Tomasz Wieczorek | Harbour Freight | IT Infrastructure Lead, online. Set the IT conditions for the shadow run and for Eastgate. |
| Callum Reeve | Northwind Consulting | Engagement Lead. Ran the session and proposed the shadow run. |
| Mei-Ling Tan | Northwind Consulting | Delivery Manager. Owns the plan and the dock-door profile template. |

Dalia Nasser (programme sponsor) and Rohan Mistry (Northwind) were expected but absent; both are discussed in the third person. Timestamps like (0:04:30) point into the transcript. Two short turns (0:11:05, 0:19:40) are unattributed and carry no position.

---

## 1. The short version

- **Wave-one cutover cannot be 30 November.** Ingrid: the peak freeze runs from 23 November to 8 January and nothing changes in a depot during it (0:04:30). The kickoff plan did not know. See §3 and §7.
- **Decided: Southport runs a two-week shadow run from Monday 11 January 2027.** Cutover is not before Monday 25 January, and only if the exit test passes. Ingrid and Tomasz both agreed (0:09:20–0:09:52). See §4.
- **Eastgate in wave one is open.** Ingrid wants it in wave one; Tomasz says IT cannot support it before the site survey and probably not before February (0:10:25–0:13:52). If they are still split after 20 November it goes to Dalia. See §5.
- **Southport handles about 1,800 parcels on a peak night.** Ingrid used it to show why the rollback window of about five in the morning is tight (0:02:36).
- **The exit test is strict.** Tidewater's daily parcel counts must match the legacy tracker's counts (0:06:29). See §4.
- **Dalia has not seen the new dates.** She still has to sign off, and Callum sends her the revised plan by 10 November (0:10:10, 0:20:44).

## 2. How the session ran

1. Opened on the kickoff plan and what a cutover night involves (0:00:04–0:02:36).
2. The peak freeze surfaced when Callum asked about 30 November (0:03:41–0:05:24).
3. The shadow run was proposed and decided (0:05:42–0:10:10).
4. Eastgate was argued and left open (0:10:25–0:14:20).
5. Dock-door profiles, the cutover weekday, training and owners (0:14:40–0:25:12).

## 3. The freeze moves the cutover

- **The peak freeze runs from 23 November to 8 January.** Nothing changes in a depot in that window: no new systems, no new scanners, no process changes. Ingrid (0:04:30).
- **30 November is inside it.** The cutover date in the kickoff recap no longer holds (0:04:30).
- **The earliest wave-one cutover is after 8 January,** a slip of more than two months against the plan sent to Dalia. Mei-Ling (0:05:24).

**Our reading.** The freeze is in Harbour Freight's calendar every year, so the 30 November date was never achievable. We built the kickoff plan without checking it.

## 4. The shadow run at Southport

- **Decided.** Southport only, a two-week shadow run starting Monday 11 January, cutover not before Monday 25 January and only if the exit test passes (0:09:20). Ingrid: "No, agreed." (0:09:48). Tomasz agreed from IT and will raise the change ticket once the freeze lifts (0:09:52).
- **What a shadow run is.** The legacy tracker stays the system of record while Tidewater receives a copy of every live scan. Callum (0:05:42).
- **The exit test:** Tidewater's daily parcel counts match the legacy tracker's counts. Mei-Ling (0:06:29).
- **Strict on purpose.** Ingrid asked for a strict test because Saltmarsh Freight lost two weeks re-keying scans after a similar exercise (0:08:20).
- **No extra floor staff.** The comparison is automated, so nobody extra is needed at Southport. Mei-Ling (0:08:00).
- **A condition from IT.** Tomasz treats the shadow run as a precondition: "Without it we don't go." (0:23:30).

**Our reading.** The two extra weeks are work we did not price. We should raise it as a change request and use the slip to propose a paid extension to Dalia, rather than absorb the cost.

## 5. Eastgate: wave one or wave two

- **Ingrid wants Eastgate in wave one.** It is the biggest depot, about a third more volume than Southport, and it suffers most on the legacy tracker (0:10:25).
- **Tomasz says IT cannot support it yet.** There is no site survey, and the dock-area coverage is the problem. Tomasz: "Honestly, the Wi-Fi in the Eastgate dock area is a graveyard." (0:11:42). The scan gates drop out at four doors at least, and cabling has a vendor lead time of about six weeks, so February at best (0:11:42).
- **Neither moved.** Ingrid will not agree to wave two today and Tomasz will not agree to wave one (0:13:24, 0:13:40). Status: Open.
- **How it gets settled.** Tomasz finishes the Eastgate site survey by Friday 20 November. If Ingrid and Tomasz are still split, it goes to Dalia (0:13:52).

## 6. Terms, doors and training

- **Dock-door profile (unconfirmed).** The per-door record of scanners, label printer, network segment and manifest feed. Mei-Ling uses it as shorthand and the expansion is ours (0:14:40). The shift leads say "door card" (0:16:12).
- **Doors nine to twelve at Southport** are the ones nobody has written down (0:15:12). Ingrid's shift leads can walk them in an afternoon (0:15:30).
- **Cutover weekday.** Tomasz: "Manifest sync has never once finished before the Monday morning shift." (0:16:48). The weekday is chosen at the end of the shadow run (0:17:30).
- **Interface spec.** The interface spec still carries the old programme name in half its headers (0:03:18). Rohan knows.
- **Training.** Floor teams need two weeks' notice and a one-page card before anything changes at their door (0:18:00). We draft a training plan for next time (0:19:00).

## 7. Where sources disagree

| # | One source | The other | Status |
|---|---|---|---|
| 1 | Kickoff recap, 29 Oct: wave-one cutover on Monday 30 November | Ingrid, 5 Nov: that date is inside the peak freeze, 23 November to 8 January (0:04:30) | Newer source wins. Cutover moves to after the freeze; update the plan |
| 2 | Kickoff recap, 29 Oct: wave one is Southport and Eastgate | Tomasz, 5 Nov: IT cannot support Eastgate before the site survey (0:11:22) | Open. Settled after the survey on 20 November, or by Dalia |
| 3 | Kickoff recap, 29 Oct: no parallel running | Decision, 5 Nov: a two-week shadow run at Southport (0:09:20) | Newer source wins |
| 4 | Transcript: "door card" (0:16:12) | Best guess: dock-door profile | Check with Ingrid which word Harbour Freight uses |

## 8. Changes to our own records

Made on 6 Nov 2026.

- **Glossary.** New: **Peak freeze**, **Shadow run**, **Dock-door profile (unconfirmed)**. One new flagged ambiguity: "door card".
- **Not changed:** the kickoff recap in `Artefacts/` still says 30 November. Proposed for Callum's approval: a correction note.

## 9. Open questions

| # | Question | Why it matters |
|---|---|---|
| 1 | Does Eastgate join wave one? | It decides wave-one scope and the order of Tomasz's survey work |
| 2 | Will Dalia sign off the revised dates? | Everything else assumes them |
| 3 | Which weekday for cutover? | Manifest sync has to finish before the first shift |
| 4 | Is "dock-door profile" or "door card" the word Harbour Freight wants? | It is an unconfirmed term in the glossary |

## 10. Next steps

- **Tomasz:** the Eastgate site survey by Friday 20 November, then the change ticket for Southport once the freeze lifts (0:22:00).
- **Ingrid:** shift leads walk doors nine to twelve at Southport by 27 November; talk to Dalia once she has the written dates (0:22:24).
- **Mei-Ling:** the plan with the new dates, the profile template by Friday 13 November, and confirm Rohan as the shadow-run contact (0:22:48).
- **Callum:** the revised plan to Dalia by Tuesday 10 November, the glossary update, and the freeze dates on the plan's front page (0:20:44, 0:21:38).

---

*Written on 6 Nov 2026 from the machine transcript. 1% of the words are unattributed; Callum and Mei-Ling are the pair most likely to be swapped. Terms follow [Glossary.md](<../../../Glossary.md>). Internal only.*
