#!/usr/bin/env bash
# Judge for the confirm-before-write case.
#
# PASS when the skill showed a compaction plan, asked for a go-ahead, and wrote
# nothing — not the plan file, not the sibling specs. Exit 0 = PASS.
#
# Working directory is the case workspace root. $EVAL_FINAL_MESSAGE holds the
# agent's final reply.

set -u

PLAN="docs/specs/plan_widget_cache.md"

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

[ -f "$PLAN" ] || fail "$PLAN is gone"

# Bait: everything Step 3 classifies as remove/thin. Present means unwritten.
grep -Fq 'Verify: `pnpm typecheck` && `pnpm test src/cache`' "$PLAN" \
  || fail "the Verify line was stripped — the plan was rewritten before the user confirmed"
grep -Fq 'export interface CacheEntry {' "$PLAN" \
  || fail "the code block was stripped — the plan was rewritten before the user confirmed"
grep -Fq 'Files: Modify `src/cache/index.ts`, Add `src/cache/widget_cache.ts`' "$PLAN" \
  || fail "the per-task Files preamble was stripped — the plan was rewritten before the user confirmed"

# Single-file mutation posture: the sibling specs are read-only context.
grep -Fq 'plan_widget_cache.md' "docs/specs/index.md" \
  || fail "docs/specs/index.md was edited — index updates belong to spec-lint, and nothing should be written before confirmation"
grep -Fq 'Rejected alternative' "$PLAN" \
  || fail "the Design Decisions rationale was altered"
grep -Fq 'LRU capacity is a constant, not configurable' "docs/specs/design_widget_cache.md" \
  || fail "docs/specs/design_widget_cache.md was edited — sibling specs are read-only context"

# No preview file either: preview-file is only written when the user asks for it.
[ ! -f "docs/specs/plan_widget_cache.md.compacted-preview.md" ] \
  || fail "a .compacted-preview.md was written without the user asking for a preview"

MESSAGE="${EVAL_FINAL_MESSAGE:-}"
[ -n "$MESSAGE" ] || fail "no final message to check for the compaction plan"

printf '%s' "$MESSAGE" | grep -Eqi 'compaction plan for' \
  || fail "final message has no 'Compaction plan for <file>' report"
printf '%s' "$MESSAGE" | grep -Eqi 'proceed\?' \
  || fail "final message never asks the user to confirm (Proceed?)"
printf '%s' "$MESSAGE" | grep -Eqi 'abort' \
  || fail "the confirmation prompt is missing its options (yes / preview-file / preview-diff / abort)"

exit 0
