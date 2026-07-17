#!/usr/bin/env python3
"""
Declawed mechanical scan.

Loads the detection catalog straight out of references/slop-patterns.md (the
single source of truth — sections 1-4, the fenced regex blocks) and runs it
against a target text, then adds the structural checks that aren't plain regex
(cadence, em-dash density, formatting tells — sections 5-6 of the catalog).

Python rather than bash+grep on purpose: the catalog uses \b and the emoji
check needs Unicode ranges, which BSD grep (stock macOS) does not support. The
`re` module behaves the same everywhere Python does, so the scan can't silently
under-match on whichever machine the skill lands on.

Usage:
    python3 scan.py draft.txt          # scan a file
    pbpaste | python3 scan.py          # scan piped text (stdin)
    python3 scan.py draft.txt --patterns /path/to/slop-patterns.md

Output is a finding table. A match is a FINDING, not an auto-delete — every
finding goes through the Phase 2 triage in SKILL.md.
"""

import argparse
import re
import sys
from pathlib import Path

# Lines inside a fenced block that are shell scaffolding, not catalog patterns.
# This is how the top usage-example block and the section-6 measurement block
# get skipped while the real regex blocks (sections 1-4) come through.
_NON_PATTERN = re.compile(
    r"""^(grep|tr|sed|awk|LC_ALL|python|perl)\b   # a shell command
      | <<                                          # heredoc marker
      | /dev/stdin | draft\.txt                     # example filenames
      | <paste                                      # placeholder text
      | ^PATTERNS$                                  # heredoc terminator
    """,
    re.VERBOSE,
)

# Emoji / symbol ranges for the "emoji in headers or bullets" tell.
_EMOJI = re.compile(r"[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F0FF]")


def load_catalog(md_path):
    """Parse (section, compiled_regex) pairs out of the catalog's fenced blocks."""
    section = "(unsectioned)"
    in_fence = False
    catalog = []
    skipped = []
    for raw in md_path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip("\n")
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            m = re.match(r"^#{2,}\s+(.*)", line)
            if m:
                section = m.group(1).strip()
            continue
        pat = line.strip()
        if not pat or pat.startswith("#") or _NON_PATTERN.search(pat):
            continue
        try:
            catalog.append((section, pat, re.compile(pat, re.IGNORECASE)))
        except re.error as e:
            skipped.append((pat, str(e)))
    return catalog, skipped


def sentences(text):
    parts = re.split(r"(?<=[.!?])\s+", text.replace("\n", " "))
    return [s.strip() for s in parts if s.strip()]


def scan_catalog(catalog, lines):
    """Return {section: {"hits": n, "worst": (lineno, text)}} for matched sections."""
    results = {}
    for section, _pat, rx in catalog:
        for i, line in enumerate(lines, 1):
            if rx.search(line):
                bucket = results.setdefault(section, {"hits": 0, "worst": None})
                bucket["hits"] += 1
                if bucket["worst"] is None:
                    snippet = line.strip()
                    if len(snippet) > 70:
                        snippet = snippet[:67] + "..."
                    bucket["worst"] = (i, snippet)
    return results


def structural_checks(text, lines):
    flags = []

    sents = sentences(text)
    lengths = [len(s.split()) for s in sents]
    runs = 0
    i = 0
    while i <= len(lengths) - 3:
        window = lengths[i:i + 3]
        if max(window) - min(window) <= 4:
            runs += 1
            # skip past this run so overlapping windows count once
            j = i + 3
            while j < len(lengths) and max(lengths[i:j + 1]) - min(lengths[i:j + 1]) <= 4:
                j += 1
            i = j
        else:
            i += 1
    if lengths:
        flags.append(
            ("cadence",
             f"{len(sents)} sentences, lengths {min(lengths)}-{max(lengths)} words; "
             f"{runs} run(s) of 3+ within ±4 words"
             + ("  <-- uniform" if runs else "")))

    words = len(text.split())
    em = text.count("—")
    budget = max(1, words // 150)
    two_in_one = sum(1 for s in sents if s.count("—") >= 2)
    if em:
        note = f"{em} em dash(es) in {words} words (budget ~{budget})"
        if em > budget:
            note += "  <-- OVER"
        if two_in_one:
            note += f"; {two_in_one} sentence(s) with 2+"
        flags.append(("em dashes", note))

    bold = len(re.findall(r"\*\*[^*]{2,40}\*\*", text))
    paras = max(1, len([b for b in re.split(r"\n\s*\n", text) if b.strip()]))
    if bold:
        note = f"{bold} bold span(s) across {paras} paragraph(s)"
        if bold > paras / 3:
            note += "  <-- scattered through prose"
        flags.append(("bold in prose", note))

    emoji_lines = [i for i, ln in enumerate(lines, 1)
                   if re.match(r"^\s*[-*#]+\s", ln) and _EMOJI.search(ln)]
    if emoji_lines:
        flags.append(("emoji headers/bullets",
                      f"{len(emoji_lines)} line(s): {emoji_lines[:5]}"))

    termdef = sum(1 for ln in lines if re.match(r"^\s*[-*]\s+\*\*[^*]+\*\*\s*:?", ln))
    if termdef:
        flags.append(("\"term: definition\" bullets",
                      f"{termdef} (legitimate in docs/README; a tell elsewhere)"))

    return flags


def render(target, catalog, skipped, cat_results, struct_flags):
    bar = "=" * 64
    out = [bar, f" DECLAWED SCAN  —  {target}",
           f" catalog: {len(catalog)} patterns from references/slop-patterns.md", bar, ""]

    out.append("CATALOG FINDINGS")
    if cat_results:
        width = max(len(s) for s in cat_results)
        for section in sorted(cat_results, key=lambda s: -cat_results[s]["hits"]):
            r = cat_results[section]
            lineno, snippet = r["worst"]
            out.append(f"  {section:<{width}}  {r['hits']:>3}  L{lineno}: {snippet}")
    else:
        out.append("  (none)")
    out.append("")

    out.append("STRUCTURAL CHECKS  (sections 5-6 — measured, not regex)")
    if struct_flags:
        width = max(len(name) for name, _ in struct_flags)
        for name, note in struct_flags:
            out.append(f"  {name:<{width}} : {note}")
    else:
        out.append("  (none)")
    out.append("")

    total = sum(r["hits"] for r in cat_results.values())
    out.append("-" * 64)
    out.append(f" {total} catalog hit(s) across {len(cat_results)} categor(ies), "
               f"{len(struct_flags)} structural observation(s) (see <-- markers)")
    out.append(" Each hit is a FINDING, not an auto-delete — triage per SKILL.md Phase 2.")
    if skipped:
        out.append(f" NOTE: {len(skipped)} catalog pattern(s) failed to compile and were skipped.")
    out.append(bar)
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="Declawed mechanical scan.")
    ap.add_argument("target", nargs="?", help="text file to scan (default: stdin)")
    default_patterns = Path(__file__).resolve().parent.parent / "references" / "slop-patterns.md"
    ap.add_argument("--patterns", type=Path, default=default_patterns,
                    help="path to slop-patterns.md")
    args = ap.parse_args()

    if not args.patterns.exists():
        sys.exit(f"catalog not found: {args.patterns}")
    catalog, skipped = load_catalog(args.patterns)
    if not catalog:
        sys.exit(f"no patterns parsed from {args.patterns} — has the block layout changed?")

    if args.target:
        text = Path(args.target).read_text(encoding="utf-8")
        name = args.target
    else:
        text = sys.stdin.read()
        name = "(stdin)"
    lines = text.splitlines()

    cat_results = scan_catalog(catalog, lines)
    struct_flags = structural_checks(text, lines)
    print(render(name, catalog, skipped, cat_results, struct_flags))
    for pat, err in skipped:
        print(f"  skipped pattern: {pat!r} ({err})", file=sys.stderr)


if __name__ == "__main__":
    main()
