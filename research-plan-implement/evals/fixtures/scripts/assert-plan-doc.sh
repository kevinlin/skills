#!/usr/bin/env bash
# Case: plan-from-existing-research
#
# Exit 0 = PASS, non-zero = FAIL. Working directory is the case workspace root.
# Helpers are inlined rather than sourced: skill-up copies only the file named
# by `judge.script_path`, so a sibling lib.sh would not exist at run time.
set -uo pipefail

workspace_find() {
  find . \( -path './.git' -o -path './.claude' -o -path './.codex' -o -path './node_modules' \) \
    -prune -o "$@" -print 2>/dev/null
}

FAILED=0
note() { echo "FAIL: $1" >&2; FAILED=1; }

require() {
  grep -qiE "$3" "$1" || note "$2 — no match for /$3/ in $1"
}

SEEDED_RESEARCH="docs/research/2026-08-18-multi-currency-ledger.md"

# --- Phase 1 was skipped, not repeated --------------------------------------
RESEARCH_DOCS=""
while IFS= read -r f; do
  if grep -qiE '^#+[[:space:]]*research question' "$f"; then
    RESEARCH_DOCS="${RESEARCH_DOCS}${f}
"
  fi
done < <(workspace_find -type f -name '*.md' | sort)
COUNT=$(printf '%s' "$RESEARCH_DOCS" | grep -c . )
if [ "$COUNT" -gt 1 ]; then
  note "research was redone — $COUNT documents carry a Research Question heading: $(printf '%s' "$RESEARCH_DOCS" | tr '\n' ' ')"
fi
[ -f "$SEEDED_RESEARCH" ] || note "the seeded research document was moved or deleted"

# --- locate the plan --------------------------------------------------------
PLAN=""
while IFS= read -r f; do
  [ "$f" = "./$SEEDED_RESEARCH" ] && continue
  if grep -qiE 'desired end state|implementation plan' "$f"; then PLAN="$f"; break; fi
done < <(workspace_find -type f -name '*.md' | sort)

if [ -z "$PLAN" ]; then
  echo "FAIL: no implementation plan was written" >&2
  echo "note: markdown files in the workspace: $(workspace_find -type f -name '*.md' | tr '\n' ' ')" >&2
  exit 1
fi

BASE=$(basename "$PLAN")
printf '%s' "$BASE" | grep -qE '^[0-9]{4}-[0-9]{2}-[0-9]{2}' \
  || note "filename '$BASE' does not start with the guide's YYYY-MM-DD prefix"

# --- plan template sections -------------------------------------------------
require "$PLAN" "Overview section" '^#+[[:space:]]*overview'
require "$PLAN" "Current State section" '^#+[[:space:]]*current state'
require "$PLAN" "Desired End State section" '^#+[[:space:]]*desired end state'
require "$PLAN" "out-of-scope section" "not doing|out of scope"
require "$PLAN" "Implementation Approach section" '^#+[[:space:]]*implementation approach'
require "$PLAN" "numbered phase heading" '^#+[[:space:]]*phase 1'

# --- the claim that distinguishes this skill's plans ------------------------
require "$PLAN" "Automated Verification criteria" 'automated verification'
require "$PLAN" "Manual Verification criteria" 'manual verification'
grep -qE '^[[:space:]]*- \[[ xX]\]' "$PLAN" \
  || note "success criteria are not checkbox items"

# --- open questions resolved ------------------------------------------------
if grep -qiE 'TBD|to be decided|to be determined|decide later|\?\?\?' "$PLAN"; then
  note "plan still carries an unresolved placeholder: $(grep -inE 'TBD|to be decided|to be determined|decide later|\?\?\?' "$PLAN" | head -3 | tr '\n' ' ')"
fi

# --- continuity with the research it was built on ---------------------------
require "$PLAN" "reference back to the research document" 'multi-currency-ledger|docs/research'
# The approved approach, taken from the prompt.
require "$PLAN" "the approved read-time conversion approach" 'compute_balance'

# --- the approval gate: no implementation before the plan is approved -------
EXTRA=$(workspace_find -type f -name '*.py' | sed 's|^\./||' \
  | grep -vE '^(src/ledger\.py|src/balance\.py|src/api\.py|tests/test_balance\.py)$')
if [ -n "$EXTRA" ]; then
  note "implementation started before plan approval — unexpected files: $(printf '%s' "$EXTRA" | tr '\n' ' ')"
fi
grep -q 'SENTINEL-LEDGER-BODY' src/ledger.py 2>/dev/null \
  || note "src/ledger.py was edited during planning"
grep -q 'GBP assumed' src/balance.py 2>/dev/null \
  || note "src/balance.py was edited during planning"

if [ "$FAILED" -eq 0 ]; then
  echo "PASS: plan at $PLAN built on the seeded research, no code written"
fi
exit "$FAILED"
