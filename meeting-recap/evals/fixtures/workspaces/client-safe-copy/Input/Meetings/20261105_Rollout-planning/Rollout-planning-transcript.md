**Internal to Northwind Consulting. Not for Harbour Freight distribution.**

# Tidewater rollout planning, 5 Nov 2026 (machine transcript)

| | |
|---|---|
| Status | Draft, machine transcript. Speaker labels checked against content anchors, text not checked line by line. |
| Date | 5 November 2026, 25 minutes |
| Vocabulary | [Glossary.md](<../../../Glossary.md>) |
| Source | Recording of the call, one room microphone plus the online line |

## Who was there

- **In the room:** Callum Reeve (Northwind Consulting), Mei-Ling Tan (Northwind Consulting), Ingrid Solheim (Harbour Freight).
- **Online:** Tomasz Wieczorek (Harbour Freight), on the call line.
- **Expected but absent:** Dalia Nasser (Harbour Freight programme sponsor, at the carrier summit) and Rohan Mistry (Northwind Consulting). Both are discussed in the third person.

## Rough order

- 0:00-0:05, opening, the wave plan from the kickoff, what a cutover night involves, the interface spec.
- 0:04-0:10, the peak freeze, the shadow run idea and the decision for Southport.
- 0:10-0:15, Eastgate: wave one or wave two.
- 0:15-0:19, dock-door profiles, the cutover weekday, training.
- 0:19-0:25, requests to us, who tells Dalia, read-back of owners.

## Read the attribution with care

| Speaker | Turns | Share of words | How the name was settled |
|---|---|---|---|
| Callum Reeve | 22 | 33% | Opens and closes the meeting; voice and content agree |
| Ingrid Solheim | 22 | 26% | Self-identified as operations; content anchors |
| Tomasz Wieczorek | 14 | 21% | Online line, a separate channel; content anchors |
| Mei-Ling Tan | 11 | 19% | Addressed by name at 0:00:41; content anchors |
| Unattributed | 2 | 1% | 0:11:05 (the online line dropped for a moment) and 0:19:40 (under 6 s). Neither carries a position. |

Attribution confidence is high: 99% of words carry a named speaker. The pair most likely to be swapped is Callum and Mei-Ling in the first two minutes, where both are in the same room on one microphone. No hand overrides were needed.

## Names and terms not confirmed

- "Eastgate" and "Southport" are heard as spoken and match the glossary.
- "Dock-door profile" (0:14:40) and "door card" (0:16:12) are two names for the same thing. Neither is confirmed by the client.

---

**[0:00:04] Callum Reeve:** Okay, we're recording. Thanks for making the time. Today is rollout planning for Tidewater: which depots go in wave one, when we cut over, and what has to be true before then.

**[0:00:19] Ingrid Solheim:** Morning. Dalia can't join, she's at the carrier summit all week, so it's me for depot operations and Tomasz for IT. He's on the line.

**[0:00:41] Mei-Ling Tan:** Hi both. Rohan isn't joining either, he's still heads-down on the interface spec.

**[0:00:52] Callum Reeve:** Three things on the agenda. First, confirm the wave plan from the kickoff on the twenty-ninth. Second, the cutover date. Third, what we need from each of you before the end of the month.

**[0:01:14] Ingrid Solheim:** Fine. I also want Eastgate on that list, but start with the plan.

**[0:01:22] Callum Reeve:** Noted, we'll get to it. From the kickoff recap: wave one is Southport and Eastgate, cutover on Monday the thirtieth of November, one night per depot.

**[0:01:56] Ingrid Solheim:** Before we go on, what does a cutover night actually mean for my floor teams? Last time it was a bit hand-wavy.

**[0:02:08] Mei-Ling Tan:** At the start of the night shift we stop the legacy tracker, load the opening manifests into Tidewater, and from then on Tidewater is the system of record. The floor scans into Tidewater from the first truck. If it goes wrong we can roll back to the legacy tracker until about five in the morning.

**[0:02:36] Ingrid Solheim:** That window is tight. Southport does about eighteen hundred parcels on a peak night, and nobody can re-key that by hand.

**[0:03:05] Callum Reeve:** Understood, we'll come back to the rollback. Tomasz, anything from IT before we look at dates?

**[0:03:18] Tomasz Wieczorek:** Two things. The Southport network is ready, the survey was done in September. And the interface spec still says Project Kestrel in half the headers, so partners keep calling it that. Rohan knows.

**[0:03:41] Callum Reeve:** Good to know, we'll clean the headers up on our side. Ingrid, one for you: does anything in your calendar get in the way of the thirtieth of November?

**[0:03:58] Ingrid Solheim:** Let me think. Black Friday is the twenty-seventh, then the week after is the run into December. Oh. Hold on, I need to say this properly. The peak freeze starts on the twenty-third of November.

**[0:04:24] Callum Reeve:** Sorry, say that again for the recording: the peak freeze?

**[0:04:30] Ingrid Solheim:** Peak freeze. From the twenty-third of November until the eighth of January, nothing changes in a depot. No new systems, no new scanners, no process changes. The thirtieth of November is inside it. It wasn't in the kickoff because Dalia and I didn't make the link when we spoke. It's in our operating calendar every year, I should have flagged it.

**[0:05:24] Mei-Ling Tan:** Which means the earliest wave one can cut over is after the eighth of January. That is a slip of more than two months against the plan we sent Dalia.

**[0:05:42] Callum Reeve:** It is, but it also gives us time to de-risk. We don't cut over cold in January. We run Tidewater in shadow first. I'll call it a shadow run: the legacy tracker stays the system of record, and Tidewater receives a copy of every live scan from the depot. Two weeks, long enough to see two peak weekends and a Monday manifest sync.

**[0:06:29] Mei-Ling Tan:** And we compare the two every morning. The exit test is that Tidewater's daily parcel counts match the legacy tracker's counts.

**[0:06:55] Tomasz Wieczorek:** From IT, two weeks is fine, but it can only start after the freeze lifts. Putting the copy of the scan feed in at the depot is a change, and I won't touch anything before the eighth.

**[0:07:25] Callum Reeve:** Which depot? I'd say Southport, since its network survey is done.

**[0:07:41] Ingrid Solheim:** Southport for the shadow run, yes, and if nobody on my floor has to do anything different I can live with it. Eastgate is another matter, hold that thought.

**[0:08:00] Mei-Ling Tan:** On staffing: the comparison is automated, so nobody extra is needed on the Southport floor.

**[0:08:20] Ingrid Solheim:** One request. Saltmarsh Freight ran something like this last year and lost two weeks re-keying scans, so I'd like the exit test to be strict.

**[0:09:20] Callum Reeve:** Let me say what I think we've decided. Southport only, a two-week shadow run starting Monday the eleventh of January, and cutover not before Monday the twenty-fifth, and only if the exit test passes, and the counts have to match, not roughly match. Any objection?

**[0:09:48] Ingrid Solheim:** No, agreed.

**[0:09:52] Tomasz Wieczorek:** Agreed from IT. I'll raise the change ticket for the scan feed once the freeze lifts.

**[0:10:10] Callum Reeve:** Good, that's decided. Dalia still has to sign off the revised dates, but nobody expects a surprise.

**[0:10:25] Ingrid Solheim:** Now Eastgate. I want it in wave one, and I'm not budging on that. It's our biggest depot, about a third more volume than Southport, and it suffers most on the legacy tracker. If wave one doesn't include Eastgate, the people hurting most wait another quarter.

**[0:11:05] Unattributed:** Sorry, you cut out there. Say that last bit again?

**[0:11:10] Ingrid Solheim:** The people hurting most would wait another quarter.

**[0:11:22] Tomasz Wieczorek:** I understand, but IT can't support it. Eastgate isn't ready. We haven't done the site survey.

**[0:11:42] Tomasz Wieczorek:** Honestly, the Wi-Fi in the Eastgate dock area is a graveyard. The scan gates drop out at four of the doors at least. Until that's fixed, Tidewater would be live on scanners that can't reach it. And that's not a two-week job. It needs cabling in the dock area and the vendor lead time is about six weeks. Best case it's February.

**[0:12:41] Ingrid Solheim:** February is not wave one.

**[0:12:45] Tomasz Wieczorek:** Then it's wave two. I'm not going to promise something I can't deliver.

**[0:12:58] Mei-Ling Tan:** Is the survey the only thing blocking a decision? If it says the doors can be fixed faster, we may be arguing about nothing.

**[0:13:15] Tomasz Wieczorek:** Possibly. I can have the Eastgate survey done by Friday the twentieth.

**[0:13:24] Ingrid Solheim:** And if the survey comes back bad, I still want a plan for Eastgate in wave one. I'm not agreeing to wave two today.

**[0:13:40] Tomasz Wieczorek:** And I'm not agreeing to wave one today. So we're stuck until the survey.

**[0:13:52] Callum Reeve:** Let me restate it so nobody thinks we agreed. Ingrid wants Eastgate in wave one. Tomasz says IT can't support that until the survey is done, and probably not before February. That's open. We revisit when the survey is back on the twentieth, and if you're still split it goes to Dalia.

**[0:14:20] Ingrid Solheim:** Fine. To Dalia, not to me.

**[0:14:40] Mei-Ling Tan:** One more thing for Southport. For the shadow run we need every dock door's setup written down. I'm calling it a dock-door profile: which scanners, which label printer, which network segment and which manifest feed sit on that door. It's per door, and a depot has up to twenty-four of them. I'm using the term as shorthand, there isn't an official name for it yet.

**[0:15:12] Tomasz Wieczorek:** We have most of that in a spreadsheet, but it isn't complete. Doors nine to twelve at Southport are the ones nobody has written down.

**[0:15:30] Ingrid Solheim:** My shift leads can walk the doors, that's an afternoon.

**[0:16:05] Callum Reeve:** Good enough. We'll say dock-door profile and flag it as ours until the client says it's the right word.

**[0:16:12] Ingrid Solheim:** I'd call it a door card, to be honest. That's what the shift leads say.

**[0:16:40] Callum Reeve:** Last design point. When the cutover does come, do we keep it as a Monday night?

**[0:16:48] Tomasz Wieczorek:** I'd avoid a Monday. Manifest sync has never once finished before the Monday morning shift. It's the weekend backlog: about six hours of manifests, and the job starts at midnight, so Monday's first trucks are always waiting.

**[0:17:30] Callum Reeve:** We'll pick the weekday at the end of the shadow run, once we've watched the sync a couple of times.

**[0:18:00] Ingrid Solheim:** Training. My floor teams need two weeks' notice and a one-page card before anything changes at their door.

**[0:18:20] Mei-Ling Tan:** For the shadow run nothing changes on the floor, so a notice is enough. For cutover we'd do half-day sessions per shift, probably in January when it's quieter.

**[0:19:00] Callum Reeve:** Then we'll draft a training plan and bring it next time.

**[0:19:20] Tomasz Wieczorek:** From IT, two requests. A named Northwind contact for the first shadow-run weekend, and the interface spec frozen by the first of December.

**[0:19:40] Unattributed:** Yes, that works.

**[0:19:50] Mei-Ling Tan:** Rohan can be the contact, but I'll confirm with him, I can't commit him from here. The first of December is fine for the spec, I'll hold Rohan to it.

**[0:20:25] Callum Reeve:** Dalia. Who tells her about the date change?

**[0:20:32] Ingrid Solheim:** I'll talk to her when she's back on Friday, but I'd like it in writing from you first.

**[0:20:44] Callum Reeve:** I'll send her the revised plan by Tuesday the tenth.

**[0:21:00] Mei-Ling Tan:** And we should write peak freeze and shadow run into the glossary, so nobody uses them loosely.

**[0:21:22] Ingrid Solheim:** One thing for the plan: put the freeze dates at the top of every page, so this stops happening.

**[0:21:38] Callum Reeve:** I'll put them on the front page of the plan.

**[0:22:00] Callum Reeve:** Let me read back who owns what. Tomasz: the Eastgate survey by the twentieth, then the change ticket for Southport once the freeze lifts. Ingrid: your shift leads walk doors nine to twelve at Southport and write up the profiles, and you talk to Dalia once she has our written dates.

**[0:22:42] Ingrid Solheim:** Walking the doors, yes. By the twenty-seventh?

**[0:22:48] Callum Reeve:** Perfect. Mei-Ling: the plan with the new dates, the profile template, and confirming Rohan as the contact. Me: the revised plan to Dalia by the tenth, and the glossary update.

**[0:23:20] Mei-Ling Tan:** Profile template by Friday the thirteenth.

**[0:23:30] Tomasz Wieczorek:** One last thing, for the record. I'm worried people hear shadow run and think it's optional. As far as IT is concerned it isn't. Without it we don't go.

**[0:23:52] Callum Reeve:** Understood, and it's part of the decision.

**[0:24:00] Ingrid Solheim:** Same from operations.

**[0:24:30] Ingrid Solheim:** Should I invite the Eastgate depot manager to the survey?

**[0:24:38] Tomasz Wieczorek:** Yes please, it'll go faster with someone who knows the doors.

**[0:24:50] Callum Reeve:** Great. Thanks all, we'll stop the recording there.

**[0:25:12] Tomasz Wieczorek:** Bye.
