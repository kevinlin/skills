# Declawed

<img src="assets/declawed.png" alt="Declawed logo" width="160">

Strip the fingerprints of AI writing from any text and make it read like a specific person wrote it for a specific audience. The goal isn't to beat a detector — it's prose that commits to a claim instead of hedging around one.

## What it catches

The scan hunts patterns that leak from how LLMs generate text:

- **Negative parallelism** — "not X but Y" and its disguises ("less about X than Y", "the real X is Y")
- **Puffery** — delve, tapestry, seamless, pivotal, game-changing
- **Rule-of-three** — triplets that pad thin analysis
- **False ranges** — "from X to Y" with no real middle
- **Hedged both-sidesing** — every claim softened, every opinion handed a counterpoint
- **Uniform cadence** — sentence after sentence of the same length and shape
- **Formatting tells** — bold scattered through prose, emoji headers, "Term: definition" bullet essays

## Why it's a loop

Two facts drive the design. You can't reliably see your own slop: the priors that produce a pattern make it invisible on re-read, so detection is mechanical — regex against a fixed catalog, never "does this look AI to me?". And rewriting reintroduces slop: ask a model to kill "it's not just X, it's Y" and it hands back "this is less about X than Y", the same move in a wig. So every rewrite gets re-scanned, and the loop runs until a pass comes back clean.

The scan is mechanical — `scripts/scan.py` loads the catalog and reports every hit — so catching slop never depends on the model spotting its own.

```
Scan → Diagnose → Rewrite by meaning → Re-scan → (repeat) → Register check
```

## Usage

Invoke it directly:

```
/declawed
```

Or just ask — it triggers on "declawed", "deslop", "remove the AI tells", "humanize this", "make this not sound like AI". Point it at text in the conversation or at a file. It fixes the target genre first (a reddit comment and an academic abstract fail in opposite ways), then runs the loop.

## Output

The rewritten text, plus a short change log: which categories were fixed, how many hits, and how many verify passes it took.

## Structure

```
declawed/
├── SKILL.md                 # The workflow: 5 phases, scan to register check
├── README.md
├── scripts/
│   └── scan.py              # Mechanical scan — loads the catalog, emits a finding table
├── assets/
│   └── declawed.png
└── references/
    ├── slop-patterns.md     # Detection catalog (single source of truth for scan.py)
    └── tones.md             # Per-genre register: what "good" sounds like, what's fatal
```

## Attribution

Forked from [JuliusBrussee/skills](https://github.com/JuliusBrussee/skills) — `skills/fuck-slop`.
