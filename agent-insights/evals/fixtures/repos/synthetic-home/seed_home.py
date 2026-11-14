#!/usr/bin/env python3
"""Lay down a synthetic home directory holding three AI coding agent sessions.

Usage: python3 seed_home.py [target_dir]      (default: ./home)

Eval fixture only. Timestamps are stamped relative to now, so the sessions always
fall inside the analysis window no matter when the suite runs — a static fixture
tree would age out of the window and start failing on its own. Log shapes mirror
the real per-tool layouts the skill's adapters parse (Claude Code JSONL, Codex
rollout JSONL, OpenCode JSON storage).

What the fixture contains:
  - claude-code : 1 session, model claude-opus-4-5, `Skill` tool call -> spec-lint
  - codex       : 1 session, model gpt-5.5, one shell function_call
  - opencode    : 1 session, model gpt-5.2, user message opening with /spec-lint

So: 3 sessions, 3 tools, 2 skill invocations that merge into one skill name.
"""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

NOW = time.time()
T0 = NOW - 2400  # 40 minutes ago


def iso(t):
    return datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def ms(t):
    return int(t * 1000)


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, (dict, list)):
        path.write_text(json.dumps(content), encoding="utf-8")
    else:
        path.write_text(content, encoding="utf-8")


def jsonl(items):
    return "\n".join(json.dumps(i) for i in items) + "\n"


def make_claude_code(home):
    lines = [
        {"type": "user", "timestamp": iso(T0), "cwd": "/tmp/checkout-api",
         "message": {"role": "user",
                     "content": "Add request throttling to the checkout API endpoints"}},
        {"type": "assistant", "timestamp": iso(T0 + 90),
         "message": {"role": "assistant", "model": "claude-opus-4-5", "content": [
             {"type": "text", "text": "Adding a token bucket throttle in the middleware."},
             {"type": "tool_use", "name": "Skill", "input": {"skill": "spec-lint"}},
             {"type": "tool_use", "name": "Edit", "input": {}}]}},
        {"type": "user", "timestamp": iso(T0 + 300), "cwd": "/tmp/checkout-api",
         "message": {"role": "user", "content": "the limit should be per API key, not per IP"}},
        {"type": "assistant", "timestamp": iso(T0 + 380),
         "message": {"role": "assistant", "model": "claude-opus-4-5", "content": [
             {"type": "text", "text": "Switched the bucket key to the API key header."},
             {"type": "tool_use", "name": "Edit", "input": {}}]}},
        {"type": "user", "timestamp": iso(T0 + 600), "cwd": "/tmp/checkout-api",
         "message": {"role": "user", "content": "run the tests and confirm"}},
        {"type": "assistant", "timestamp": iso(T0 + 720),
         "message": {"role": "assistant", "model": "claude-opus-4-5", "content": [
             {"type": "text", "text": "All 34 tests pass, including two new throttle cases."},
             {"type": "tool_use", "name": "Bash", "input": {}}]}},
    ]
    write(home / ".claude" / "projects" / "-tmp-checkout-api"
          / "7c1de5f0-1111-4a2b-9c3d-000000000001.jsonl", jsonl(lines))


def make_codex(home):
    day = datetime.fromtimestamp(T0).strftime("%Y/%m/%d")
    sid = "7c1de5f0-2222-4a2b-9c3d-000000000002"
    lines = [
        {"timestamp": iso(T0), "type": "session_meta",
         "payload": {"id": sid, "timestamp": iso(T0), "cwd": "/tmp/etl-nightly"}},
        {"timestamp": iso(T0 + 2), "type": "turn_context",
         "payload": {"cwd": "/tmp/etl-nightly", "model": "gpt-5.5"}},
        {"timestamp": iso(T0 + 10), "type": "event_msg",
         "payload": {"type": "user_message",
                     "message": "The nightly ETL job takes 40 minutes. Find the bottleneck."}},
        {"timestamp": iso(T0 + 120), "type": "response_item",
         "payload": {"type": "function_call", "name": "shell"}},
        {"timestamp": iso(T0 + 240), "type": "event_msg",
         "payload": {"type": "agent_message",
                     "message": "The row-by-row upsert dominates; batching it cuts the run to 6 minutes."}},
        {"timestamp": iso(T0 + 480), "type": "event_msg",
         "payload": {"type": "user_message", "message": "apply the batching and rerun it"}},
        {"timestamp": iso(T0 + 660), "type": "event_msg",
         "payload": {"type": "agent_message", "message": "Batched and rerun: 5m52s end to end."}},
    ]
    write(home / ".codex" / "sessions" / Path(day) / f"rollout-{sid}.jsonl", jsonl(lines))


def make_opencode(home):
    storage = home / ".local" / "share" / "opencode" / "storage"
    sid = "ses_seed000000001"
    m1, m2, m3, m4 = "msg_s1", "msg_s2", "msg_s3", "msg_s4"
    write(storage / "session" / "global" / f"{sid}.json",
          {"id": sid, "projectID": "global", "directory": "/tmp/billing-web",
           "title": "Audit the config schema",
           "time": {"created": ms(T0), "updated": ms(T0 + 540)}})
    for mid, role, t in ((m1, "user", T0), (m2, "assistant", T0 + 150),
                         (m3, "user", T0 + 360), (m4, "assistant", T0 + 540)):
        msg = {"id": mid, "sessionID": sid, "role": role, "time": {"created": ms(t)}}
        if role == "assistant":
            msg.update({"modelID": "gpt-5.2", "providerID": "openai"})
        write(storage / "message" / sid / f"{mid}.json", msg)
    write(storage / "part" / m1 / "prt_1.json",
          {"id": "prt_1", "messageID": m1, "type": "text",
           "text": "/spec-lint check the billing config schema docs against the code"})
    write(storage / "part" / m2 / "prt_2.json",
          {"id": "prt_2", "messageID": m2, "type": "text",
           "text": "Three documented keys no longer exist in the loader."})
    write(storage / "part" / m2 / "prt_3.json",
          {"id": "prt_3", "messageID": m2, "type": "tool", "tool": "read"})
    write(storage / "part" / m3 / "prt_4.json",
          {"id": "prt_4", "messageID": m3, "type": "text",
           "text": "drop the dead keys from the docs and note the rename"})
    write(storage / "part" / m4 / "prt_5.json",
          {"id": "prt_5", "messageID": m4, "type": "text",
           "text": "Docs updated and the rename is noted in the changelog."})


def main():
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "home").expanduser().resolve()
    for fn in (make_claude_code, make_codex, make_opencode):
        fn(target)
    print(f"synthetic home written to {target}")
    print("tools: claude-code, codex, opencode | sessions: 3 | skill invocations: 2")


if __name__ == "__main__":
    main()
