#!/usr/bin/env bash
# Grader self-test: runs every script judge from a copy in a fresh temp dir, as skill-up does,
# against good and bad workspaces. Prints "ok" and exits 0 when every judge behaves as expected.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONDONTWRITEBYTECODE=1

python3 "$here/../build_manifests.py" --check

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
for src in "$here"/judge_*.py; do
  name="$(basename "$src" .py)"
  name="${name#judge_}"
  mkdir -p "$tmp/judges/$name"
  cp "$src" "$tmp/judges/$name/script"   # skill-up uploads a judge as a file named "script"
  chmod 700 "$tmp/judges/$name/script"
done
mkdir "$tmp/work"

python3 "$here/selftest.py" "$tmp/judges" "$tmp/work"
echo ok
