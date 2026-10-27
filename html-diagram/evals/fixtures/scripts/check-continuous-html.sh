#!/usr/bin/env bash
# Judge for Rule 2 (no empty lines inside the HTML diagram block) plus the
# Rule 0 / Rule 1 baseline: skill class vocabulary present, no ```html fence,
# no ASCII or Mermaid substitute.
#
# Exit 0 = PASS, non-zero = FAIL. Reads the agent's final message from
# $EVAL_FINAL_MESSAGE, which may hold either the text itself or a path to it.
set -uo pipefail

msg_src="${EVAL_FINAL_MESSAGE:-}"
if [ -z "$msg_src" ]; then
  echo "FAIL: EVAL_FINAL_MESSAGE is empty" >&2
  exit 2
fi

response_file="$(mktemp)"
trap 'rm -f "$response_file"' EXIT
if [ -f "$msg_src" ]; then
  cat "$msg_src" >"$response_file"
else
  printf '%s\n' "$msg_src" >"$response_file"
fi

fail=0
note() { echo "FAIL: $1" >&2; fail=1; }

# --- Rule 0: the skill's own vocabulary, no substitutes -----------------------
for needle in 'arch-box' '<style' '<div'; do
  grep -qF "$needle" "$response_file" || note "response is missing '$needle'"
done
grep -qE 'arch-(layer|stage|pipeline)' "$response_file" \
  || note "no arch-layer / arch-stage / arch-pipeline container found"

for banned in '```html' '```HTML' '```mermaid' 'graph TD' 'graph LR'; do
  grep -qF "$banned" "$response_file" && note "response contains banned '$banned'"
done
grep -qE '[┌┐└┘│─├┤┬┴┼]' "$response_file" \
  && note "response contains box-drawing ASCII art"

# --- Rule 2: the HTML block has no empty lines -------------------------------
# Slice from the first line holding '<div' through the last line holding
# '</div>', then look for a blank or whitespace-only line inside that slice.
blank_lines="$(
  awk '
    /<div/ && !seen { seen = 1 }
    seen { buf[++n] = $0; if (/<\/div>/) last = n }
    END { for (i = 1; i <= last; i++) print buf[i] }
  ' "$response_file" | grep -c '^[[:space:]]*$'
)"
if [ "${blank_lines:-0}" -gt 0 ]; then
  note "HTML block contains $blank_lines empty line(s) — Rule 2 requires it be continuous"
fi

if [ "$fail" -ne 0 ]; then
  exit 1
fi
echo "PASS: continuous HTML block using the skill's class vocabulary"
exit 0
