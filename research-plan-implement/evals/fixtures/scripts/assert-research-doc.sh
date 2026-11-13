#!/usr/bin/env bash
# Case: research-doc-and-stop
#
# Exit 0 = PASS, non-zero = FAIL. Working directory is the case workspace root.
# Helpers are inlined rather than sourced: skill-up copies only the file named
# by `judge.script_path`, so a sibling lib.sh would not exist at run time.
set -uo pipefail

# find over the case workspace, skipping git metadata and the installed skill.
workspace_find() {
  find . \( -path './.git' -o -path './.claude' -o -path './.codex' -o -path './node_modules' \) \
    -prune -o "$@" -print 2>/dev/null
}

FAILED=0
note() { echo "FAIL: $1" >&2; FAILED=1; }

# require <file> <label> <extended-regex>  (case-insensitive)
require() {
  grep -qiE "$3" "$1" || note "$2 — no match for /$3/ in $1"
}

# --- locate the research document -------------------------------------------
DOC=""
while IFS= read -r f; do
  if grep -qiE '^#+[[:space:]]*research question' "$f"; then DOC="$f"; break; fi
done < <(workspace_find -type f -name '*.md' | sort)

if [ -z "$DOC" ]; then
  echo "FAIL: no research document with a 'Research Question' heading was written" >&2
  echo "note: markdown files in the workspace: $(workspace_find -type f -name '*.md' | tr '\n' ' ')" >&2
  exit 1
fi

# --- document shape ---------------------------------------------------------
[ "$(head -1 "$DOC")" = "---" ] || note "no YAML frontmatter at the top of $DOC"
head -25 "$DOC" | grep -qiE '^topic:' || note "frontmatter has no topic: field in $DOC"

BASE=$(basename "$DOC")
printf '%s' "$BASE" | grep -qE '^[0-9]{4}-[0-9]{2}-[0-9]{2}' \
  || note "filename '$BASE' does not start with the guide's YYYY-MM-DD prefix"

require "$DOC" "Summary section" '^#+[[:space:]]*.*summary'
require "$DOC" "Detailed Findings section" '^#+[[:space:]]*.*findings'
require "$DOC" "Code References section" '^#+[[:space:]]*.*code references'
require "$DOC" "Open Questions section" '^#+[[:space:]]*.*open questions'

# Findings have to point at lines, not just files.
grep -qE '\.py(:|#L)[0-9]+' "$DOC" || note "no file:line reference anywhere in $DOC"

# The amount path runs through both of these; a trace that misses either is thin.
require "$DOC" "the balance calculation named" 'compute_balance'
require "$DOC" "the entry recording named" 'post_entry'

# --- the approval gate: Phase 1 stops before planning and before code -------
while IFS= read -r f; do
  if grep -qiE 'automated verification|manual verification|desired end state' "$f"; then
    note "plan-shaped document at $f — Phase 1 hands back before planning"
  fi
done < <(workspace_find -type f -name '*.md' | sort)

EXTRA=$(workspace_find -type f -name '*.py' | sed 's|^\./||' \
  | grep -vE '^(src/ledger\.py|src/balance\.py|src/api\.py|tests/test_balance\.py)$')
if [ -n "$EXTRA" ]; then
  note "code was written during research — unexpected files: $(printf '%s' "$EXTRA" | tr '\n' ' ')"
fi
grep -q 'SENTINEL-LEDGER-BODY' src/ledger.py 2>/dev/null \
  || note "src/ledger.py was rewritten during research"

if [ "$FAILED" -eq 0 ]; then
  echo "PASS: research document at $DOC, no plan and no code yet"
fi
exit "$FAILED"
