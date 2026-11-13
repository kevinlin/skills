#!/usr/bin/env bash
# Case: resumes-from-checkmarks
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

ticked() { printf '%s\n' "$1" | grep -qE '^[[:space:]]*- \[[xX]\]'; }

PLAN="docs/plans/2026-08-19-multi-currency-ledger.md"
[ -f "$PLAN" ] || { echo "FAIL: the seeded plan is gone from $PLAN" >&2; exit 1; }

# --- Phase 2, the first unchecked item, was the work done -------------------
if [ ! -f src/rates.py ]; then
  note "src/rates.py was not created — Phase 2 is the first unchecked item"
else
  grep -qE 'def[[:space:]]+rate_for' src/rates.py || note "src/rates.py has no rate_for function"
fi
grep -q 'rate_for' src/fx.py 2>/dev/null \
  || note "src/fx.py does not delegate to rate_for — Phase 2's second change is missing"

# --- finished work was trusted, not redone ----------------------------------
grep -q '7900' tests/test_fx.py 2>/dev/null \
  || note "the Phase 1 test was rewritten — its 7900 assertion is gone"
if command -v python3 >/dev/null 2>&1; then
  if ! OUT=$(PYTHONPATH=. python3 tests/test_fx.py 2>&1); then
    note "conversion is broken after Phase 2: PYTHONPATH=. python3 tests/test_fx.py -> $(printf '%s' "$OUT" | tail -2 | tr '\n' ' ')"
  fi
else
  echo "note: python3 not on PATH; skipped running the conversion check" >&2
fi

P1=$(sed -n '/^##*[[:space:]]*Phase 1/,/^##*[[:space:]]*Phase 2/p' "$PLAN")
P2=$(sed -n '/^##*[[:space:]]*Phase 2/,/^##*[[:space:]]*Phase 3/p' "$PLAN")
P3=$(sed -n '/^##*[[:space:]]*Phase 3/,$p' "$PLAN")
[ -n "$P2" ] || note "the Phase 2 heading is no longer in the plan"

P1_AUTO=$(printf '%s\n' "$P1" | sed -n '/[Aa]utomated [Vv]erification/,/[Mm]anual [Vv]erification/p')
ticked "$P1_AUTO" || note "Phase 1's ticks were removed — completed work should be trusted, not re-verified"

P2_AUTO=$(printf '%s\n' "$P2" | sed -n '/[Aa]utomated [Vv]erification/,/[Mm]anual [Vv]erification/p')
P2_MANUAL=$(printf '%s\n' "$P2" | sed -n '/[Mm]anual [Vv]erification/,$p')
ticked "$P2_AUTO" || note "Phase 2's automated criteria were left unticked after passing"
ticked "$P2_MANUAL" && note "Phase 2's manual criteria were ticked without user confirmation"

# --- Phase 3 must still be waiting ------------------------------------------
ticked "$P3" && note "Phase 3 boxes were ticked — the run went past one phase"
grep -q '"convert"' src/api.py 2>/dev/null && note "a convert route was added — Phase 3 ran before user confirmation"
grep -q 'SENTINEL-API-ROUTES' src/api.py 2>/dev/null \
  || note "src/api.py was rewritten — Phase 3 is not in scope yet"

EXTRA=$(workspace_find -type f -name '*.py' | sed 's|^\./||' \
  | grep -vE '^(src/ledger\.py|src/balance\.py|src/api\.py|src/fx\.py|src/rates\.py|tests/test_balance\.py|tests/test_fx\.py)$')
if [ -n "$EXTRA" ]; then
  note "unexpected modules for a Phase 2 run: $(printf '%s' "$EXTRA" | tr '\n' ' ')"
fi

MSG_SRC="${EVAL_FINAL_MESSAGE:-}"
if [ -z "$MSG_SRC" ]; then
  echo "note: EVAL_FINAL_MESSAGE not provided by the runner; skipped the hand-back check" >&2
else
  MSG_FILE=$(mktemp)
  trap 'rm -f "$MSG_FILE"' EXIT
  if [ -f "$MSG_SRC" ]; then cat "$MSG_SRC" >"$MSG_FILE"; else printf '%s\n' "$MSG_SRC" >"$MSG_FILE"; fi
  grep -qiE 'manual verification|manual check|verify manually|manual step|phase 3' "$MSG_FILE" \
    || note "the reply neither hands back the manual steps nor says what comes next"
fi

if [ "$FAILED" -eq 0 ]; then
  echo "PASS: resumed at Phase 2, Phase 1 trusted, Phase 3 still waiting"
fi
exit "$FAILED"
