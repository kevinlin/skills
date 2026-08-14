#!/usr/bin/env bash
# Shared helpers for spec-lint case judges.
#
# Every judge grades the same haystack: the dated lint report(s) the skill
# writes under a meta/ directory, plus the agent's final message. A finding
# counts whether it was delivered in the report file, the reply, or both.

collect_haystack() {
  local reports
  reports=$(find . -path '*/meta/lint-report-*.md' -type f 2>/dev/null)
  if [ -n "$reports" ]; then
    # shellcheck disable=SC2086
    cat $reports 2>/dev/null
  fi
  printf '\n%s\n' "${EVAL_FINAL_MESSAGE:-}"
}

# require <haystack> <label> <extended-regex>
require() {
  local hay="$1" label="$2" pattern="$3"
  if printf '%s' "$hay" | grep -qiE "$pattern"; then
    return 0
  fi
  echo "FAIL: $label — no match for /$pattern/" >&2
  FAILED=1
}

# reject <haystack> <label> <extended-regex>
reject() {
  local hay="$1" label="$2" pattern="$3"
  if printf '%s' "$hay" | grep -qiE "$pattern"; then
    echo "FAIL: $label — unexpected match for /$pattern/" >&2
    FAILED=1
  fi
}
