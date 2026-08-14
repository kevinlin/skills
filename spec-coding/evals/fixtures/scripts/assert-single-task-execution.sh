#!/usr/bin/env bash
# Case: execute-one-task-only
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

# require_cs <haystack> <label> <extended-regex>   (case-sensitive)
require_cs() {
  local hay="$1" label="$2" pattern="$3"
  printf '%s' "$hay" | grep -qE "$pattern" && return 0
  echo "FAIL: $label — no match for /$pattern/" >&2
  FAILED=1
}

FAILED=0
MSG="${EVAL_FINAL_MESSAGE:-}"
TASKS="docs/specs/rate-limiting/tasks.md"

# Task 2 is implemented.
LIMITER=$(cat src/limiter.py 2>/dev/null)
if printf '%s' "$LIMITER" | grep -q "NotImplementedError"; then
  echo "FAIL: TokenBucket.consume is still a stub" >&2
  FAILED=1
fi
require_cs "$LIMITER" "consume still defined" 'def consume'
require "$LIMITER" "refill by elapsed time" 'monotonic|elapsed|updated_at|refill'

# Task 2 is ticked off; tasks 3 and 4 are not.
TASK_BODY=$(cat "$TASKS" 2>/dev/null)
require_cs "$TASK_BODY" "task 2 marked complete" '^[[:space:]]*- \[[xX]\] 2\.'
require_cs "$TASK_BODY" "task 3 left unchecked" '^[[:space:]]*- \[ \] 3\.'
require_cs "$TASK_BODY" "task 4 left unchecked" '^[[:space:]]*- \[ \] 4\.'

# "Don't implement ahead" — tasks 3 and 4 own these files.
for f in src/middleware.py src/metrics.py; do
  if [ -e "$f" ]; then
    echo "FAIL: implemented ahead — '$f' belongs to a later unchecked task" >&2
    FAILED=1
  fi
done
if grep -qiE "middleware|ratelimitmetrics" src/app.py 2>/dev/null; then
  echo "FAIL: implemented ahead — src/app.py was wired up for task 3" >&2
  FAILED=1
fi

# "Stop and let the user review before moving on."
require "$MSG" "hands back for review" \
  'review|let me know|confirm|shall i|want me to|ready|next task|task 3|before (i|we) (move|continue|go)'

exit "$FAILED"
