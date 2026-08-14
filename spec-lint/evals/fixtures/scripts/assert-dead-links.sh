#!/usr/bin/env bash
# Case: default-profile-dead-links
set -uo pipefail
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

FAILED=0
HAY=$(collect_haystack)

require "$HAY" "default profile named" 'default'
require "$HAY" "missing link target named" 'requirements_billing\.md'
require "$HAY" "missing target described as broken" 'dead|broken|not found|does not exist|missing|unresolved'
require "$HAY" "missing anchor reported" 'data-flow|data flow'
require "$HAY" "anchor defect described" 'anchor|heading'

exit "$FAILED"
