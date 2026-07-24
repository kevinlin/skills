#!/usr/bin/env python3
"""Generate synthetic session fixtures for every supported tool, shaped as a fake HOME.

Usage: python3 make_fixtures.py [target_dir]   (default: tests/fixtures)
Then:  agent_insights.py scan --home <target_dir> --days 30 --data-dir /tmp/ai-fixture-test

Timestamps are stamped relative to now so the fixtures always fall inside the window.
"""

import json
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

NOW = time.time()
T0 = NOW - 3600  # one hour ago


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


def tc_string(s):
    """Java-serialization TC_STRING wire encoding (0x74 + u2 length + utf8 bytes)."""
    b = s.encode("utf-8")
    return b"\x74" + len(b).to_bytes(2, "big") + b


def write_nitrite_db(path, tokens):
    """Copilot-for-JetBrains Nitrite fixture: MVStore header + TC_STRING tokens
    interleaved with 0x80 separators (record tags the parser breaks on)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"H:2,block:7,blockSize:1000\x00"
                     + b"\x80".join(tc_string(t) for t in tokens))


def make_claude_code(home):
    lines = [
        {"type": "user", "timestamp": iso(T0), "cwd": "/tmp/proj-alpha",
         "message": {"role": "user", "content": "Please add input validation to the signup form"}},
        {"type": "assistant", "timestamp": iso(T0 + 60),
         "message": {"role": "assistant", "model": "claude-opus-4-5", "content": [
             {"type": "text", "text": "I'll add validation now."},
             {"type": "tool_use", "name": "Skill", "input": {"skill": "research-plan-implement"}},
             {"type": "tool_use", "name": "Edit", "input": {}}]}},
        {"type": "user", "timestamp": iso(T0 + 180), "cwd": "/tmp/proj-alpha",
         "message": {"role": "user", "content": "thanks, looks good. now add tests please"}},
        {"type": "assistant", "timestamp": iso(T0 + 240),
         "message": {"role": "assistant", "model": "claude-opus-4-5", "content": [
             {"type": "text", "text": "Tests added and passing."},
             {"type": "tool_use", "name": "Write", "input": {}}]}},
        {"type": "user", "timestamp": iso(T0 + 200), "isMeta": True,
         "message": {"role": "user", "content": "meta line, must be ignored"}},
    ]
    write(home / ".claude" / "projects" / "-tmp-proj-alpha" / "11111111-aaaa-bbbb-cccc-000000000001.jsonl",
          jsonl(lines))


def make_claude_cowork(home):
    """Claude desktop Cowork: metadata JSON + Claude Code-format JSONL transcript
    in the session's sandbox dir."""
    sid = "local_99999999-aaaa-bbbb-cccc-000000000009"
    ws = (home / "Library" / "Application Support" / "Claude" / "local-agent-mode-sessions"
          / "fixture-account" / "fixture-workspace")
    write(ws / f"{sid}.json",
          {"sessionId": sid, "processName": "fixture-process", "cliSessionId": "cli-fixture-0009",
           "cwd": "/tmp/cowork-sandbox/outputs", "createdAt": ms(T0), "lastActivityAt": ms(T0 + 240),
           "model": "claude-opus-4-8[1m]", "isArchived": False, "title": "Draft release notes"})
    lines = [
        {"type": "queue-operation", "operation": "enqueue", "sessionId": "cli-fixture-0009",
         "timestamp": iso(T0)},
        {"type": "user", "timestamp": iso(T0 + 2), "cwd": "/tmp/cowork-sandbox/outputs",
         "message": {"role": "user", "content": "Draft release notes for v2.3 from the merged PRs"}},
        {"type": "assistant", "timestamp": iso(T0 + 60),
         "message": {"role": "assistant", "model": "claude-opus-4-8", "content": [
             {"type": "text", "text": "Drafted release notes covering 12 PRs."},
             {"type": "tool_use", "name": "Skill", "input": {"skill": "spec-coding"}},
             {"type": "tool_use", "name": "Write", "input": {}}]}},
        {"type": "user", "timestamp": iso(T0 + 180), "cwd": "/tmp/cowork-sandbox/outputs",
         "message": {"role": "user", "content": "group the fixes by area and add upgrade notes"}},
        {"type": "assistant", "timestamp": iso(T0 + 240),
         "message": {"role": "assistant", "model": "claude-opus-4-8", "content": [
             {"type": "text", "text": "Grouped by area and added an upgrade notes section."},
             {"type": "tool_use", "name": "Edit", "input": {}}]}},
    ]
    write(ws / sid / ".claude" / "projects" / "-tmp-cowork-sandbox-outputs" / "cli-fixture-0009.jsonl",
          jsonl(lines))


def make_copilot_vscode(home):
    ws = home / "Library" / "Application Support" / "Code" / "User" / "workspaceStorage" / "fixturehash"
    write(ws / "workspace.json", {"folder": "file:///tmp/proj-beta"})
    # old plain-JSON snapshot format
    state = {
        "version": 3, "sessionId": "22222222-aaaa-bbbb-cccc-000000000002",
        "creationDate": str(ms(T0)),
        "requests": [
            {"timestamp": ms(T0), "modelId": "copilot/claude-sonnet-4.5",
             "message": {"text": "Refactor the date utils into a single module"},
             "response": [{"value": "Refactored into utils/date.ts."},
                          {"kind": "toolInvocationSerialized", "toolId": "editFile"}],
             "result": {"timings": {"totalElapsed": 45000}}},
            {"timestamp": ms(T0 + 300), "modelId": "copilot/claude-sonnet-4.5",
             "message": {"text": "great, also update the imports"},
             "response": [{"value": "Imports updated across 4 files."}],
             "result": {"timings": {"totalElapsed": 30000}}},
        ],
    }
    write(ws / "chatSessions" / "22222222-aaaa-bbbb-cccc-000000000002.json", state)
    # newer JSONL update-log format (kind 0 snapshot, kind 2 appends, kind 1 sets)
    log = [
        {"kind": 0, "v": {"version": 3, "sessionId": "33333333-aaaa-bbbb-cccc-000000000003",
                          "creationDate": str(ms(T0)), "requests": []}},
        {"kind": 2, "k": ["requests"],
         "v": [{"timestamp": ms(T0), "modelId": "copilot/gpt-5",
                "message": {"text": "Fix the failing pipeline on main"}}]},
        {"kind": 2, "k": ["requests", 0, "response"],
         "v": [{"kind": "toolInvocationSerialized", "toolId": "runInTerminal"},
               {"value": "The lint step was failing; fixed the config."}]},
        {"kind": 1, "k": ["requests", 0, "result"], "v": {"timings": {"totalElapsed": 60000}}},
        {"kind": 2, "k": ["requests"],
         "v": [{"timestamp": ms(T0 + 240), "modelId": "copilot/gpt-5",
                "message": {"text": "ok now rerun it to confirm"}}]},
        {"kind": 2, "k": ["requests", 1, "response"], "v": [{"value": "Pipeline is green."}]},
    ]
    write(ws / "chatSessions" / "33333333-aaaa-bbbb-cccc-000000000003.jsonl", jsonl(log))


def make_copilot_cli(home):
    write(home / ".copilot" / "history-session-state" / "fixture-session" / "state.json",
          {"sessionId": "fixture-session", "messages": [
              {"role": "user", "content": "Summarize the open TODOs in this repo", "timestamp": ms(T0)},
              {"role": "assistant", "content": "There are 7 TODOs across 3 files.",
               "timestamp": ms(T0 + 90), "model": "gpt-5"},
              {"role": "user", "content": "turn the auth ones into GitHub issues", "timestamp": ms(T0 + 150)},
              {"role": "assistant", "content": "Created 2 issues.", "timestamp": ms(T0 + 200)},
          ]})


def make_copilot_cli_store(home):
    """Newer Copilot CLI builds (also embedded by the JetBrains plugin) replaced
    history-session-state/ JSON with `~/.copilot/session-state/<conversationId>/
    events.jsonl` (rich event log) plus a shared `~/.copilot/session-store.db` SQLite
    (`sessions` + `turns`). Three sessions here: one claimed by a JetBrains IDE via
    the nitrite metadata's conversationId (-> copilot-jetbrains), one standalone
    (-> copilot-cli), one present only in the store db (fallback path, no events.jsonl)."""
    def events(sid, cwd, prompt, answer, model, tool, skill=None):
        rows = [
            {"type": "session.start", "timestamp": iso(T0),
             "data": {"sessionId": sid, "selectedModel": model,
                      "context": {"cwd": cwd, "gitRoot": cwd, "branch": "main"}}},
            {"type": "user.message", "timestamp": iso(T0 + 5),
             "data": {"content": prompt, "transformedContent": f"<current_datetime>x</current_datetime>\n\n{prompt}"}},
            # injected context rides in as its own user.message; `<`-leading -> not a prompt
            {"type": "user.message", "timestamp": iso(T0 + 6),
             "data": {"content": "<skill-context name=\"x\">wrapper</skill-context>"}},
            {"type": "assistant.message", "timestamp": iso(T0 + 30),
             "data": {"model": model, "content": "",
                      "toolRequests": [{"name": tool, "arguments": {}}]}},
            {"type": "tool.execution_start", "timestamp": iso(T0 + 35),
             "data": {"toolName": tool, "arguments": {}, "model": model}},
            {"type": "assistant.message", "timestamp": iso(T0 + 120),
             "data": {"model": model, "content": answer, "toolRequests": []}},
        ]
        if skill:  # parser dispatches on event type; row position is irrelevant
            rows.append({"type": "skill.invoked", "timestamp": iso(T0 + 33),
                         "data": {"name": skill, "path": f"/tmp/skills/{skill}/SKILL.md"}})
        write(home / ".copilot" / "session-state" / sid / "events.jsonl", jsonl(rows))

    # claimed by the JetBrains fixture below -> attributed copilot-jetbrains
    events("88888888-aaaa-bbbb-cccc-0000000000a1", "/tmp/proj-jetbrains-agent",
           "Profile the slow integration test suite", "Slowest test is test_sync; 41s in setup.",
           "claude-sonnet-5", "bash", skill="agent-insights")
    # standalone CLI session -> stays copilot-cli
    events("88888888-aaaa-bbbb-cccc-0000000000b2", "/tmp/proj-cli-new",
           "List the failing CI jobs", "Two jobs failing: lint and e2e.",
           "gpt-5", "view")

    db = home / ".copilot" / "session-store.db"
    db.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE sessions (id TEXT PRIMARY KEY, cwd TEXT, repository TEXT,"
                " host_type TEXT, branch TEXT, summary TEXT, created_at TEXT, updated_at TEXT)")
    con.execute("CREATE TABLE turns (id INTEGER PRIMARY KEY, session_id TEXT, turn_index INT,"
                " user_message TEXT, assistant_response TEXT, timestamp TEXT)")
    # store rows for the two events.jsonl sessions (dedup keeps the richer events variant)
    for sid, cwd, summ in [
        ("88888888-aaaa-bbbb-cccc-0000000000a1", "/tmp/proj-jetbrains-agent", "Profile the slow integration test suite"),
        ("88888888-aaaa-bbbb-cccc-0000000000b2", "/tmp/proj-cli-new", "List the failing CI jobs"),
    ]:
        con.execute("INSERT INTO sessions VALUES (?,?,NULL,NULL,'main',?,?,?)",
                    (sid, cwd, summ, iso(T0), iso(T0 + 120)))
    # store-only session: its session-state dir is gone, only the shared db remembers it
    con.execute("INSERT INTO sessions VALUES (?,?,NULL,NULL,'main',?,?,?)",
                ("88888888-aaaa-bbbb-cccc-0000000000c3", "/tmp/proj-cli-old-turns",
                 "Rename the config module", iso(T0), iso(T0 + 200)))
    con.execute("INSERT INTO turns VALUES (NULL,?,0,?,?,?)",
                ("88888888-aaaa-bbbb-cccc-0000000000c3", "Rename the config module", None, iso(T0)))
    con.execute("INSERT INTO turns VALUES (NULL,?,1,?,?,?)",
                ("88888888-aaaa-bbbb-cccc-0000000000c3",
                 "<skill-context name=\"y\">wrapper</skill-context>",
                 "Renamed config to settings across 6 files.", iso(T0 + 200)))
    con.commit()
    con.close()


def make_copilot_jetbrains_agent_meta(home):
    """Newer Copilot-for-JetBrains plugin builds delegate agent chat to the embedded
    Copilot CLI: the per-project Nitrite DB keeps only NtAgentSession *metadata* — the
    session title (`name`/`value`), the `modelName`, and the `conversationId` linking to
    the CLI's session-state store where the turns actually live. No `query`/`response`
    markers, no message text. This fixture emits that metadata-only wire shape."""
    tokens = [
        "$nitrite_store_info", "MVStore/2.2.224",
        "com.github.copilot.agent.session.persistence.nitrite.entity.NtAgentSession",
        "name", "value", "Profile the slow integration test suite", "source", "copilot",
        "conversationId", "88888888-aaaa-bbbb-cccc-0000000000a1",
        "schemaVersion", "createdAt", str(ms(T0)), "activeAt", str(ms(T0 + 120)),
        "input", "turns", "workingSet", "isArchived", "chatType", "PANEL",
        "modelName", "claude-sonnet-5", "modelProvider", "modelIdType", "status",
    ]
    write_nitrite_db(home / ".config" / "github-copilot" / "ws" / "chat-agent-sessions"
                     / "3AAAgentSessionDirKsuid000000" / "copilot-agent-sessions-nitrite.db",
                     tokens)


def make_cursor(home):
    db = home / "Library" / "Application Support" / "Cursor" / "User" / "globalStorage" / "state.vscdb"
    db.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE IF NOT EXISTS cursorDiskKV (key TEXT PRIMARY KEY, value BLOB)")
    cid = "44444444-aaaa-bbbb-cccc-000000000004"
    headers = [{"bubbleId": f"b{i}", "type": t} for i, t in enumerate([1, 2, 1, 2])]
    composer = {"composerId": cid, "createdAt": ms(T0), "lastUpdatedAt": ms(T0 + 600),
                "name": "Fix login redirect", "fullConversationHeadersOnly": headers,
                "modelConfig": {"modelName": "composer-2.5-fast", "maxMode": False}}
    bubbles = {
        "b0": {"type": 1, "text": "/spec-lint The login page redirects to / instead of /dashboard, fix it"},
        "b1": {"type": 2, "text": "Found it: the callback ignores the next param.",
               "toolFormerData": {"name": "read_file"}},
        "b2": {"type": 1, "text": "works now, thanks!"},
        "b3": {"type": 2, "text": "Great, the next param is honored now."},
    }
    rows = [(f"composerData:{cid}", json.dumps(composer))]
    rows += [(f"bubbleId:{cid}:{b}", json.dumps(v)) for b, v in bubbles.items()]
    con.executemany("INSERT OR REPLACE INTO cursorDiskKV VALUES (?, ?)", rows)
    con.commit()
    con.close()


def make_codex(home):
    day = datetime.fromtimestamp(T0).strftime("%Y/%m/%d")
    lines = [
        {"timestamp": iso(T0), "type": "session_meta",
         "payload": {"id": "55555555-aaaa-bbbb-cccc-000000000005", "timestamp": iso(T0),
                     "cwd": "/tmp/proj-gamma"}},
        {"timestamp": iso(T0 + 1), "type": "turn_context",
         "payload": {"cwd": "/tmp/proj-gamma", "model": "gpt-5.5"}},
        {"timestamp": iso(T0 + 5), "type": "event_msg",
         "payload": {"type": "user_message", "message": "Profile this script and make it faster"}},
        {"timestamp": iso(T0 + 60), "type": "response_item",
         "payload": {"type": "function_call", "name": "shell"}},
        {"timestamp": iso(T0 + 120), "type": "event_msg",
         "payload": {"type": "agent_message", "message": "Main cost is the O(n^2) join; switched to a dict lookup."}},
        {"timestamp": iso(T0 + 200), "type": "event_msg",
         "payload": {"type": "user_message", "message": "nice, 10x faster. commit it"}},
        {"timestamp": iso(T0 + 260), "type": "event_msg",
         "payload": {"type": "agent_message", "message": "Committed."}},
    ]
    write(home / ".codex" / "sessions" / Path(day) /
          "rollout-fixture-55555555-aaaa-bbbb-cccc-000000000005.jsonl", jsonl(lines))


def make_kiro(home):
    db = home / "Library" / "Application Support" / "Kiro" / "User" / "workspaceStorage" / "fixturews" / "state.vscdb"
    db.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE IF NOT EXISTS ItemTable (key TEXT PRIMARY KEY, value BLOB)")
    chat = {"messages": [
        {"role": "user", "content": "Generate a spec for the export feature", "timestamp": ms(T0)},
        {"role": "assistant", "content": "Spec drafted with 4 requirements.", "timestamp": ms(T0 + 100),
         "model": "claude-sonnet-4.5"},
        {"role": "user", "content": "add an acceptance criterion for CSV size limits", "timestamp": ms(T0 + 200)},
        {"role": "assistant", "content": "Added.", "timestamp": ms(T0 + 260), "model": "claude-sonnet-4.5"},
    ]}
    con.execute("INSERT OR REPLACE INTO ItemTable VALUES (?, ?)", ("kiro.kiroAgent", json.dumps(chat)))
    con.commit()
    con.close()


def make_opencode(home):
    storage = home / ".local" / "share" / "opencode" / "storage"
    sid, m1, m2, m3 = "ses_fixture000001", "msg_f1", "msg_f2", "msg_f3"
    write(storage / "session" / "global" / f"{sid}.json",
          {"id": sid, "projectID": "global", "directory": "/tmp/proj-delta",
           "title": "Rename config keys", "time": {"created": ms(T0), "updated": ms(T0 + 400)}})
    for mid, role, t in ((m1, "user", T0), (m2, "assistant", T0 + 120), (m3, "user", T0 + 300)):
        msg = {"id": mid, "sessionID": sid, "role": role, "time": {"created": ms(t)}}
        if role == "assistant":
            msg.update({"modelID": "gpt-5.2", "providerID": "openai"})
        write(storage / "message" / sid / f"{mid}.json", msg)
    write(storage / "part" / m1 / "prt_1.json",
          {"id": "prt_1", "messageID": m1, "type": "text", "text": "/spec-coding Rename all SNAKE_CASE config keys to camelCase"})
    write(storage / "part" / m2 / "prt_2.json",
          {"id": "prt_2", "messageID": m2, "type": "text", "text": "Renamed 23 keys and updated readers."})
    write(storage / "part" / m2 / "prt_3.json",
          {"id": "prt_3", "messageID": m2, "type": "tool", "tool": "edit"})
    write(storage / "part" / m3 / "prt_4.json",
          {"id": "prt_4", "messageID": m3, "type": "text", "text": "perfect, that works"})


def make_antigravity(home):
    """Antigravity stores per-session step logs as JSONL under
    brain/<sid>/.system_generated/logs/. Models surface via a <USER_SETTINGS_CHANGE>
    model switch and an error-message machine id; tool calls live in PLANNER_RESPONSE."""
    sid = "477a9734-aaaa-bbbb-cccc-000000000077"
    logs = home / ".gemini" / "antigravity" / "brain" / sid / ".system_generated" / "logs"
    lines = [
        {"step_index": 1, "source": "USER_EXPLICIT", "type": "USER_INPUT", "status": "DONE",
         "created_at": iso(T0),
         "content": ("<USER_REQUEST>\nAdd retry logic to the API client\n</USER_REQUEST>\n"
                     "<USER_SETTINGS_CHANGE>\nThe user changed setting `Model Selection` from "
                     "Claude Sonnet 4.6 (Thinking) to Gemini 3.1 Pro (Low). No need to comment.\n"
                     "</USER_SETTINGS_CHANGE>")},
        {"step_index": 2, "source": "SYSTEM", "type": "EPHEMERAL_MESSAGE", "status": "DONE",
         "created_at": iso(T0 + 1), "content": "<EPHEMERAL_MESSAGE>reminder, ignore</EPHEMERAL_MESSAGE>"},
        {"step_index": 3, "source": "MODEL", "type": "PLANNER_RESPONSE", "status": "DONE",
         "created_at": iso(T0 + 30), "thinking": "Locate the client.",
         "tool_calls": [{"name": "view_file", "args": {"AbsolutePath": "\"/tmp/proj-epsilon/api/client.py\""}}]},
        {"step_index": 4, "source": "MODEL", "type": "VIEW_FILE", "status": "DONE",
         "created_at": iso(T0 + 31), "content": "file contents (a tool result, must not be counted)"},
        {"step_index": 5, "source": "MODEL", "type": "PLANNER_RESPONSE", "status": "DONE",
         "created_at": iso(T0 + 90), "content": "Added exponential backoff with 3 retries.",
         "tool_calls": [{"name": "edit_file", "args": {"AbsolutePath": "\"/tmp/proj-epsilon/api/client.py\""}}]},
        {"step_index": 6, "source": "USER_EXPLICIT", "type": "USER_INPUT", "status": "DONE",
         "created_at": iso(T0 + 200),
         "content": "<USER_REQUEST>\nnow add a unit test for the retry path\n</USER_REQUEST>"},
        {"step_index": 7, "source": "MODEL", "type": "PLANNER_RESPONSE", "status": "DONE",
         "created_at": iso(T0 + 260), "content": "Test added and passing.",
         "tool_calls": [{"name": "edit_file", "args": {"AbsolutePath": "\"/tmp/proj-epsilon/tests/test_client.py\""}}]},
    ]
    write(logs / "transcript_full.jsonl", jsonl(lines))


def make_copilot_jetbrains(home):
    """GitHub Copilot for JetBrains stores chat under ~/.config/github-copilot/<product>/
    chat-sessions/<id>/00000000000.xd — a binary Xodus log. The real format is Java-
    serialized; the adapter only string-scans it and rebuilds turns from the `query`
    (user) / `response` (assistant) markers. This fixture emits a minimal byte stream
    with the same markers, separated by the control byte Xodus uses between records,
    plus file:// references the adapter folds into a project name."""
    tokens = [
        "XdChatSession", "projectName", "New Conversation",
        "66666666-aaaa-bbbb-cccc-000000000066", "copilot", "kevinlin",
        "file:///tmp/proj-jetbrains/src/Main.kt",
        "file:///tmp/proj-jetbrains/build.gradle.kts",
        "kevinlin", "query", "Add a JetBrains run configuration for the test suite",
        "GitHub Copilot", "response", "Added a run configuration named \"All Tests\".",
        "query", "also wire it into the gradle check task",
        "response", "Wired the test task into the gradle build.",
    ]
    blob = b"\x01".join(t.encode("utf-8") for t in tokens)
    xd = (home / ".config" / "github-copilot" / "ws" / "chat-sessions"
          / "66666666-aaaa-bbbb-cccc-000000000066" / "00000000000.xd")
    xd.parent.mkdir(parents=True, exist_ok=True)
    xd.write_bytes(blob)


def make_copilot_jetbrains_nitrite(home):
    """Newer Copilot-for-JetBrains chat/agent/edit sessions persist turns in a sibling
    Nitrite DB (`copilot-*-nitrite.db`, H2 MVStore + Java serialization) instead of the
    Xodus `.xd`. The adapter recovers the message text from the Java-serialized UTF strings
    (TC_STRING `0x74` + u2 length). This fixture emits exactly that wire shape — the
    `query`/`response` field markers, status/author tokens, decimal `created_at` epoch-ms
    timestamps, the `model`,<value>,`modelProviderName` triple, and file:// references —
    interleaved with `0x80` separators (Xodus/MVStore record tags the parser breaks on)."""
    tokens = [
        "$nitrite_store_info", "MVStore/2.2.224",
        "com.github.copilot.chat.session.persistence.nitrite.entity.NtChatSession",
        "created_at", str(ms(T0)), "uuid",
        "com.github.copilot.chat.session.persistence.nitrite.entity.NtTurn",
        "file:///tmp/proj-jetbrains-nitrite/src/App.java",
        "file:///tmp/proj-jetbrains-nitrite/pom.xml",
        # turn 1 (chat shape: query, status, user-text, references)
        "query", "ok", "Generate a REST controller for the Order entity",
        "references", "model", "auto", "modelProviderName",
        "response", "GitHub Copilot", "Here is an OrderController with CRUD endpoints.",
        "created_at", str(ms(T0 + 100)),
        # turn 2
        "query", "ok", "now add pagination to the list endpoint",
        "references",
        "response", "GitHub Copilot", "Added Pageable support to the list endpoint.",
        "created_at", str(ms(T0 + 200)),
    ]
    write_nitrite_db(home / ".config" / "github-copilot" / "iu" / "chat-sessions"
                     / "77777777-aaaa-bbbb-cccc-000000000077" / "copilot-chat-nitrite.db",
                     tokens)


def make_sandbox(home):
    """A Claude Cowork-style sandbox HOME: an ephemeral per-session user whose home sits
    under a `sessions` volume, with read-only bindfs `mnt/.skills`. Used to exercise
    `detect --home` for the sandboxed-runtime path. The real Cowork sandbox also carries
    the global @anthropic-ai/sandbox-runtime module and a bwrap PID 1, which can't be
    faked via --home; the home layout + bindfs mount together are a strong (high-confidence) hit."""
    sandbox = home / "sandbox-home" / "sessions" / "eloquent-eager-gauss"
    write(sandbox / "mnt" / ".skills" / "docx" / "SKILL.md", "# docx skill (read-only mount)\n")
    # the sandbox's own Claude Code session (the only log reachable from inside)
    write(sandbox / ".claude" / "projects" / "-sessions-eloquent-eager-gauss" / "sandbox-sess.jsonl",
          jsonl([{"type": "user", "timestamp": iso(T0),
                  "message": {"role": "user", "content": "analyze my agent usage"}}]))


def main():
    target = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent / "fixtures")
    for fn in (make_claude_code, make_claude_cowork, make_copilot_vscode, make_copilot_cli,
               make_copilot_cli_store, make_copilot_jetbrains, make_copilot_jetbrains_nitrite,
               make_copilot_jetbrains_agent_meta, make_cursor, make_codex,
               make_kiro, make_opencode, make_antigravity, make_sandbox):
        fn(target)
    print(f"fixtures written to {target}")
    print(f"sandbox home: {target / 'sandbox-home' / 'sessions' / 'eloquent-eager-gauss'}")


if __name__ == "__main__":
    main()
