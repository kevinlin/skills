#!/usr/bin/env bash
# Case: reverse-consistency-design-gap
set -uo pipefail
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

FAILED=0
HAY=$(collect_haystack)

# 5.8 — the design never mentions tax.
require "$HAY" "uncovered requirement named" 'tax|vat'
# 5.9 — the plan never mentions the audit log component.
require "$HAY" "uncovered design item named" 'auditlog|audit log|audit-log'
require "$HAY" "gaps described as coverage failures" \
  'cover|coverage|not addressed|unaddressed|no (corresponding|matching)|gap|missing'
require "$HAY" "design file named" 'design_billing\.md'
require "$HAY" "plan file named" 'plan_billing\.md'

exit "$FAILED"
