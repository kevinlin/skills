# Glossary

The live vocabulary of the Tidewater rollout at Harbour Freight. Use these terms in every recap and plan; the aliases to avoid are words people use loosely or that mean something else here.

Sources: the [Tidewater scope kickoff (29 Oct 2026)](<Artefacts/Meetings/20261029_Tidewater-scope-kickoff/Tidewater-scope-kickoff-recap.md>), and the [Rollout planning (5 Nov 2026)](<Output/Meetings/20261105_Rollout-planning/Rollout-planning-recap.md>).

Terms marked **(unconfirmed)** are our reading of the source material and still need Harbour Freight confirmation.

---

## Rollout

| Term | Definition | Aliases to avoid |
|---|---|---|
| **Tidewater** | The shipment-tracking platform Harbour Freight is rolling out to its depots, and the programme that delivers it. | the new tracker |
| **Wave** | A group of depots that cut over together. Wave one is the first group. | phase, tranche |
| **Depot** | A Harbour Freight parcel hub with its own dock doors and scan gates. | branch, yard |
| **Cutover** | The night a depot stops using the legacy tracker and Tidewater becomes its system of record. | switchover, go-live night |
| **Shadow run** | A period before cutover in which Tidewater receives a copy of every live scan while the legacy tracker stays the system of record. Callum, 5 Nov: "I'll call it a shadow run." | parallel run, dry run |
| **Peak freeze** | The yearly window, 23 November to 8 January, in which nothing changes in a depot: no new systems, scanners or process changes. Ingrid, 5 Nov. | change freeze, blackout |
| **Legacy tracker** | The existing in-house parcel tracking system that Tidewater replaces. | the old system |
| **System of record** | The system whose data wins when two systems disagree about a parcel. | master |

## Depot systems

| Term | Definition | Aliases to avoid |
|---|---|---|
| **Scan gate** | The handheld scanner checkpoint at a dock door where parcels are logged in and out. | checkpoint, scan point |
| **Manifest sync** | The nightly job that sends each depot's loading manifests to the central system. | manifest upload |
| **Site survey** | An IT walk-through of a depot's network coverage and dock layout. | walkthrough |
| **Dock-door profile** | The per-door record of scanners, label printer, network segment and manifest feed. The expansion is ours. **(unconfirmed)** | door card (what the shift leads say) |

---

## Relationships

- A **Wave** contains one or more **Depots**. Every **Depot** cuts over once, on one **Cutover** night.
- Before **Cutover**, the **Legacy tracker** is the **System of record**. After it, **Tidewater** is.
- A **Shadow run** comes before **Cutover** and never falls inside a **Peak freeze**.

## Flagged ambiguities

- **"Site" is overloaded.** It can mean a depot or a survey location. Say **Depot** for the first and **Site survey** for the activity.
- **"Door card" or "dock-door profile"?** Mei-Ling, 5 Nov: "there isn't an official name for it yet". Ingrid, 5 Nov: "I'd call it a door card." Use **Dock-door profile** until Harbour Freight picks a word. **(unresolved)**
