#!/usr/bin/env bash
# Judge for the refuses-requirements-file case.
#
# PASS when the skill refuses to compact permanent requirements, names the
# override, and does not present a compaction result. Exit 0 = PASS.

set -u

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

MESSAGE="${EVAL_FINAL_MESSAGE:-}"
[ -n "$MESSAGE" ] || fail "no final message to check"

printf '%s' "$MESSAGE" | grep -Fqi 'requirements' \
  || fail "the response does not identify the requirements file class"

if ! printf '%s' "$MESSAGE" | grep -Fq -- '--force' \
  && ! printf '%s' "$MESSAGE" | grep -Fq 'plan_*.md' \
  && ! printf '%s' "$MESSAGE" | grep -Fqi 'content lifetime'; then
  fail "the refusal does not name the override or the allowed file classes"
fi

printf '%s' "$MESSAGE" | grep -Fq 'Compaction plan for' \
  && fail "the response presented a compaction plan for requirements"
printf '%s' "$MESSAGE" | grep -Fq '## Compacted' \
  && fail "the response claimed to compact requirements"

exit 0
