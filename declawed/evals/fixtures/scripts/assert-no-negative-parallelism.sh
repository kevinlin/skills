#!/usr/bin/env bash
# Fail if the rewritten prose still contains the "not X but Y" family or its
# banned escape hatches. Reads rewritten.md only, so changelog prose that names
# the patterns does not trigger a false failure.
set -uo pipefail

FILE="rewritten.md"
if [[ ! -f "$FILE" ]]; then
  echo "FAIL: $FILE was not produced"
  exit 1
fi

patterns=(
  "(is|are|isn'?t|was|wasn'?t|does|don'?t|doesn'?t) *n?o?t? just [^.!?]*(,| --| —|-) *(it'?s|they'?re|but)"
  "not (only|merely|simply) [^.!?]*(but|it'?s)"
  "it'?s not (about )?[^.!?]*(,|—) *it'?s"
  "less about [^.!?]* than"
  "the real [a-z]+ (here )?is"
  "the question (isn'?t|is not)"
  "— *not [^.!?]*, *but"
  "built not on"
)

failed=0
for p in "${patterns[@]}"; do
  if grep -inE "$p" "$FILE" >/dev/null; then
    echo "FAIL: negative-parallelism pattern survived: /$p/"
    grep -inE "$p" "$FILE"
    failed=1
  fi
done

puffery="pivotal|seismic|testament to|tapestry|delve|in today's|fast-paced world|game-?chang"
if grep -inE "$puffery" "$FILE" >/dev/null; then
  echo "FAIL: puffery survived"
  grep -inE "$puffery" "$FILE"
  failed=1
fi

if [[ $failed -eq 0 ]]; then
  echo "PASS: rewritten prose is free of the targeted tells"
fi
exit $failed
