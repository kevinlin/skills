#!/usr/bin/env bash
# Case: implements-first-phase-only
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

# ticked <text> — true when the text holds at least one checked box.
ticked() { printf '%s\n' "$1" | grep -qE '^[[:space:]]*- \[[xX]\]'; }

PLAN="docs/plans/2026-08-19-multi-currency-ledger.md"
[ -f "$PLAN" ] || { echo "FAIL: the seeded plan is gone from $PLAN" >&2; exit 1; }

# --- Phase 1 was implemented ------------------------------------------------
if grep -q 'NotImplementedError' src/fx.py 2>/dev/null; then
  note "src/fx.py still raises NotImplementedError — Phase 1 was not implemented"
fi
grep -q '7900' tests/test_fx.py 2>/dev/null \
  || note "the Phase 1 test was weakened — its 7900 assertion is gone"

if command -v python3 >/dev/null 2>&1; then
  if ! OUT=$(PYTHONPATH=. python3 tests/test_fx.py 2>&1); then
    note "the plan's Phase 1 automated check fails: PYTHONPATH=. python3 tests/test_fx.py -> $(printf '%s' "$OUT" | tail -2 | tr '\n' ' ')"
  fi
else
  echo "note: python3 not on PATH; skipped running the Phase 1 automated check" >&2
fi

# --- one phase at a time ----------------------------------------------------
P1=$(sed -n '/^##*[[:space:]]*Phase 1/,/^##*[[:space:]]*Phase 2/p' "$PLAN")
P2=$(sed -n '/^##*[[:space:]]*Phase 2/,/^##*[[:space:]]*Phase 3/p' "$PLAN")
P3=$(sed -n '/^##*[[:space:]]*Phase 3/,$p' "$PLAN")
[ -n "$P1" ] || note "the Phase 1 heading is no longer in the plan"

P1_AUTO=$(printf '%s\n' "$P1" | sed -n '/[Aa]utomated [Vv]erification/,/[Mm]anual [Vv]erification/p')
P1_MANUAL=$(printf '%s\n' "$P1" | sed -n '/[Mm]anual [Vv]erification/,$p')

ticked "$P1_AUTO" || note "Phase 1's automated criteria were left unticked after passing"
ticked "$P1_MANUAL" && note "Phase 1's manual criteria were ticked without user confirmation"
ticked "$P2" && note "Phase 2 boxes were ticked — the run went past one phase"
ticked "$P3" && note "Phase 3 boxes were ticked — the run went past one phase"

# --- Phase 2 and Phase 3 work must not have happened ------------------------
[ -f src/rates.py ] && note "src/rates.py exists — Phase 2 ran before user confirmation"
grep -q '"convert"' src/api.py 2>/dev/null && note "a convert route was added — Phase 3 ran before user confirmation"
grep -q 'SENTINEL-API-ROUTES' src/api.py 2>/dev/null \
  || note "src/api.py was rewritten — Phase 3 is not in scope yet"

EXTRA=$(workspace_find -type f -name '*.py' | sed 's|^\./||' \
  | grep -vE '^(src/ledger\.py|src/balance\.py|src/api\.py|src/fx\.py|tests/test_balance\.py|tests/test_fx\.py)$')
if [ -n "$EXTRA" ]; then
  note "unexpected modules for a Phase 1 run: $(printf '%s' "$EXTRA" | tr '\n' ' ')"
fi

# --- the pause ---------------------------------------------------------------
MSG_SRC="${EVAL_FINAL_MESSAGE:-}"
if [ -z "$MSG_SRC" ]; then
  echo "note: EVAL_FINAL_MESSAGE not provided by the runner; skipped the hand-back check" >&2
else
  MSG_FILE=$(mktemp)
  trap 'rm -f "$MSG_FILE"' EXIT
  if [ -f "$MSG_SRC" ]; then cat "$MSG_SRC" >"$MSG_FILE"; else printf '%s\n' "$MSG_SRC" >"$MSG_FILE"; fi
  grep -qiE 'manual verification|manual check|verify manually|manual step' "$MSG_FILE" \
    || note "the reply does not hand the manual verification steps back to the user"
fi

if [ "$FAILED" -eq 0 ]; then
  echo "PASS: Phase 1 implemented and ticked, Phases 2-3 untouched, manual steps handed back"
fi
exit "$FAILED"
