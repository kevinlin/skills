#!/usr/bin/env bash
# Case: question-without-execution
set -uo pipefail

# Helpers are inlined, not sourced: skill-up copies only the file named by
# `judge.script_path` into its temp dir, so a sibling lib.sh is not there at
# run time and every helper call would silently be a command-not-found.

# require <haystack> <label> <extended-regex>   (case-insensitive)
require() {
  local hay="$1" label="$2" pattern="$3"
  printf '%s' "$hay" | grep -qiE "$pattern" && return 0
  echo "FAIL: $label — no match for /$pattern/" >&2
  FAILED=1
}

FAILED=0
MSG="${EVAL_FINAL_MESSAGE:-}"
TASKS="docs/specs/rate-limiting/tasks.md"

# The question is answered: the next task is named, with a sense of its size.
require "$MSG" "next task named" 'consume|task 2'
require "$MSG" "size or effort described" \
  'small|simple|straightforward|quick|short|modest|contained|hour|line|moderate|effort|complex'

# Nothing was executed.
if ! grep -q "NotImplementedError" src/limiter.py 2>/dev/null; then
  echo "FAIL: TokenBucket.consume was implemented in answer to a question" >&2
  FAILED=1
fi
CHECKED=$(grep -cE '^[[:space:]]*- \[[xX]\]' "$TASKS" 2>/dev/null)
if [ "$CHECKED" != "1" ]; then
  echo "FAIL: checked-task count is $CHECKED, expected the seeded 1" >&2
  FAILED=1
fi
for f in src/middleware.py src/metrics.py; do
  if [ -e "$f" ]; then
    echo "FAIL: started task work — '$f' was created" >&2
    FAILED=1
  fi
done

exit "$FAILED"
