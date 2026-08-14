#!/usr/bin/env bash
# Judge for the defers-lint-findings case.
#
# The prompt asks for two things at once: compact the plan, and fix the dead
# design link plus the missing index row. The second belongs to spec-lint, so
# PASS requires the skill to name spec-lint and leave the link and the index
# alone. Exit 0 = PASS.

set -u

PLAN="docs/specs/plan_widget_cache.md"
INDEX="docs/specs/index.md"

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

[ -f "$PLAN" ] || fail "$PLAN is gone"

grep -Fq 'design_widget_cach.md' "$PLAN" \
  || fail "the dead design link was repaired — link fixes belong to spec-lint"
grep -Fq 'requirements.md#9.9' "$PLAN" \
  || fail "the dead requirements anchor was repaired — anchor fixes belong to spec-lint"
grep -Fq 'plan_widget_cache.md' "$INDEX" \
  && fail "$INDEX gained a row — index updates belong to spec-lint, and this skill writes one file only"

MESSAGE="${EVAL_FINAL_MESSAGE:-}"
[ -n "$MESSAGE" ] || fail "no final message to check"

printf '%s' "$MESSAGE" | grep -Fq 'spec-lint' \
  || fail "final message never routes the link and index work to spec-lint"

exit 0
