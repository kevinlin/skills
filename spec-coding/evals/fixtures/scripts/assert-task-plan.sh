#!/usr/bin/env bash
# Case: task-plan-checkboxes
set -uo pipefail

# Helpers are inlined, not sourced: skill-up copies only the file named by
# `judge.script_path` into its temp dir, so a sibling lib.sh is not there at
# run time and every helper call would silently be a command-not-found.

# find over the case workspace, skipping git metadata and the installed skill.
workspace_find() {
  find . \( -path './.git' -o -path './.claude' -o -path './node_modules' \) -prune -o "$@" -print 2>/dev/null
}

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

# reject <haystack> <label> <extended-regex>   (case-insensitive)
reject() {
  local hay="$1" label="$2" pattern="$3"
  if printf '%s' "$hay" | grep -qiE "$pattern"; then
    echo "FAIL: $label — unexpected match for /$pattern/" >&2
    FAILED=1
  fi
}

# only_seeded_python <allowed-regex> — no Python file outside the seeded set.
only_seeded_python() {
  local allowed="$1" extra
  extra=$(workspace_find -type f -name '*.py' | sed 's|^\./||' | grep -vE "$allowed")
  if [ -n "$extra" ]; then
    echo "FAIL: implementation started early — unexpected files: $(printf '%s' "$extra" | tr '\n' ' ')" >&2
    FAILED=1
  fi
}

FAILED=0

TASKS="docs/specs/discount-codes/tasks.md"
if [ ! -f "$TASKS" ]; then
  FOUND=$(workspace_find -type f -name tasks.md | head -1)
  if [ -z "$FOUND" ]; then
    echo "FAIL: no tasks.md was written" >&2
    exit 1
  fi
  echo "FAIL: tasks.md landed at '$FOUND', not beside the approved design" >&2
  FAILED=1
  TASKS="$FOUND"
fi

BODY=$(cat "$TASKS")

# Numbered checkbox list, everything still open.
require_cs "$BODY" "numbered first checkbox task" '^[[:space:]]*- \[ \] 1\.'
OPEN=$(printf '%s\n' "$BODY" | grep -cE '^[[:space:]]*- \[ \]')
if [ "$OPEN" -lt 3 ]; then
  echo "FAIL: only $OPEN unchecked tasks — the design has more work than that" >&2
  FAILED=1
fi
if printf '%s\n' "$BODY" | grep -qE '^[[:space:]]*- \[[xX]\]'; then
  echo "FAIL: a task is pre-checked in a plan nothing has executed yet" >&2
  FAILED=1
fi

# "Reference specific acceptance criteria from requirements."
require "$BODY" "requirement references" 'requirement'
# "Specifies which files or components to create/modify."
require "$BODY" "files or components named" 'src/|discounts|DiscountResolver|DiscountCode|checkout'
# Tests planned early, per the TDD sequencing principle.
require "$BODY" "test work planned" 'test'

# "Exclude deployment, user testing, performance monitoring, and other
# non-coding activities" — the design's rollout section is bait.
reject "$BODY" "non-coding task in the checklist" \
  '^[[:space:]]*- \[[ xX]\].*(deploy|rollout|roll out|monitor|user acceptance|user testing|stakeholder|announce)'

# Planning is not execution.
only_seeded_python '^(src/checkout\.py|src/orders\.py|tests/test_orders\.py)$'
if ! grep -q "SENTINEL-ORDERS-BODY" src/orders.py 2>/dev/null; then
  echo "FAIL: src/orders.py was edited during task planning" >&2
  FAILED=1
fi
if grep -qi "discount" src/orders.py src/checkout.py 2>/dev/null; then
  echo "FAIL: the feature was implemented during task planning" >&2
  FAILED=1
fi

exit "$FAILED"
