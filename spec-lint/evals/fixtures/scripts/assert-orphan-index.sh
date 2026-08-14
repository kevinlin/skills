#!/usr/bin/env bash
# Case: orphan-and-index-drift
set -uo pipefail
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

FAILED=0
HAY=$(collect_haystack)

require "$HAY" "orphan file named" 'design_reporting\.md'
require "$HAY" "orphan or index drift described" 'orphan|no inbound|not linked|absent from|missing from (the )?index|not (listed|referenced) in'
require "$HAY" "root index inspected" 'index\.md'
reject "$HAY" "wired-up billing plan not flagged as an orphan" 'orphan.*plan_billing\.md'

exit "$FAILED"
