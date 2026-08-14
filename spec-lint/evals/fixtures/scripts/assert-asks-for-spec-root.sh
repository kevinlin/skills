#!/usr/bin/env bash
# Case: no-specs-asks-user
set -uo pipefail

FAILED=0
MSG="${EVAL_FINAL_MESSAGE:-}"

# The reply must say no spec root was found and put the question back to the user.
if ! printf '%s' "$MSG" | grep -qiE "could ?n.t find|could not find|did ?n.t find|did not find|no spec|none of the|unable to (find|locate)|no .*(spec|profile).*(found|detected|match)"; then
  echo "FAIL: reply does not state that no spec root was found" >&2
  FAILED=1
fi
if ! printf '%s' "$MSG" | grep -qiE "where.*(spec|doc)|which (directory|folder|path)|point me|tell me where|let me know where|\?"; then
  echo "FAIL: reply does not ask the user where the specs live" >&2
  FAILED=1
fi

# Nothing may be invented on disk.
for d in docs/specs docs/spec specs spec .kiro openspec .planning _bmad-output; do
  if [ -e "$d" ]; then
    echo "FAIL: invented spec location '$d'" >&2
    FAILED=1
  fi
done
# `.claude/` holds the installed copy of the skill under test — its own bundled
# references/convention.md is not an invented artefact, so it is excluded.
if find . -path ./.claude -prune -o -name 'lint-report-*.md' -type f -print 2>/dev/null | grep -q .; then
  echo "FAIL: wrote a lint report despite having no spec root" >&2
  FAILED=1
fi
if find . -path ./.claude -prune -o -name 'convention.md' -type f -print 2>/dev/null | grep -q .; then
  echo "FAIL: seeded convention.md despite having no spec root" >&2
  FAILED=1
fi

exit "$FAILED"
