#!/usr/bin/env bash
# Case: kiro-profile-detection
set -uo pipefail
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

FAILED=0
HAY=$(collect_haystack)

require "$HAY" "kiro profile named" 'kiro'
require "$HAY" "feature folder named" 'user-login'
require "$HAY" "missing artefact named" 'design\.md'
require "$HAY" "missing artefact described" 'missing|absent|not (present|found)|incomplete|expected'

# The bookkeeping artefacts belong under the kiro spec root, not a fabricated
# docs/specs/ tree.
if ! find .kiro -path '*/meta/lint-report-*.md' -type f 2>/dev/null | grep -q .; then
  echo "FAIL: no lint report under the kiro spec root's meta/ directory" >&2
  FAILED=1
fi
if [ -d "docs/specs" ]; then
  echo "FAIL: fabricated docs/specs/ tree in a kiro repo" >&2
  FAILED=1
fi

exit "$FAILED"
