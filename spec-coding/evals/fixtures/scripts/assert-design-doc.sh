#!/usr/bin/env bash
# Case: design-doc-sections
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

DESIGN="docs/specs/discount-codes/design.md"
if [ ! -f "$DESIGN" ]; then
  FOUND=$(workspace_find -type f -name design.md | head -1)
  if [ -z "$FOUND" ]; then
    echo "FAIL: no design.md was written" >&2
    exit 1
  fi
  echo "FAIL: design.md landed at '$FOUND', not beside the approved requirements" >&2
  FAILED=1
  DESIGN="$FOUND"
fi

BODY=$(cat "$DESIGN")
require "$BODY" "Overview section" 'overview'
require "$BODY" "Architecture section" 'architecture'
require "$BODY" "Components and Interfaces section" 'component'
require "$BODY" "Data Models section" 'data model|schema'
require "$BODY" "Error Handling section" 'error handling'
require "$BODY" "Testing Strategy section" 'testing strategy|test strategy|testing approach'
# Research folded into the design: it has to name the code it plugs into.
require "$BODY" "existing code named" 'checkout|create_order|orders\.py'
# Requirement coverage, including the refusal paths.
require "$BODY" "refusal paths addressed" 'expir'

# Approval gate — Stage 4 must wait, and no code may be written yet.
no_artifact tasks.md "ran ahead to task planning without approval"
only_seeded_python '^(src/checkout\.py|src/orders\.py|tests/test_orders\.py)$'

if [ ! -f "docs/specs/discount-codes/requirements.md" ]; then
  echo "FAIL: the approved requirements.md was moved or deleted" >&2
  FAILED=1
fi

exit "$FAILED"
