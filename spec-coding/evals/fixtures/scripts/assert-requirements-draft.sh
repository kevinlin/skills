#!/usr/bin/env bash
# Case: requirements-ears-draft
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

REQ=$(workspace_find -type f -name requirements.md | head -1)
if [ -z "$REQ" ]; then
  echo "FAIL: no requirements.md was written" >&2
  exit 1
fi

# "All spec artifacts live in docs/specs/{feature-name}/ (kebab-case)."
if ! printf '%s' "$REQ" | grep -qE '^\./docs/specs/[a-z0-9]+(-[a-z0-9]+)*/requirements\.md$'; then
  echo "FAIL: '$REQ' is not docs/specs/<kebab-case-feature>/requirements.md" >&2
  FAILED=1
fi

BODY=$(cat "$REQ")
require "$BODY" "introduction section" '^#+ *introduction'
require "$BODY" "user story per requirement" 'user story'
require "$BODY" "acceptance criteria" 'acceptance criteria'
require_cs "$BODY" "EARS SHALL clause" 'SHALL'
require_cs "$BODY" "EARS trigger keyword" '(^|[^A-Za-z])(WHEN|WHERE|IF|WHILE)([^A-Za-z]|$)'
# The stated goal's rejection cases have to survive into the requirements.
require "$BODY" "expiry rejection captured" 'expir'
require "$BODY" "usage cap captured" 'cap|limit|exhaust|remaining use'

# Approval gate — Stage 3 and Stage 4 artefacts must not exist yet.
no_artifact design.md "ran ahead to the design without approval"
no_artifact tasks.md "ran ahead to task planning without approval"
only_seeded_python '^(src/checkout\.py|src/orders\.py|tests/test_orders\.py)$'

# "Present it and ask if it looks good."
require "$MSG" "reply asks for approval" '\?|approve|approval|look good|looks good|sign off|feedback|let me know'

exit "$FAILED"
