#!/usr/bin/env bash
# Judge for the applies-after-yes case.
#
# PASS when the confirmed compaction rewrote the plan the way Step 3 and Step 5
# prescribe: the how is gone, the why and the heading skeleton survive, and a
# compaction changelog entry sits above the old entries. Exit 0 = PASS.

set -u

PLAN="docs/specs/plan_widget_cache.md"

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

[ -f "$PLAN" ] || fail "$PLAN is gone — the compaction was supposed to rewrite it in place"

LINES=$(wc -l < "$PLAN" | tr -d ' ')
[ "$LINES" -lt 85 ] || fail "plan is still $LINES lines (was 111) — nothing meaningful was compacted"

# --- The how, which the codebase now owns ---
grep -Fq 'Verify: `pnpm typecheck`' "$PLAN" \
  && fail "Verify: command lines survived — project commands belong in CLAUDE.md"
grep -Fq 'Files: Modify `src/cache/index.ts`' "$PLAN" \
  && fail "the per-task Files: preamble survived — paths belong in the Critical Files table"
grep -Fq 'if (key.startsWith(' "$PLAN" \
  && fail "an implementation code block survived — the versioned code is the source of truth"
grep -Fq 'Re-export `WidgetCache` from' "$PLAN" \
  && fail "the file-by-file Steps: body survived — the diffs are in git"

# --- The why, which only the plan holds ---
grep -Fq '## Design Decisions' "$PLAN" \
  || fail "the Design Decisions heading was dropped"
grep -Fq 'Rejected alternative' "$PLAN" \
  || fail "the rejected-alternative rationale was deleted — the most expensive content to recreate"
grep -Fq 'polling' "$PLAN" \
  || fail "the invalidation-vs-polling rationale was deleted"
grep -Fq '## Context' "$PLAN" \
  || fail "the Context section was dropped"

# --- Heading skeleton preserved ---
grep -Fq '## Implementation Plan' "$PLAN" \
  || fail "the Implementation Plan heading vanished — it should survive as a thin worklist"
grep -Fq 'Task 1' "$PLAN" \
  || fail "the Task 1 heading vanished — task headings are kept, only their bodies are thinned"
grep -Fq 'Task 2' "$PLAN" \
  || fail "the Task 2 heading vanished"
grep -Fq 'src/cache/widget_cache.ts' "$PLAN" \
  || fail "the Critical Files pointer to src/cache/widget_cache.ts was lost"
grep -Fq 'plan_widget_metrics.md' "$PLAN" \
  || fail "the outstanding follow-up pointing at plan_widget_metrics.md was lost"
head -n 1 "$PLAN" | grep -Fq '# Plan: Widget cache' \
  || fail "the H1 was rewritten — Step 5 keeps frontmatter and the H1 untouched"

# --- Changelog ---
grep -Fq '2026-05-02' "$PLAN" \
  || fail "the pre-existing changelog entry was dropped — old entries are kept"
grep -Eqi 'compact' "$PLAN" \
  || fail "no compaction changelog entry was added"

# --- Single-file mutation ---
grep -Fq 'plan_widget_cache.md' "docs/specs/index.md" \
  || fail "docs/specs/index.md was rewritten — sibling specs are read-only context"
grep -Fq 'LRU capacity is a constant, not configurable' "docs/specs/design_widget_cache.md" \
  || fail "docs/specs/design_widget_cache.md was edited — sibling specs are read-only context"

exit 0
