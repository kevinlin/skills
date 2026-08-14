#!/usr/bin/env bash
# Case: goal-confirmation-first
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

# no_artifact <filename> <label> — the named artefact must not exist anywhere.
no_artifact() {
  local name="$1" label="$2" hits
  hits=$(workspace_find -type f -name "$name")
  if [ -n "$hits" ]; then
    echo "FAIL: $label — found $(printf '%s' "$hits" | tr '\n' ' ')" >&2
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
MSG="${EVAL_FINAL_MESSAGE:-}"

# Stage 1 puts questions back to the user before any document exists.
require "$MSG" "reply asks the user something" '\?'
require "$MSG" "reply probes at least one Stage 1 topic" \
  'scope|out of scope|boundar|problem|who |users?|customer|constraint|integrat|behaviou?r|outcome|channel|trigger'

# No Stage 2-4 artefact may exist yet.
no_artifact requirements.md "wrote requirements before the goal was confirmed"
no_artifact design.md "wrote a design before the goal was confirmed"
no_artifact tasks.md "wrote a task plan before the goal was confirmed"

# Nor may implementation start.
only_seeded_python '^(src/checkout\.py|src/orders\.py|tests/test_orders\.py)$'

exit "$FAILED"
