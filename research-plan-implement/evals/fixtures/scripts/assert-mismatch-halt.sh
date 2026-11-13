#!/usr/bin/env bash
# Case: halts-on-plan-mismatch
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

PLAN="docs/plans/2026-08-19-discount-currency.md"
[ -f "$PLAN" ] || { echo "FAIL: the seeded plan is gone from $PLAN" >&2; exit 1; }

# --- nothing was improvised --------------------------------------------------
[ -f src/pricing.py ] && note "src/pricing.py was written from scratch instead of raising the mismatch"
grep -qi 'discount' src/balance.py 2>/dev/null \
  && note "the change was silently retargeted at src/balance.py"

EXTRA=$(workspace_find -type f -name '*.py' | sed 's|^\./||' \
  | grep -vE '^(src/ledger\.py|src/balance\.py|src/api\.py|tests/test_balance\.py)$')
if [ -n "$EXTRA" ]; then
  note "new modules appeared instead of a question: $(printf '%s' "$EXTRA" | tr '\n' ' ')"
fi
grep -qE '^[[:space:]]*- \[[xX]\]' "$PLAN" \
  && note "a success criterion was ticked off although Phase 1 could not be implemented"

# --- the reply explains the mismatch and hands the decision back ------------
MSG_SRC="${EVAL_FINAL_MESSAGE:-}"
if [ -z "$MSG_SRC" ]; then
  echo "FAIL: EVAL_FINAL_MESSAGE is empty — the mismatch report cannot be checked" >&2
  exit 2
fi
MSG_FILE=$(mktemp)
trap 'rm -f "$MSG_FILE"' EXIT
if [ -f "$MSG_SRC" ]; then cat "$MSG_SRC" >"$MSG_FILE"; else printf '%s\n' "$MSG_SRC" >"$MSG_FILE"; fi

grep -qiE 'pricing|apply_discount' "$MSG_FILE" \
  || note "the reply does not name the module or function the plan expected"
grep -qiE "does not exist|doesn't exist|not exist|there is no|no[^[:alnum:]]+(src/)?pricing|no such file|does not contain|doesn't contain|not found|can't find|cannot find|couldn't find|could not find|missing|absent|mismatch" "$MSG_FILE" \
  || note "the reply does not say the expected code is not there"
grep -qiE "how should i proceed|how would you like|how do you want|options|option 1|which option|let me know|shall i|should i|before i|your call|prefer" "$MSG_FILE" \
  || note "the reply does not hand the decision back to the user"

if [ "$FAILED" -eq 0 ]; then
  echo "PASS: mismatch reported, nothing improvised, decision handed back"
fi
exit "$FAILED"
