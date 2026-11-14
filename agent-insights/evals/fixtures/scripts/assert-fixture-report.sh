#!/usr/bin/env bash
# Judge for the fixture-home-report case.
#
# PASS when the run produced the artefacts Steps 3-6 promise, with numbers that match
# the seeded home exactly: 3 sessions across claude-code, codex and opencode, 7 user
# messages, 2 skill invocations merging into one skill name, an analysis model that is
# a real base model id, every narrative section written, and one self-contained
# 0600 HTML report. Exit 0 = PASS.

set -u

DATA="insights-data"

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

[ -d "$DATA" ] || fail "$DATA/ does not exist — the run ignored the --data-dir it was given"
[ -f "$DATA/aggregate.json" ] || fail "$DATA/aggregate.json missing — Step 3 never ran"
[ -f "$DATA/narrative.json" ] || fail "$DATA/narrative.json missing — Step 4 never ran"

REPORTS=$(find "$DATA" -maxdepth 1 -name 'report-*_30-days.html' | sort)
COUNT=$(printf '%s\n' "$REPORTS" | grep -c . || true)
[ "$COUNT" -eq 1 ] || fail "expected exactly one report-YYYY-MM-DD_30-days.html in $DATA, found $COUNT"
REPORT=$(printf '%s\n' "$REPORTS" | head -1)

# --- rendered report -------------------------------------------------------------

MODE=$(stat -f "%Lp" "$REPORT" 2>/dev/null || stat -c "%a" "$REPORT")
[ "$MODE" = "600" ] || fail "report is mode $MODE, not 600 — it carries transcript snippets"

grep -Eq '(src|href)="https?://' "$REPORT" \
  && fail "the report pulls a resource off the network — it is supposed to be self-contained"

for needle in "Per-Tool Breakdown" "Skill invocations" "Skills used" \
              "Analysis model (main agent)" "spec-lint" \
              "claude-code" "codex" "opencode" \
              "claude-opus-4-5" "gpt-5.5" "gpt-5.2"; do
  grep -Fq "$needle" "$REPORT" || fail "the report never mentions '$needle'"
done

grep -Fq "Analysis model (main agent): unknown" "$REPORT" \
  && fail "the report records the analysis model as 'unknown' — Step 3 dropped --analysis-model"

# --- aggregate + narrative -------------------------------------------------------

python3 - "$DATA" <<'PY' || exit 1
import json
import re
import sys

data = sys.argv[1]
problems = []


def load(name):
    with open(f"{data}/{name}", encoding="utf-8") as fh:
        return json.load(fh)


agg = load("aggregate.json")
nar = load("narrative.json")
totals = agg.get("totals") or {}
per_tool = agg.get("per_tool") or {}
dist = agg.get("distributions") or {}


def eq(actual, expected, what):
    if actual != expected:
        problems.append(f"{what}: expected {expected!r}, got {actual!r}")


# Numbers the seeded home fixes in advance.
eq(totals.get("sessions"), 3, "aggregate totals.sessions")
eq(totals.get("user_messages"), 7, "aggregate totals.user_messages")
eq(totals.get("skill_invocations"), 2, "aggregate totals.skill_invocations")
eq(sorted(totals.get("tools_detected") or []),
   ["claude-code", "codex", "opencode"], "aggregate totals.tools_detected")
eq(sorted(totals.get("models_detected") or []),
   ["claude-opus-4-5", "gpt-5.2", "gpt-5.5"], "aggregate totals.models_detected")
# /spec-lint in opencode and the Skill tool call in claude-code are one skill, not two.
eq((dist.get("skills_used") or {}).get("spec-lint"), 2,
   "distributions.skills_used['spec-lint'] (cross-tool merge)")

for tool, skills in (("claude-code", 1), ("codex", 0), ("opencode", 1)):
    pt = per_tool.get(tool)
    if not pt:
        problems.append(f"per_tool is missing {tool}")
        continue
    eq(pt.get("sessions"), 1, f"per_tool[{tool}].sessions")
    eq(pt.get("skill_invocations"), skills, f"per_tool[{tool}].skill_invocations")

# Step 3: the analysing model, base id only.
model = (agg.get("analysis_model") or "").strip()
if not model or model == "unknown":
    problems.append("aggregate analysis_model is 'unknown' — --analysis-model was not passed")
elif not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", model):
    problems.append(f"analysis_model {model!r} is not a bare base model id "
                    "(runtime/context suffixes must be stripped)")

# Step 4: every section, and the version stamp copied from the aggregate.
glance = nar.get("at_a_glance") or {}
for key in ("persona", "whats_working", "whats_hindering", "quick_wins",
            "ambitious_workflows"):
    if not str(glance.get(key) or "").strip():
        problems.append(f"narrative at_a_glance.{key} is missing or empty")
persona = str(glance.get("persona") or "")
if not re.match(r"^You are an? .+\.", persona):
    problems.append(f"persona {persona!r} does not follow 'You are a <level> AI <user_type>.'")
for key in ("tool_comparison", "project_areas", "interaction_style", "what_works",
            "friction_analysis", "suggestions", "new_use_cases"):
    if not nar.get(key):
        problems.append(f"narrative section {key} is missing")
if nar.get("version") != agg.get("version"):
    problems.append(f"narrative version {nar.get('version')!r} does not match "
                    f"aggregate version {agg.get('version')!r}")

if problems:
    for p in problems:
        print(f"FAIL: {p}", file=sys.stderr)
    sys.exit(1)
PY

# --- Step 6 reply ----------------------------------------------------------------

MSG=${EVAL_FINAL_MESSAGE-__UNSET__}
if [ "$MSG" = "__UNSET__" ]; then
  echo "note: EVAL_FINAL_MESSAGE not provided by the runner; skipped the Step 6 reply checks" >&2
else
  printf '%s' "$MSG" | grep -Fq "3 sessions" \
    || fail "the reply's stats line does not say '3 sessions'"
  printf '%s' "$MSG" | grep -Eq "user messages" \
    || fail "the reply's stats line is missing the user-message count"
  printf '%s' "$MSG" | grep -Eq "You are an? " \
    || fail "the reply is missing the At a Glance persona one-liner"
  printf '%s' "$MSG" | grep -Eiq "what.?s working" \
    || fail "the reply is missing the What's working section"
  printf '%s' "$MSG" | grep -Eiq "hinder" \
    || fail "the reply is missing the What's hindering you section"
  printf '%s' "$MSG" | grep -Eiq "quick win" \
    || fail "the reply is missing the Quick wins section"
  printf '%s' "$MSG" | grep -Eiq "ambitious" \
    || fail "the reply is missing the Ambitious workflows section"
  printf '%s' "$MSG" | grep -Eq "report-[0-9]{4}-[0-9]{2}-[0-9]{2}_30-days\.html" \
    || fail "the reply never gives the path of the rendered report"
fi

echo "PASS: 3 sessions across 3 tools, 2 merged skill invocations, self-contained 0600 report"
exit 0
