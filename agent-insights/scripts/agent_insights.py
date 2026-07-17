#!/usr/bin/env python3
"""agent-insights: scan local AI-agent session logs, aggregate stats, render an HTML report.

Subcommands:
  detect    [--home DIR]                               detect host vs sandboxed runtime (Cowork etc.)
  scan      --days N [--home DIR] [--data-dir DIR]   discover + normalize sessions, prepare facet batches
  aggregate --days N [--data-dir DIR]                 ingest facet batches, merge meta+facets -> aggregate.json
  render    [--data-dir DIR]                          aggregate.json + narrative.json -> report HTML

Python 3 stdlib only. All data stays local.
"""

import argparse
import glob
import json
import os
import platform
import re
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# --- constants ----------------------------------------------------------------

USER_TRUNC = 500
ASSIST_TRUNC = 300
MAX_FACET_EXTRACTIONS = 50
BATCH_SIZE = 10
MIN_USER_MSGS = 1
MIN_DURATION_MIN = 1.0
# Canonical low->high order for the user-expertise facet (see references/expertise-classifier-prompt.md).
EXPERTISE_LEVELS = ["1_novice", "2_beginner", "3_intermediate", "4_advanced", "5_expert"]
# Sessions whose transcripts contain these markers are insight-analysis sessions
# (this skill's own runs, or Claude Code's builtin /insights) — exclude them.
SELF_MARKERS = (
    "RESPOND WITH ONLY A VALID JSON OBJECT",
    "agent-insights facet extraction",
)

DEFAULT_DATA_DIR = Path("~/.agent-insights").expanduser()


# --- small helpers --------------------------------------------------------------


def epoch_from_iso(s):
    """ISO-8601 string -> epoch seconds, or None."""
    if not s or not isinstance(s, str):
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def epoch_from_ms(v):
    """Millisecond int/str -> epoch seconds, or None."""
    try:
        n = float(v)
    except (TypeError, ValueError):
        return None
    if n > 1e12:  # milliseconds
        n /= 1000.0
    return n if n > 1e9 else None


def fmt_date(epoch):
    if not epoch:
        return "unknown"
    return datetime.fromtimestamp(epoch).strftime("%Y-%m-%d %H:%M")


def resolve_analysis_model(arg):
    """Model id of the main agent running this skill (the one doing facet/narrative work).
    Recorded so reports can be benchmarked against an agreed standard model. Resolution
    order: explicit --analysis-model arg, then AGENT_INSIGHTS_MODEL env, else 'unknown'."""
    model = (arg or os.environ.get("AGENT_INSIGHTS_MODEL") or "").strip()
    return model or "unknown"


def skill_version():
    """Read metadata.version from SKILL.md frontmatter (single source of truth).
    Used to stamp output filenames so reports are traceable to the skill release
    that produced them. Falls back to 'unknown' if SKILL.md is missing/unreadable."""
    skill_md = Path(__file__).resolve().parent.parent / "SKILL.md"
    try:
        text = skill_md.read_text(encoding="utf-8")
    except OSError:
        return "unknown"
    m = re.search(r"^\s*version:\s*(\S+)", text, re.MULTILINE)
    return m.group(1).strip() if m else "unknown"


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def save_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)


def iter_jsonl(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue  # skip malformed line
    except OSError:
        return


def open_sqlite_ro(db_path):
    """Open SQLite read-only; on lock/error, copy db (+wal/shm) to temp and open the copy."""
    try:
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        con.execute("SELECT 1")
        return con, None
    except sqlite3.Error:
        pass
    tmpdir = tempfile.mkdtemp(prefix="agent-insights-db-")
    dst = os.path.join(tmpdir, os.path.basename(db_path))
    try:
        shutil.copy2(db_path, dst)
        for suffix in ("-wal", "-shm"):
            side = str(db_path) + suffix
            if os.path.exists(side):
                shutil.copy2(side, dst + suffix)
        con = sqlite3.connect(f"file:{dst}?mode=ro", uri=True)
        con.execute("SELECT 1")
        return con, tmpdir
    except (sqlite3.Error, OSError):
        shutil.rmtree(tmpdir, ignore_errors=True)
        return None, None


class TranscriptBuilder:
    """Normalized transcript with /insights-style truncation."""

    def __init__(self):
        self.lines = []

    def user(self, text):
        text = (text or "").strip()
        if text:
            self.lines.append("[User]: " + text[:USER_TRUNC])

    def assistant(self, text):
        text = (text or "").strip()
        if text:
            self.lines.append("[Assistant]: " + text[:ASSIST_TRUNC])

    def tool(self, name):
        if name:
            self.lines.append(f"[Tool: {name}]")

    def text(self):
        return "\n".join(self.lines)


def active_minutes(timestamps, gap_cap=1800):
    """Active time: sum of inter-message gaps, each capped at 30 min.
    Avoids counting idle days in long-lived resumed sessions."""
    ts = sorted(t for t in timestamps if t)
    if len(ts) < 2:
        return None
    return round(sum(min(b - a, gap_cap) for a, b in zip(ts, ts[1:])) / 60.0, 1)


def make_meta(tool, session_id, project, start, end, user_n, assistant_n, tool_calls, transcript,
              timestamps=None, models=None):
    duration = active_minutes(timestamps or [])
    if duration is None and start and end and end >= start:
        # no per-message timestamps: wall-clock span, capped at 8h to avoid idle inflation
        duration = round(min(end - start, 8 * 3600) / 60.0, 1)
    return {
        "tool": tool,
        "session_id": session_id,
        "project": project or "",
        "start_ts": start,
        "end_ts": end,
        "duration_minutes": duration,
        "user_msg_count": user_n,
        "assistant_msg_count": assistant_n,
        "tool_calls": tool_calls,
        "models": models or {},
        "transcript": transcript,
    }


def count_model(models, name):
    """Record one use of a model in a per-session model->count dict."""
    if isinstance(name, str) and name and not name.startswith("<"):  # skip "<synthetic>"
        models[name] = models.get(name, 0) + 1


def recent_files(pattern, since):
    """Glob, keep files modified after `since`, oldest-first."""
    out = [p for p in glob.glob(pattern, recursive=True) if os.path.getmtime(p) >= since]
    return sorted(out, key=os.path.getmtime)


# --- adapters -------------------------------------------------------------------
# Each adapter: (home: Path, since: epoch) -> list[SessionMeta]
# Missing roots -> return []. Parse errors -> skip item, keep going.


def _parse_claude_jsonl(path, tb, tool_calls, models, ts_list):
    """Parse one Claude Code-format JSONL transcript (used by Claude Code and Claude
    Cowork). Accumulates into tb/tool_calls/models/ts_list; returns
    (user_n, assistant_n, start, end, cwd)."""
    user_n = assistant_n = 0
    start = end = None
    cwd = None
    for o in iter_jsonl(path):
        if o.get("isSidechain") is True or o.get("isMeta") is True:
            continue
        t = o.get("type")
        if t not in ("user", "assistant"):
            continue
        ts = epoch_from_iso(o.get("timestamp"))
        if ts:
            start = start or ts
            end = ts
            ts_list.append(ts)
        cwd = cwd or o.get("cwd")
        msg = o.get("message") or {}
        content = msg.get("content")
        if t == "user":
            text = content if isinstance(content, str) else " ".join(
                b.get("text", "") for b in content or [] if isinstance(b, dict) and b.get("type") == "text"
            )
            text = (text or "").strip()
            # skip harness-injected command/caveat wrappers, count real prompts only
            if not text or text.startswith("<"):
                continue
            user_n += 1
            tb.user(text)
        else:
            count_model(models, msg.get("model"))
            texts = []
            for b in content or [] if isinstance(content, list) else []:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "text":
                    texts.append(b.get("text", ""))
                elif b.get("type") == "tool_use":
                    name = b.get("name", "?")
                    tool_calls[name] = tool_calls.get(name, 0) + 1
                    tb.tool(name)
            if texts:
                assistant_n += 1
                tb.assistant(" ".join(texts))
    return user_n, assistant_n, start, end, cwd


def scan_claude_code(home, since):
    sessions = []
    root = home / ".claude" / "projects"
    if not root.is_dir():
        return sessions
    for path in recent_files(str(root / "*" / "*.jsonl"), since):
        tb = TranscriptBuilder()
        tool_calls, models, ts_list = {}, {}, []
        user_n, assistant_n, start, end, cwd = _parse_claude_jsonl(path, tb, tool_calls, models, ts_list)
        sessions.append(make_meta(
            "claude-code", Path(path).stem, cwd, start, end, user_n, assistant_n, tool_calls, tb.text(),
            timestamps=ts_list, models=models))
    return sessions


def _claude_cowork_roots(home):
    """Claude desktop Cowork (local agent mode) session roots across platforms."""
    roots = [base / "Claude" / "local-agent-mode-sessions" for base in _app_data_bases(home)]
    # Microsoft Store build keeps Roaming data inside the package LocalCache
    pkg = (Path("Packages") / "Claude_pzs8sxrjxfjjc" / "LocalCache" / "Roaming"
           / "Claude" / "local-agent-mode-sessions")
    roots.append(home / "AppData" / "Local" / pkg)
    if home == Path.home():
        localappdata = os.environ.get("LOCALAPPDATA")
        if localappdata:
            roots.append(Path(localappdata) / pkg)
    out = []
    for r in roots:
        if r not in out and r.is_dir():
            out.append(r)
    return out


def scan_claude_cowork(home, since):
    """Claude Cowork: per session a `local_<id>.json` metadata file (model, title,
    createdAt/lastActivityAt ms) plus a sibling `local_<id>/` sandbox dir holding a
    Claude Code-format JSONL transcript under `.claude/projects/`."""
    sessions = []
    for root in _claude_cowork_roots(home):
        # layout: <root>/<account-id>/<workspace-id>/local_<session-id>.json
        for mpath in recent_files(str(root / "*" / "*" / "local_*.json"), since):
            meta = load_json(mpath)
            if not isinstance(meta, dict):
                continue
            sid = meta.get("sessionId") or Path(mpath).stem
            created = epoch_from_ms(meta.get("createdAt"))
            updated = epoch_from_ms(meta.get("lastActivityAt")) or created
            tb = TranscriptBuilder()
            tool_calls, models, ts_list = {}, {}, []
            user_n = assistant_n = 0
            start = end = None
            session_dir = Path(mpath).with_suffix("")
            for tpath in sorted(glob.glob(str(session_dir / ".claude" / "projects" / "*" / "*.jsonl")),
                                key=os.path.getmtime):
                u, a, s, e, _cwd = _parse_claude_jsonl(tpath, tb, tool_calls, models, ts_list)
                user_n += u
                assistant_n += a
                if s:
                    start = min(start, s) if start else s
                if e:
                    end = max(end, e) if end else e
            if not models:
                # no transcript model info: fall back to the session's configured model,
                # minus context-size suffixes like "[1m]"
                count_model(models, re.sub(r"\[[^\]]*\]$", "", str(meta.get("model") or "")))
            sessions.append(make_meta(
                "claude-cowork", sid, str(meta.get("title") or ""),
                start or created, end or updated, user_n, assistant_n, tool_calls, tb.text(),
                timestamps=ts_list, models=models))
    return sessions


def _app_data_bases(home):
    """Per-OS application-data bases for VS Code-family apps (macOS/Linux/Windows).
    %APPDATA% can be relocated on Windows, so the env var is honored too — but only
    when scanning the real home, keeping fixture runs (--home) deterministic."""
    bases = [
        home / "Library" / "Application Support",  # macOS
        home / ".config",                          # Linux
        home / "AppData" / "Roaming",              # Windows default
    ]
    appdata = os.environ.get("APPDATA")
    if appdata and home == Path.home():
        bases.append(Path(appdata))
    out = []
    for b in bases:
        if b not in out:
            out.append(b)
    return out


def _vscode_chat_roots(home, app_dirs):
    """workspaceStorage roots across macOS/Linux/Windows for VS Code-family apps."""
    roots = [base / app / "User" / "workspaceStorage"
             for app in app_dirs for base in _app_data_bases(home)]
    return [r for r in roots if r.is_dir()]


def _walk_to_parent(state, path):
    cur = state
    for i, key in enumerate(path[:-1]):
        nxt_key = path[i + 1]
        if isinstance(cur, list):
            if not isinstance(key, int) or key > len(cur):
                return None
            if key == len(cur):
                cur.append([] if isinstance(nxt_key, int) else {})
            cur = cur[key]
        elif isinstance(cur, dict):
            if key not in cur or not isinstance(cur[key], (dict, list)):
                cur[key] = [] if isinstance(nxt_key, int) else {}
            cur = cur[key]
        else:
            return None
    return cur


def _set_path(state, path, value):
    """kind=1 update from VS Code chat-session JSONL: set value at path."""
    cur = _walk_to_parent(state, path)
    if cur is None:
        return
    last = path[-1]
    if isinstance(cur, list) and isinstance(last, int):
        if last == len(cur):
            cur.append(value)
        elif 0 <= last < len(cur):
            cur[last] = value
    elif isinstance(cur, dict):
        cur[last] = value


def _append_path(state, path, value):
    """kind=2 update from VS Code chat-session JSONL: append items to the list at path."""
    cur = _walk_to_parent(state, path)
    if cur is None:
        return
    last = path[-1]
    if isinstance(cur, dict):
        if not isinstance(cur.get(last), list):
            cur[last] = []
        target = cur[last]
    elif isinstance(cur, list) and isinstance(last, int) and 0 <= last < len(cur):
        target = cur[last]
    else:
        return
    if isinstance(target, list) and isinstance(value, list):
        target.extend(value)


def _copilot_session_from_state(state, fallback_id, project):
    tb = TranscriptBuilder()
    user_n = assistant_n = 0
    tool_calls = {}
    models = {}
    ts_list = []
    start = epoch_from_ms(state.get("creationDate"))
    end = epoch_from_ms(state.get("lastMessageDate")) or start
    for r in state.get("requests") or []:
        if not isinstance(r, dict):
            continue
        count_model(models, r.get("modelId"))
        ts = epoch_from_ms(r.get("timestamp"))
        if ts:
            start = start or ts
            end = max(end or ts, ts)
            ts_list.append(ts)
            # totalElapsed (duration ms) marks the end of the turn
            elapsed = ((r.get("result") or {}).get("timings") or {}).get("totalElapsed")
            if isinstance(elapsed, (int, float)) and 0 < elapsed < 86400000:
                ts_list.append(ts + elapsed / 1000.0)
        msg = r.get("message") or {}
        text = msg.get("text") if isinstance(msg, dict) else None
        if text:
            user_n += 1
            tb.user(text)
        resp_texts = []
        for part in r.get("response") or []:
            if not isinstance(part, dict):
                continue
            kind = part.get("kind", "")
            if kind == "toolInvocationSerialized":
                name = part.get("toolId") or part.get("toolName") or "tool"
                tool_calls[name] = tool_calls.get(name, 0) + 1
                tb.tool(name)
            elif isinstance(part.get("value"), str):
                resp_texts.append(part["value"])
        if resp_texts:
            assistant_n += 1
            tb.assistant(" ".join(resp_texts))
    sid = state.get("sessionId") or fallback_id
    return make_meta("copilot-vscode", sid, project, start, end, user_n, assistant_n, tool_calls, tb.text(),
                     timestamps=ts_list, models=models)


def scan_copilot_vscode(home, since):
    sessions = []
    for root in _vscode_chat_roots(home, ["Code", "Code - Insiders"]):
        for path in recent_files(str(root / "*" / "chatSessions" / "*"), since):
            if not (path.endswith(".json") or path.endswith(".jsonl")):
                continue
            project = ""
            ws = load_json(Path(path).parent.parent / "workspace.json")
            if ws and isinstance(ws.get("folder"), str):
                project = ws["folder"].replace("file://", "")
            if path.endswith(".jsonl"):
                state = None
                for o in iter_jsonl(path):
                    kind = o.get("kind")
                    if kind == 0:
                        state = o.get("v") or {}
                    elif isinstance(state, dict) and isinstance(o.get("k"), list) and o["k"]:
                        if kind == 1:
                            _set_path(state, o["k"], o.get("v"))
                        elif kind == 2:
                            _append_path(state, o["k"], o.get("v"))
                if not isinstance(state, dict):
                    continue
            else:
                state = load_json(path)
                if not isinstance(state, dict):
                    continue
            sessions.append(_copilot_session_from_state(state, Path(path).stem, project))
    return sessions


def _deep_find_messages(obj, depth=0):
    """Best-effort: find a list of {role/type + content/text} message dicts anywhere in obj."""
    if depth > 4:
        return []
    if isinstance(obj, list):
        msgs = [m for m in obj if isinstance(m, dict)
                and (m.get("role") or m.get("type")) and (m.get("content") or m.get("text"))]
        if len(msgs) >= 2:
            return msgs
        return []
    if isinstance(obj, dict):
        for key in ("messages", "chatMessages", "history", "timeline", "events"):
            found = _deep_find_messages(obj.get(key), depth + 1)
            if found:
                return found
        for v in obj.values():
            found = _deep_find_messages(v, depth + 1)
            if found:
                return found
    return []


def _session_from_generic_messages(tool, sid, project, msgs, fallback_ts):
    tb = TranscriptBuilder()
    user_n = assistant_n = 0
    models = {}
    start = end = None
    for m in msgs:
        role = str(m.get("role") or m.get("type") or "").lower()
        count_model(models, m.get("model") or m.get("modelId") or m.get("modelID"))
        content = m.get("content") if isinstance(m.get("content"), str) else m.get("text")
        if not isinstance(content, str):
            continue
        ts = epoch_from_ms(m.get("timestamp") or m.get("createdAt")) or epoch_from_iso(
            m.get("timestamp") or m.get("createdAt"))
        if ts:
            start = start or ts
            end = ts
        if "user" in role or role == "human":
            user_n += 1
            tb.user(content)
        elif role in ("assistant", "ai", "agent", "model") or "assistant" in role:
            assistant_n += 1
            tb.assistant(content)
    start = start or fallback_ts
    end = end or fallback_ts
    return make_meta(tool, sid, project, start, end, user_n, assistant_n, {}, tb.text(), models=models)


def scan_copilot_cli(home, since):
    sessions = []
    root = home / ".copilot" / "history-session-state"
    if not root.is_dir():
        return sessions
    for entry in sorted(root.iterdir()):
        try:
            mtime = entry.stat().st_mtime
        except OSError:
            continue
        if mtime < since:
            continue
        json_files = [entry] if entry.suffix == ".json" else sorted(entry.glob("*.json")) if entry.is_dir() else []
        for jf in json_files:
            data = load_json(jf)
            msgs = _deep_find_messages(data)
            if msgs:
                sessions.append(_session_from_generic_messages(
                    "copilot-cli", entry.stem, "", msgs, mtime))
                break
    return sessions


# --- GitHub Copilot for JetBrains -----------------------------------------------
# JetBrains IDEs store Copilot chat under ~/.config/github-copilot/ (macOS + Linux)
# or %LOCALAPPDATA%\github-copilot\ (Windows). The `intellij/` subdir holds only config
# (instructions + mcp.json); actual sessions live under per-IDE product-code dirs
# (`iu`=IntelliJ, `ws`=WebStorm, `py`/`pc`=PyCharm, `rd`=Rider, `ai`=Android Studio, ...)
# in `chat-sessions/<id>/00000000000.xd`. The `.xd` file is a JetBrains Xodus embedded-DB
# log (binary, Java-serialized) — not JSON. There is no stdlib Xodus/Nitrite reader, so the
# adapter is best-effort, like copilot-cli/kiro: it extracts printable text runs from the
# log and reconstructs turns using the `query` (user) and `response` (assistant) property
# markers that precede each message's content. Newer agent/chat/edit sessions
# (chat-agent-sessions/chat-sessions/chat-edit-sessions) keep their messages in a sibling
# Nitrite DB (`copilot-*-nitrite.db`, Nitrite v4 on H2 MVStore with Java serialization).
# That DB is not stdlib-decodable as a database, but the message payloads are stored as
# Java-serialized UTF strings (TC_STRING `0x74` + u2 length, TC_LONGSTRING `0x7c` + u8
# length), so `_parse_jetbrains_nitrite` recovers them the same best-effort way: it walks
# the serialized strings in file order and rebuilds turns from the `query`/`response`
# field markers. Unlike Xodus, the Nitrite log also exposes decimal `created_at` epoch-ms
# timestamps (real duration + window membership) and the selected `model`. NOTE: the
# top-level `~/.config/github-copilot/copilot-intellij.db` is a plain SQLite state store
# (a single `mcp-first-boot-completed` flag) — it holds NO transcripts and is not scanned.

# Xodus entity-schema / property tokens that are NOT message content.
_JB_NON_CONTENT = {
    "query", "response", "content", "request", "references", "steps", "turns",
    "sessionId", "type", "status", "errorCode", "rating", "title", "input", "client",
    "user", "nameSource", "projectName", "createdAt", "activeAt", "modifiedAt",
    "editorName", "editorVersion", "editorPluginVersion", "name", "executedAt",
    "migrateReferences", "GitHub Copilot",
    "XdChatSession", "XdClient", "XdMessage", "XdStep", "XdTurn", "XdFileReference",
    "XdMigration",
}
_JB_UUID_RE = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-")


def _xodus_strings(data, min_len=3):
    """Best-effort: ASCII-printable text runs from a Xodus `.xd` log, in file order.
    Keeps tab/newline so a multi-line message blob stays a single run; breaks on every
    other control byte AND on high bytes (>=0x80), which Xodus uses as length prefixes
    and record tags between values — gluing them onto a run would corrupt the `query`/
    `response` markers and message text the adapter keys off."""
    out, cur = [], bytearray()
    for b in data:
        if b in (9, 10, 13) or 32 <= b <= 126:
            cur.append(b)
        else:
            if len(cur) >= min_len:
                out.append(cur.decode("ascii", "replace"))
            cur = bytearray()
    if len(cur) >= min_len:
        out.append(cur.decode("ascii", "replace"))
    return out


def _jb_is_content(t):
    """Heuristic: does this extracted string look like real message text (vs a schema
    token, UUID, file URI, or binary noise)? Real text carries at least two letters,
    which rejects the short length-prefix artifacts (`1q1`, `8b8`, ...) Xodus interleaves."""
    return (len(t) >= 3 and t not in _JB_NON_CONTENT
            and not _JB_UUID_RE.match(t) and not t.startswith("file://")
            and sum(c.isalpha() for c in t) >= 2)


def _jb_project_from_uris(uris):
    """Infer the project from the common parent dir of the session's file:// references.
    When a session touches files in more than one repo the common parent collapses to the
    user's home dir (e.g. `.../Users/<name>`), which is not a project — reject those so the
    field stays blank rather than misleading."""
    parts, seen = [], set()
    for u in uris:
        p = re.sub(r"%([0-9A-Fa-f]{2})", lambda m: chr(int(m.group(1), 16)), u[len("file://"):])
        low = p.lower()
        if low in seen:  # drop the lowercased index copies Xodus stores alongside originals
            continue
        seen.add(low)
        parts.append(p.strip("/").split("/"))
    if not parts:
        return ""
    common = []
    for col in zip(*parts):
        if len(set(col)) == 1:
            common.append(col[0])
        else:
            break
    if not common:
        return ""
    if len(common) >= 2 and common[-2].lower() in ("users", "home", "root"):
        return ""  # common parent is a home dir, not a project
    return common[-1]


def _parse_jetbrains_chat(data, sid, mtime):
    """Reconstruct a Copilot-for-JetBrains chat session from its Xodus `.xd` bytes.
    Roles come from the `query`/`response` markers; the lowercased search-index copies
    Xodus keeps are deduped by case-folded text."""
    tb = TranscriptBuilder()
    user_n = assistant_n = 0
    captured, uris, pending = set(), [], None
    for s in _xodus_strings(data):
        t = s.strip()
        if t == "query":
            pending = "user"
            continue
        if t == "response":
            pending = "assistant"
            continue
        if pending:
            # Content is the run IMMEDIATELY after the marker. Anything else (a schema
            # token like `steps`, or the next marker in the lowercased index region) is
            # not this turn's content, so consume the marker and move on either way.
            role, pending = pending, None
            if _jb_is_content(t):
                key = t.lower()
                if key not in captured:  # drop the lowercased search-index duplicates
                    captured.add(key)
                    if role == "user":
                        user_n += 1
                        tb.user(t)
                    else:
                        assistant_n += 1
                        tb.assistant(t)
        elif t.startswith("file://"):
            uris.append(t)
    # Xodus stores no decimal timestamps; use file mtime as last-activity and leave the
    # start unknown so duration stays None (a single-timestamp session passes the filter).
    return make_meta("copilot-jetbrains", sid, _jb_project_from_uris(uris), None, mtime,
                     user_n, assistant_n, {}, tb.text())


# Cap on bytes read from a Nitrite DB: the agent log for a long session can grow to
# hundreds of MB. We read at most the trailing slice (MVStore appends, so the newest
# chunks — the ones inside the analysis window — live near the end of the file).
_MAX_NITRITE_BYTES = 96 * 1024 * 1024

# Field-name / status / author tokens that appear next to a turn marker but are NOT the
# turn's message text (on top of the shared Xodus token set).
_JB_NITRITE_SKIP = _JB_NON_CONTENT | {
    "ok", "status", "stringContent", "contents", "annotations", "agent", "slug",
    "avatarUrl", "confirmationResponse", "confirmationRequest", "notifications",
    "errorReason", "model", "modelProviderName", "modelInformation", "auto",
    "references", "file", "uri", "range", "line", "character", "Project",
    "Ask about your project", "completed", "request", "timestamp", "stringContent",
}


def _iter_java_strings(buf):
    """Yield Java-serialized string values (TC_STRING `0x74` + u2 length, TC_LONGSTRING
    `0x7c` + u8 length) from `buf` in file order. Best-effort, like `_xodus_strings`: a
    candidate marker is accepted only when its length-prefixed payload is mostly printable;
    otherwise we jump (via `bytes.find`, at C speed) to the next candidate byte, which both
    skips binary noise fast and keeps the parser aligned to real string boundaries."""
    i, N = 0, len(buf)
    while i < N:
        c = buf[i]
        consumed = False
        if c == 0x74 and i + 3 <= N:
            ln = (buf[i + 1] << 8) | buf[i + 2]
            if 0 < ln <= N - (i + 3):
                s = buf[i + 3:i + 3 + ln]
                if sum(32 <= x < 127 or x in (9, 10, 13) for x in s) >= ln * 0.9:
                    yield s.decode("utf-8", "replace")
                    i += 3 + ln
                    consumed = True
        elif c == 0x7c and i + 9 <= N:
            ln = int.from_bytes(buf[i + 1:i + 9], "big")
            if 0 < ln <= N - (i + 9):
                yield buf[i + 9:i + 9 + ln].decode("utf-8", "replace")
                i += 9 + ln
                consumed = True
        if not consumed:
            nt = buf.find(b"\x74", i + 1)
            nl = buf.find(b"\x7c", i + 1)
            cands = [x for x in (nt, nl) if x != -1]
            if not cands:
                break
            i = min(cands)


def _jb_nitrite_content(t):
    """Does this serialized string look like real turn text (vs a schema/status token,
    UUID, file URI, JSON sub-payload, or bare number)?"""
    return (_jb_is_content(t) and t not in _JB_NITRITE_SKIP
            and not t.startswith('{"') and not t.startswith("[{") and not t.isdigit())


def _parse_jetbrains_nitrite(path):
    """Reconstruct a Copilot-for-JetBrains chat/agent/edit session from its Nitrite
    `copilot-*-nitrite.db` bytes. Walks the Java-serialized strings and rebuilds turns
    from the `query`/`response` field markers (the message text is the first content-like
    string within a short lookahead, skipping status/author tokens like `ok` and
    `GitHub Copilot`). Recovers `created_at` epoch-ms timestamps and the selected model."""
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        if size > _MAX_NITRITE_BYTES:
            f.seek(size - _MAX_NITRITE_BYTES)
        buf = f.read(_MAX_NITRITE_BYTES)
    sid = Path(path).parent.name
    mtime = os.path.getmtime(path)
    tb = TranscriptBuilder()
    user_n = assistant_n = 0
    captured, uris, models = set(), [], {}
    min_ts = max_ts = None
    pending, look = None, 0
    prev2 = prev1 = None  # ring buffer for the `model`,<value>,`modelProviderName` rule
    for t in _iter_java_strings(buf):
        t = t.strip()
        # Decimal epoch-ms timestamps (createdAt/created_at values), 2020-01-01..~2033.
        if len(t) == 13 and t.isdigit():
            v = int(t)
            if 1577836800000 <= v <= 2000000000000:
                if min_ts is None or v < min_ts:
                    min_ts = v
                if max_ts is None or v > max_ts:
                    max_ts = v
        # Model is serialized as `model`, <value>, `modelProviderName`/`modelInformation`.
        if t in ("modelProviderName", "modelInformation") and prev2 == "model" and prev1:
            count_model(models, prev1)
        if t == "query":
            pending, look = "user", 8
        elif t == "response":
            pending, look = "assistant", 8
        elif pending and look > 0:
            if t.startswith('{"') or t.startswith("[{"):
                pending = None  # structured agent payload (subgraph) — no clean text
            elif _jb_nitrite_content(t):
                key = t.lower()
                if key not in captured:  # drop the lowercased search-index duplicates
                    captured.add(key)
                    if pending == "user":
                        user_n += 1
                        tb.user(t)
                    else:
                        assistant_n += 1
                        tb.assistant(t)
                pending = None
            else:
                look -= 1
                if look == 0:
                    pending = None
        if t.startswith("file://"):
            uris.append(t)
        prev2, prev1 = prev1, t
    start = min_ts / 1000.0 if min_ts else None
    end = max_ts / 1000.0 if max_ts else mtime
    return make_meta("copilot-jetbrains", sid, _jb_project_from_uris(uris), start, end,
                     user_n, assistant_n, {}, tb.text(), models=models)


def _copilot_jetbrains_roots(home):
    """Copilot-for-JetBrains config roots: `~/.config/github-copilot` (macOS + Linux),
    `%LOCALAPPDATA%\\github-copilot` (Windows). Env var honored only for the real home."""
    bases = [home / ".config" / "github-copilot",
             home / "AppData" / "Local" / "github-copilot"]
    if home == Path.home():
        v = os.environ.get("LOCALAPPDATA")
        if v:
            bases.append(Path(v) / "github-copilot")
    out = []
    for b in bases:
        if b not in out and b.is_dir():
            out.append(b)
    return out


def scan_copilot_jetbrains(home, since):
    # A session dir can hold both a content-bearing Nitrite DB and a metadata-only Xodus
    # `.xd` (newer sessions write the real turns to Nitrite). Key by session id and keep
    # whichever variant recovered more user messages, so the empty `.xd` never shadows it.
    by_sid = {}

    def consider(meta):
        sid = meta["session_id"]
        cur = by_sid.get(sid)
        if cur is None or meta["user_msg_count"] > cur["user_msg_count"]:
            by_sid[sid] = meta

    for root in _copilot_jetbrains_roots(home):
        # <product>/<*-sessions>/<session-id>/copilot-*-nitrite.db  (newer chat/agent/edit)
        for db in recent_files(str(root / "*" / "*-sessions" / "*" / "copilot-*-nitrite.db"), since):
            try:
                consider(_parse_jetbrains_nitrite(Path(db)))
            except (OSError, ValueError):
                continue
        # <product>/<*-sessions>/<session-id>/00000000000.xd  (also old intellij/ layout)
        for xd in recent_files(str(root / "*" / "*-sessions" / "*" / "00000000000.xd"), since):
            xd = Path(xd)
            try:
                data = xd.read_bytes()
            except OSError:
                continue
            consider(_parse_jetbrains_chat(data, xd.parent.name, os.path.getmtime(xd)))
    return list(by_sid.values())


def scan_cursor(home, since):
    sessions = []
    roots = [base / "Cursor" / "User" / "globalStorage" / "state.vscdb"
             for base in _app_data_bases(home)]
    db = next((p for p in roots if p.is_file()), None)
    if not db:
        return sessions
    con, tmpdir = open_sqlite_ro(db)
    if not con:
        return sessions
    try:
        cur = con.cursor()
        bub = con.cursor()  # separate cursor: nested execute on `cur` would reset the outer iteration
        for key, value in cur.execute(
                "SELECT key, value FROM cursorDiskKV WHERE key LIKE 'composerData:%'"):
            try:
                o = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                continue
            created = epoch_from_ms(o.get("createdAt"))
            updated = epoch_from_ms(o.get("lastUpdatedAt")) or created
            if not created or max(created, updated or 0) < since:
                continue
            cid = o.get("composerId") or key.split(":", 1)[1]
            tb = TranscriptBuilder()
            user_n = assistant_n = 0
            tool_calls = {}
            # bubbles carry no model info; the composer-level modelConfig is the
            # session's selected model
            models = {}
            mc = o.get("modelConfig") or {}
            if isinstance(mc, dict):
                sel = [sm.get("modelId") for sm in mc.get("selectedModels") or []
                       if isinstance(sm, dict)]
                count_model(models, mc.get("modelName") or (sel[0] if sel else None))
            headers = o.get("fullConversationHeadersOnly") or []
            for h in headers:
                bid = h.get("bubbleId") if isinstance(h, dict) else None
                if not bid:
                    continue
                row = bub.execute("SELECT value FROM cursorDiskKV WHERE key = ?",
                                  (f"bubbleId:{cid}:{bid}",)).fetchone()
                if not row:
                    continue
                try:
                    b = json.loads(row[0])
                except (json.JSONDecodeError, TypeError):
                    continue
                text = (b.get("text") or "").strip()
                tfd = b.get("toolFormerData") or {}
                if b.get("type") == 1 and text:
                    user_n += 1
                    tb.user(text)
                elif b.get("type") == 2:
                    if isinstance(tfd, dict) and tfd.get("name"):
                        tool_calls[tfd["name"]] = tool_calls.get(tfd["name"], 0) + 1
                        tb.tool(tfd["name"])
                    if text:
                        assistant_n += 1
                        tb.assistant(text)
            sessions.append(make_meta(
                "cursor", cid, str(o.get("name") or ""), created, updated,
                user_n, assistant_n, tool_calls, tb.text(), models=models))
    except sqlite3.Error:
        pass
    finally:
        con.close()
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)
    return sessions


def scan_codex(home, since):
    sessions = []
    for root in (home / ".codex" / "sessions", home / ".codex" / "archived_sessions"):
        if not root.is_dir():
            continue
        for path in recent_files(str(root / "**" / "rollout-*.jsonl"), since):
            tb = TranscriptBuilder()
            user_n = assistant_n = 0
            tool_calls = {}
            models = {}
            start = end = None
            sid = Path(path).stem
            cwd = None
            ts_list = []
            for o in iter_jsonl(path):
                ts = epoch_from_iso(o.get("timestamp"))
                if ts:
                    ts_list.append(ts)
                payload = o.get("payload") or {}
                if not isinstance(payload, dict):
                    continue
                pt = payload.get("type")
                if o.get("type") == "session_meta":
                    sid = payload.get("id") or sid
                    cwd = payload.get("cwd")
                    start = start or epoch_from_iso(payload.get("timestamp")) or ts
                elif o.get("type") == "turn_context":
                    count_model(models, payload.get("model"))
                elif pt == "user_message":
                    text = (payload.get("message") or "").strip()
                    if text and not text.startswith("<"):
                        user_n += 1
                        tb.user(text)
                        if ts:
                            start = start or ts
                            end = ts
                elif pt == "agent_message":
                    text = (payload.get("message") or "").strip()
                    if text:
                        assistant_n += 1
                        tb.assistant(text)
                        if ts:
                            end = ts
                elif pt == "function_call":
                    name = payload.get("name") or "tool"
                    tool_calls[name] = tool_calls.get(name, 0) + 1
                    tb.tool(name)
                    if ts:
                        end = ts
            sessions.append(make_meta(
                "codex", sid, cwd, start, end, user_n, assistant_n, tool_calls, tb.text(),
                timestamps=ts_list, models=models))
    return sessions


def scan_kiro(home, since):
    """Kiro stores agent chat inside per-workspace state.vscdb (VS Code fork). Best effort."""
    sessions = []
    for root in _vscode_chat_roots(home, ["Kiro"]):
        for db in recent_files(str(root / "*" / "state.vscdb"), since):
            con, tmpdir = open_sqlite_ro(db)
            if not con:
                continue
            try:
                cur = con.cursor()
                rows = cur.execute(
                    "SELECT key, value FROM ItemTable WHERE key LIKE '%kiro%' OR key LIKE '%chat%'").fetchall()
                for key, value in rows:
                    try:
                        data = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        continue
                    msgs = _deep_find_messages(data)
                    if msgs:
                        sid = Path(db).parent.name + ":" + key
                        sessions.append(_session_from_generic_messages(
                            "kiro", sid, "", msgs, os.path.getmtime(db)))
            except sqlite3.Error:
                pass
            finally:
                con.close()
                if tmpdir:
                    shutil.rmtree(tmpdir, ignore_errors=True)
    return sessions


def _opencode_session_from_parts(sid, directory, title, created, updated, messages):
    """messages: list of (role, created_ts, parts, model) where parts is list of part dicts."""
    tb = TranscriptBuilder()
    user_n = assistant_n = 0
    tool_calls = {}
    models = {}
    ts_list = [t for _r, t, _p, _m in messages if t]
    for role, _ts, parts, model in messages:
        count_model(models, model)
        texts = []
        for p in parts:
            ptype = p.get("type")
            if ptype == "text" and isinstance(p.get("text"), str):
                texts.append(p["text"])
            elif ptype == "tool":
                name = p.get("tool") or "tool"
                tool_calls[name] = tool_calls.get(name, 0) + 1
                tb.tool(name)
        joined = " ".join(texts).strip()
        if role == "user" and joined:
            user_n += 1
            tb.user(joined)
        elif role == "assistant" and joined:
            assistant_n += 1
            tb.assistant(joined)
    return make_meta("opencode", sid, directory or title, created, updated,
                     user_n, assistant_n, tool_calls, tb.text(), timestamps=ts_list, models=models)


def _opencode_bases(home):
    """OpenCode data roots: `~/.local/share/opencode` on every OS (incl. Windows
    %USERPROFILE%), plus Windows builds that map XDG data to LOCALAPPDATA/APPDATA.
    Env vars only apply when scanning the real home (keeps --home fixture runs clean)."""
    bases = [home / ".local" / "share" / "opencode",
             home / "AppData" / "Local" / "opencode",
             home / "AppData" / "Roaming" / "opencode"]
    if home == Path.home():
        for env in ("LOCALAPPDATA", "APPDATA"):
            v = os.environ.get(env)
            if v:
                bases.append(Path(v) / "opencode")
    out = []
    for b in bases:
        if b not in out and b.is_dir():
            out.append(b)
    return out


def scan_opencode(home, since):
    sessions = []
    seen = set()
    for base in _opencode_bases(home):
        sessions += _scan_opencode_base(base, since, seen)
    return sessions


def _scan_opencode_base(base, since, seen):
    sessions = []
    # 1) newer builds: opencode.db
    db = base / "opencode.db"
    if db.is_file():
        con, tmpdir = open_sqlite_ro(db)
        if con:
            try:
                scur, mcur, pcur = con.cursor(), con.cursor(), con.cursor()
                session_rows = scur.execute(
                    "SELECT id, directory, title, time_created, time_updated, parent_id FROM session").fetchall()
                for sid, directory, title, created, updated, parent in session_rows:
                    if parent:  # subagent child session
                        continue
                    c, u = epoch_from_ms(created), epoch_from_ms(updated)
                    last = u or c
                    if not last or last < since:
                        continue
                    messages = []
                    msg_rows = mcur.execute(
                        "SELECT id, data FROM message WHERE session_id = ? ORDER BY time_created",
                        (sid,)).fetchall()
                    for mid_row, mdata in msg_rows:
                        try:
                            m = json.loads(mdata)
                        except (json.JSONDecodeError, TypeError):
                            continue
                        parts = []
                        for pd, in pcur.execute(
                                "SELECT data FROM part WHERE message_id = ? ORDER BY time_created",
                                (mid_row,)):
                            try:
                                p = json.loads(pd)
                            except (json.JSONDecodeError, TypeError):
                                continue
                            if isinstance(p, dict):
                                parts.append(p)
                        mts = epoch_from_ms((m.get("time") or {}).get("created"))
                        messages.append((m.get("role"), mts, parts, m.get("modelID")))
                    sessions.append(_opencode_session_from_parts(sid, directory, title, c, u, messages))
                    seen.add(sid)
            except sqlite3.Error:
                pass
            finally:
                con.close()
                if tmpdir:
                    shutil.rmtree(tmpdir, ignore_errors=True)
    # 2) older builds: JSON file storage
    storage = base / "storage"
    if storage.is_dir():
        for spath in recent_files(str(storage / "session" / "**" / "ses_*.json"), since):
            s = load_json(spath)
            if not isinstance(s, dict):
                continue
            sid = s.get("id")
            if not sid or sid in seen:
                continue
            t = s.get("time") or {}
            c, u = epoch_from_ms(t.get("created")), epoch_from_ms(t.get("updated"))
            messages = []
            for mpath in sorted(glob.glob(glob.escape(str(storage / "message" / sid)) + "/*.json")):
                m = load_json(mpath)
                if not isinstance(m, dict):
                    continue
                parts = [p for p in (load_json(pp) for pp in sorted(
                    glob.glob(glob.escape(str(storage / "part" / str(m.get("id")))) + "/*.json"))) if isinstance(p, dict)]
                mts = epoch_from_ms((m.get("time") or {}).get("created"))
                messages.append((m.get("role"), mts, parts, m.get("modelID")))
            sessions.append(_opencode_session_from_parts(
                sid, s.get("directory"), s.get("title"), c, u, messages))
            seen.add(sid)
    return sessions


def _antigravity_model_slug(name):
    """Antigravity reports models as display names ("Gemini 3.1 Pro (Low)"). Normalize to
    a lowercase-hyphen slug, dropping the reasoning-effort parenthetical, so the two
    in-log signals agree: "Claude Sonnet 4.6 (Thinking)" and the error-message machine id
    "claude-sonnet-4-6" both collapse to claude-sonnet-4-6."""
    name = re.sub(r"\([^)]*\)", "", name or "")  # drop "(Thinking)" / "(Low)"
    name = re.sub(r"[.\s]+", "-", name.strip().lower())
    return re.sub(r"[^a-z0-9\-]", "", name).strip("-")


_ANTIGRAVITY_PATH_KEYS = ("AbsolutePath", "DirectoryPath", "SearchPath", "TargetFile", "Path", "path")


def _antigravity_collect_paths(args, out):
    """Antigravity transcripts carry no cwd; tool-call args hold absolute paths. Values are
    JSON-encoded strings (wrapped in literal quotes), so strip them before use."""
    if not isinstance(args, dict):
        return
    for k in _ANTIGRAVITY_PATH_KEYS:
        v = args.get(k)
        if isinstance(v, str):
            v = v.strip().strip('"').strip()
            if v.startswith("/") or (len(v) > 2 and v[1] == ":"):  # unix or windows abs path
                out.append(v)


def _common_dir(paths):
    if not paths:
        return ""
    try:
        return os.path.commonpath(paths) if len(paths) > 1 else os.path.dirname(paths[0])
    except ValueError:  # mixed drives (Windows)
        return os.path.dirname(paths[0])


def _parse_antigravity(path, sid):
    """Parse one Antigravity `transcript*.jsonl`: one JSON object per step with
    `source` (USER_EXPLICIT / MODEL / SYSTEM), `type`, `created_at` (ISO), and
    `content` / `thinking` / `tool_calls` / `error`."""
    tb = TranscriptBuilder()
    user_n = assistant_n = 0
    tool_calls, models, ts_list = {}, {}, []
    start = end = None
    paths_seen, error_models = [], []
    for o in iter_jsonl(path):
        ts = epoch_from_iso(o.get("created_at"))
        if ts:
            start = start or ts
            end = ts
            ts_list.append(ts)
        src, typ = o.get("source"), o.get("type")
        content = o.get("content") or ""
        if typ == "ERROR_MESSAGE":
            m = re.search(r"\bmodel ([a-z0-9][\w.\-]+)", o.get("error") or "")
            if m:
                error_models.append(m.group(1))
        elif src == "USER_EXPLICIT" and typ == "USER_INPUT":
            for block in re.findall(r"<USER_SETTINGS_CHANGE>(.*?)</USER_SETTINGS_CHANGE>", content, re.S):
                sm = re.search(r"from (.+?) to (.+?)\.(?:\s|$)", block)
                if sm:  # model switch: both the prior and the new model were used
                    count_model(models, _antigravity_model_slug(sm.group(1)))
                    count_model(models, _antigravity_model_slug(sm.group(2)))
            req = re.search(r"<USER_REQUEST>\s*(.*?)\s*</USER_REQUEST>", content, re.S)
            text = (req.group(1) if req else content).strip()
            if text:
                user_n += 1
                tb.user(text)
        elif src == "MODEL" and typ == "PLANNER_RESPONSE":
            for call in o.get("tool_calls") or []:
                if not isinstance(call, dict):
                    continue
                name = call.get("name") or "tool"
                tool_calls[name] = tool_calls.get(name, 0) + 1
                tb.tool(name)
                _antigravity_collect_paths(call.get("args"), paths_seen)
            text = content.strip()
            if text:
                assistant_n += 1
                tb.assistant(text)
        # EPHEMERAL_MESSAGE (system reminders) and MODEL tool-result rows
        # (VIEW_FILE / GREP_SEARCH / ... — already counted via tool_calls) are ignored
    if not models:  # no model-switch in this session: fall back to error-message machine ids
        for mid in error_models:
            count_model(models, mid)
    return make_meta("antigravity", sid, _common_dir(paths_seen), start, end,
                     user_n, assistant_n, tool_calls, tb.text(), timestamps=ts_list, models=models)


def scan_antigravity(home, since):
    """Antigravity (Gemini IDE) stores per-session step logs as JSONL under
    `~/.gemini/antigravity/brain/<session-id>/.system_generated/logs/`. The `.gemini`
    home dir is the same on macOS/Linux/Windows (%USERPROFILE%). `transcript_full.jsonl`
    has untruncated content; `transcript.jsonl` is the truncated fallback."""
    sessions = []
    brain = home / ".gemini" / "antigravity" / "brain"
    if not brain.is_dir():
        return sessions
    for sdir in sorted(brain.iterdir()):
        if not sdir.is_dir():
            continue
        logs = sdir / ".system_generated" / "logs"
        path = logs / "transcript_full.jsonl"
        if not path.is_file():
            path = logs / "transcript.jsonl"
        try:
            if not path.is_file() or os.path.getmtime(path) < since:
                continue
        except OSError:
            continue
        sessions.append(_parse_antigravity(str(path), sdir.name))
    return sessions


ADAPTERS = [
    ("claude-code", scan_claude_code),
    ("claude-cowork", scan_claude_cowork),
    ("copilot-vscode", scan_copilot_vscode),
    ("copilot-cli", scan_copilot_cli),
    ("copilot-jetbrains", scan_copilot_jetbrains),
    ("cursor", scan_cursor),
    ("codex", scan_codex),
    ("kiro", scan_kiro),
    ("opencode", scan_opencode),
    ("antigravity", scan_antigravity),
]


# --- runtime detection -----------------------------------------------------------
# Detect whether this skill is running on the host machine (where the user's agent
# logs live) or inside a sandboxed runtime such as Claude Cowork. Cowork isolates the
# process with Bubblewrap + Linux namespaces and does NOT mount the host filesystem,
# so a scan from inside it can only see the sandbox's own session -- effectively an
# empty report. Detecting this up front lets the agent warn the user and point them at
# a non-sandboxed agent instead. See docs/research/claude-cowork-sandbox.md.

# Cowork installs its orchestrator as a global Node module at a fixed path.
COWORK_SANDBOX_MODULE = Path(
    "/usr/local/lib/node_modules_global/lib/node_modules/@anthropic-ai/sandbox-runtime")


def _pid1_comm():
    """Command name of PID 1 (Linux only). 'bwrap' indicates a Bubblewrap sandbox."""
    try:
        return Path("/proc/1/comm").read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _known_source_roots(home):
    """(tool, root) pairs for the primary log dir of each adapter, used to report which
    sources are even reachable from the current runtime."""
    roots = [
        ("claude-code", home / ".claude" / "projects"),
        ("codex", home / ".codex" / "sessions"),
        ("copilot-cli", home / ".copilot" / "history-session-state"),
        ("copilot-jetbrains", home / ".config" / "github-copilot"),
        ("copilot-jetbrains", home / "AppData" / "Local" / "github-copilot"),  # Windows
        ("antigravity", home / ".gemini" / "antigravity" / "brain"),
        ("opencode", home / ".local" / "share" / "opencode"),
    ]
    for base in _app_data_bases(home):
        roots += [
            ("claude-cowork", base / "Claude" / "local-agent-mode-sessions"),
            ("copilot-vscode", base / "Code" / "User" / "workspaceStorage"),
            ("cursor", base / "Cursor" / "User" / "globalStorage"),
            ("kiro", base / "Kiro" / "User" / "workspaceStorage"),
        ]
    return roots


def _reachable_sources(home):
    """Known agent-log roots that actually exist under `home` (dir-level, best effort)."""
    found = []
    for name, p in _known_source_roots(home):
        try:
            if name not in found and p.exists():
                found.append(name)
        except OSError:
            pass
    return sorted(found)


def detect_runtime(home):
    """Best-effort detection of the runtime this skill runs in. Returns a dict with the
    runtime label, whether it's sandboxed (host filesystem not mounted), the signals that
    fired, which sources are reachable, environment facts, and a user-facing
    recommendation. Never raises -- detection failures degrade to 'host'."""
    home = Path(home)
    cowork, generic = [], []

    home_under_sessions = home.parent.name == "sessions"
    if home_under_sessions:
        cowork.append(f"home '{home}' sits directly under a per-session 'sessions' volume")
    bindfs = next((sub for sub in (".skills", "uploads", "outputs")
                   if (home / "mnt" / sub).is_dir() or (home / sub).is_dir()), None)
    if bindfs:
        cowork.append(f"bindfs mount '{bindfs}' present in home (read-only skills/uploads layout)")
    try:
        module = COWORK_SANDBOX_MODULE.exists()
    except OSError:
        module = False
    if module:
        cowork.append("@anthropic-ai/sandbox-runtime installed globally")

    if _pid1_comm() == "bwrap":
        generic.append("PID 1 is bwrap (Bubblewrap container)")
    if "3128" in os.environ.get("HTTP_PROXY", "") or \
            "socks5h" in os.environ.get("ALL_PROXY", "").lower():
        generic.append("network egress forced through a localhost sandbox proxy")

    strong_cowork = module or (home_under_sessions and bool(bindfs))
    if cowork:
        runtime, confidence = "claude-cowork", ("high" if strong_cowork else "medium")
    elif generic:
        runtime, confidence = "generic-sandbox", ("high" if len(generic) >= 2 else "medium")
    else:
        runtime, confidence = "host", "high"

    sandboxed = runtime != "host"
    environment = {
        "platform": sys.platform,
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "home": str(home),
        "user": os.environ.get("USER") or os.environ.get("USERNAME") or "",
    }

    if runtime == "claude-cowork":
        recommendation = (
            "This skill is running inside Claude Cowork's sandboxed Linux runtime, which does "
            "not mount your host machine's agent log directories. From here it can only see "
            "logs created inside the sandbox, so a usage report would be empty or cover just "
            "this one session. Run /agent-insights from a non-sandboxed agent that has direct "
            "access to your host files -- e.g. Claude Code in your terminal, or another local "
            "coding agent (Cursor, Copilot, Codex) on the same machine.")
    elif runtime == "generic-sandbox":
        recommendation = (
            "This skill appears to be running inside a sandboxed runtime with restricted host "
            "filesystem access, so your host machine's agent logs may not be reachable. If the "
            "report comes back empty, re-run /agent-insights from a non-sandboxed agent with "
            "direct access to your home directory.")
    else:
        recommendation = ""

    return {
        "runtime": runtime,
        "sandboxed": sandboxed,
        "restricted_host_fs": sandboxed,
        "confidence": confidence,
        "signals": cowork + generic,
        "reachable_sources": _reachable_sources(home),
        "environment": environment,
        "recommendation": recommendation,
    }


def cmd_detect(args):
    home = Path(args.home).expanduser() if args.home else Path.home()
    print(json.dumps(detect_runtime(home), indent=1))
    return 0


# --- scan command ----------------------------------------------------------------


def session_key(meta):
    sid = re.sub(r"[^A-Za-z0-9_.-]", "_", str(meta["session_id"]))[:80]
    return f"{meta['tool']}__{sid}"


def is_self_referential(meta):
    head = meta["transcript"][:4000]
    return any(m in head for m in SELF_MARKERS)


def is_substantive(meta):
    if meta["user_msg_count"] < MIN_USER_MSGS:
        return False
    dur = meta["duration_minutes"]
    # unknown duration (single timestamp source): keep if it has real dialogue
    return dur is None or dur >= MIN_DURATION_MIN


def activity_ts(meta):
    """Timestamp that represents the session within the window: last activity,
    falling back to start. Used for window membership AND day/date-range bucketing
    so a long-lived resumed session is counted and bucketed on the same date."""
    return meta["end_ts"] or meta["start_ts"]


def in_window(meta, since):
    ts = activity_ts(meta)
    return ts is not None and ts >= since


def cmd_scan(args):
    home = Path(args.home).expanduser() if args.home else Path.home()
    data_dir = Path(args.data_dir).expanduser()
    since = datetime.now(timezone.utc).timestamp() - args.days * 86400
    runtime = detect_runtime(home)

    detected, all_sessions = {}, []
    for name, fn in ADAPTERS:
        try:
            found = fn(home, since)
        except Exception as e:  # one broken adapter must not kill the scan
            print(f"warning: {name} adapter failed: {e}", file=sys.stderr)
            found = []
        found = [m for m in found if in_window(m, since)]
        if found:
            detected[name] = len(found)
        all_sessions += found

    if not all_sessions:
        err = {"error": "No agent sessions found in window across any source. "
                        "Checked: " + ", ".join(n for n, _ in ADAPTERS),
               "runtime": runtime}
        if runtime["sandboxed"]:
            err["error"] = (f"No host agent sessions reachable. Detected runtime: "
                            f"{runtime['runtime']} (sandboxed; host filesystem not mounted). "
                            + runtime["recommendation"])
        print(json.dumps(err))
        return 2

    # dedupe by (tool, session_id): keep variant with most user messages
    by_key = {}
    for m in all_sessions:
        k = session_key(m)
        if k not in by_key or m["user_msg_count"] > by_key[k]["user_msg_count"]:
            by_key[k] = m

    kept = [m for m in by_key.values()
            if not is_self_referential(m) and is_substantive(m)]
    kept.sort(key=lambda m: m["end_ts"] or m["start_ts"] or 0, reverse=True)

    cache = data_dir / "cache"
    work = data_dir / "work"
    transcripts_dir = work / "transcripts"
    if work.exists():
        shutil.rmtree(work, ignore_errors=True)
    transcripts_dir.mkdir(parents=True, exist_ok=True)

    uncached = []
    for m in kept:
        k = session_key(m)
        save_json(cache / m["tool"] / f"{k}.meta.json", m)
        facets_path = cache / m["tool"] / f"{k}.facets.json"
        if facets_path.exists() and load_json(facets_path) is None:
            facets_path.unlink()  # corrupt cache entry
        if not facets_path.exists():
            uncached.append(m)

    cached_count = len(kept) - len(uncached)
    deferred = max(0, len(uncached) - MAX_FACET_EXTRACTIONS)
    uncached = uncached[:MAX_FACET_EXTRACTIONS]
    batches = []
    for i in range(0, len(uncached), BATCH_SIZE):
        batch = uncached[i:i + BATCH_SIZE]
        batch_files = []
        for m in batch:
            k = session_key(m)
            tpath = transcripts_dir / f"{k}.txt"
            header = (f"=== SESSION {k} ===\n"
                      f"Tool: {m['tool']} | Date: {fmt_date(m['start_ts'])} | "
                      f"Project: {m['project'] or 'unknown'} | "
                      f"Duration: {m['duration_minutes'] or '?'} min | "
                      f"Messages: {m['user_msg_count']} user / {m['assistant_msg_count']} assistant\n")
            tpath.write_text(header + m["transcript"][:30000], encoding="utf-8")
            batch_files.append(str(tpath))
        batches.append({"batch_id": len(batches), "transcript_files": batch_files,
                        "output_file": str(work / f"facets-batch-{len(batches)}.json")})

    summary = {
        "days": args.days,
        "runtime": runtime,
        "sources_detected": detected,
        "sessions_kept": len(kept),
        "sessions_with_cached_facets": cached_count,
        "facet_extractions_needed": len(uncached),
        "facet_extractions_deferred": deferred,
        "batches": batches,
        "per_tool": {t: sum(1 for m in kept if m["tool"] == t) for t in {m["tool"] for m in kept}},
    }
    save_json(work / "scan-summary.json", summary)
    print(json.dumps(summary, indent=1))
    return 0


# --- aggregate command -------------------------------------------------------------


def ingest_facet_batches(data_dir):
    """Validate facets-batch-*.json written by subagents; store per-session facet cache files."""
    work = data_dir / "work"
    cache = data_dir / "cache"
    ingested = errors = 0
    for bpath in sorted(glob.glob(str(work / "facets-batch-*.json"))):
        items = load_json(bpath)
        if not isinstance(items, list):
            errors += 1
            continue
        for item in items:
            if not isinstance(item, dict):
                errors += 1
                continue
            k = item.get("session_key")
            f = item.get("facets")
            if not k or not isinstance(f, dict) or "outcome" not in f or "brief_summary" not in f:
                errors += 1
                continue
            tool = k.split("__", 1)[0]
            save_json(cache / tool / f"{k}.facets.json", f)
            ingested += 1
    return ingested, errors


def cmd_aggregate(args):
    data_dir = Path(args.data_dir).expanduser()
    since = datetime.now(timezone.utc).timestamp() - args.days * 86400
    ingested, ingest_errors = ingest_facet_batches(data_dir)

    cache = data_dir / "cache"
    metas = []
    for mpath in glob.glob(str(cache / "*" / "*.meta.json")):
        m = load_json(mpath)
        if isinstance(m, dict) and in_window(m, since):
            f = load_json(mpath.replace(".meta.json", ".facets.json"))
            m["facets"] = f if isinstance(f, dict) else None
            metas.append(m)

    if not metas:
        print(json.dumps({"error": "No cached sessions in window; run scan first."}))
        return 2

    # drop warmup-only sessions from narrative analysis (kept in counts)
    def warmup_only(m):
        f = m.get("facets") or {}
        cats = f.get("goal_categories") or {}
        return list(cats.keys()) == ["warmup_minimal"]

    def add_counts(total, counts):
        for k, v in (counts or {}).items():
            if isinstance(v, (int, float)):
                total[k] = total.get(k, 0) + v

    tools_used, goals, outcomes, satisfaction, friction, session_types = {}, {}, {}, {}, {}, {}
    expertise_level = {}  # one rating per session (whole conversation)
    per_tool = {}
    day_hist = {}
    models_used = {}  # model -> number of sessions it appeared in
    total_minutes = 0.0
    briefs, friction_details = [], []
    for m in sorted(metas, key=lambda x: x["end_ts"] or 0, reverse=True):
        t = m["tool"]
        pt = per_tool.setdefault(t, {"sessions": 0, "user_messages": 0, "assistant_messages": 0,
                                     "hours": 0.0, "tool_calls": 0, "top_tools": {}, "models": {}})
        pt["sessions"] += 1
        pt["user_messages"] += m["user_msg_count"]
        pt["assistant_messages"] += m["assistant_msg_count"]
        dur = m["duration_minutes"] or 0
        pt["hours"] = round(pt["hours"] + dur / 60.0, 2)
        total_minutes += dur
        add_counts(tools_used, m.get("tool_calls"))
        add_counts(pt["top_tools"], m.get("tool_calls"))
        pt["tool_calls"] += sum((m.get("tool_calls") or {}).values())
        for model in m.get("models") or {}:
            models_used[model] = models_used.get(model, 0) + 1
            pt["models"][model] = pt["models"].get(model, 0) + 1
        ats = activity_ts(m)
        if ats:
            day = datetime.fromtimestamp(ats).strftime("%Y-%m-%d")
            day_hist[day] = day_hist.get(day, 0) + 1
        f = m.get("facets")
        if f and not warmup_only(m):
            add_counts(goals, f.get("goal_categories"))
            outcomes[f.get("outcome", "unclear")] = outcomes.get(f.get("outcome", "unclear"), 0) + 1
            add_counts(satisfaction, f.get("user_satisfaction_counts"))
            add_counts(friction, f.get("friction_counts"))
            st = f.get("session_type")
            if st:
                session_types[st] = session_types.get(st, 0) + 1
            exp = f.get("expertise_level")
            if exp:
                expertise_level[exp] = expertise_level.get(exp, 0) + 1
            if len(briefs) < 50 and f.get("brief_summary"):
                briefs.append({"tool": t, "date": fmt_date(m["start_ts"]),
                               "project": (m["project"] or "")[-60:],
                               "summary": f["brief_summary"]})
            fd = f.get("friction_detail")
            if fd and len(friction_details) < 20:
                friction_details.append({"tool": t, "detail": fd})

    def top(d, n=10):
        return dict(sorted(d.items(), key=lambda kv: -kv[1])[:n])

    def order_expertise_level(d):
        # Canonical low->high order so the chart reads novice->expert; unknown keys appended.
        ordered = {k: d[k] for k in EXPERTISE_LEVELS if k in d}
        for k in d:
            if k not in ordered:
                ordered[k] = d[k]
        return ordered

    for pt in per_tool.values():
        pt["top_tools"] = top(pt["top_tools"], 8)

    dates = [activity_ts(m) for m in metas if activity_ts(m)]
    version = skill_version()
    agg = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "version": version,
        "analysis_model": resolve_analysis_model(args.analysis_model),
        "window_days": args.days,
        "date_range": {"from": fmt_date(min(dates)) if dates else "?",
                       "to": fmt_date(max(dates)) if dates else "?"},
        "totals": {
            "sessions": len(metas),
            "sessions_with_facets": sum(1 for m in metas if m.get("facets")),
            "user_messages": sum(m["user_msg_count"] for m in metas),
            "assistant_messages": sum(m["assistant_msg_count"] for m in metas),
            "hours": round(total_minutes / 60.0, 1),
            "tools_detected": sorted(per_tool.keys()),
            "models_detected": sorted(models_used.keys()),
        },
        "per_tool": per_tool,
        "distributions": {
            "goal_categories": top(goals, 12),
            "outcomes": outcomes,
            "satisfaction": satisfaction,
            "friction": top(friction, 12),
            "session_types": session_types,
            "expertise_level": order_expertise_level(expertise_level),  # per-session user expertise, novice->expert
            "agent_tools_used": top(tools_used, 12),
            "models": top(models_used, 12),  # sessions per model
        },
        "sessions_per_day": dict(sorted(day_hist.items())),
        "facet_ingestion": {"ingested": ingested, "errors": ingest_errors},
        "narrative_context": {"session_briefs": briefs, "friction_details": friction_details},
    }
    save_json(data_dir / "aggregate.json", agg)
    print(json.dumps(agg, indent=1, ensure_ascii=False))
    return 0


# --- render command ---------------------------------------------------------------


def esc(s):
    import html as _html
    return _html.escape(str(s if s is not None else ""))


def md_inline(s):
    """Minimal markdown: escape HTML, then **bold** and newlines."""
    out = esc(s)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    return out.replace("\n\n", "</p><p>").replace("\n", "<br>")


def fmt_num(v):
    """Human number: thousands separators for ints, trimmed decimals for floats."""
    return f"{v:g}" if isinstance(v, float) else f"{v:,}"


def bar_chart(counts, tone="chart-1"):
    """Horizontal bar rows tinted with a chart-N design token (see REPORT_CSS)."""
    if not counts:
        return "<p class='muted'>No data.</p>"
    mx = max(counts.values()) or 1
    rows = []
    for k, v in counts.items():
        pct = max(3, round(v / mx * 100))
        rows.append(
            f"<div class='bar-row'><span class='bar-label' title='{esc(k)}'>{esc(k)}</span>"
            f"<span class='bar-track'><span class='bar' style='width:{pct}%;background:hsl(var(--{tone}))'></span></span>"
            f"<span class='bar-val'>{fmt_num(v)}</span></div>")
    return f"<div class='chart'>{''.join(rows)}</div>"


def card(title, body):
    return f"<article class='card'><h3>{esc(title)}</h3>{body}</article>"


def day_chart(day_hist):
    """Sessions-per-day column strip. Fills missing days between the first and last
    active date so gaps read as gaps."""
    if not day_hist:
        return "<p class='muted'>No data.</p>"
    try:
        from datetime import timedelta
        d0 = datetime.strptime(min(day_hist), "%Y-%m-%d").date()
        d1 = datetime.strptime(max(day_hist), "%Y-%m-%d").date()
        days = [(d0 + timedelta(n)).isoformat() for n in range((d1 - d0).days + 1)]
    except ValueError:
        days = sorted(day_hist)
    mx = max(day_hist.values()) or 1
    cols = []
    for day in days:
        n = day_hist.get(day, 0)
        pct = max(4, round(n / mx * 100)) if n else 0
        cls = " zero" if not n else ""
        cols.append(f"<span class='spark-col{cls}' style='height:{pct}%' "
                    f"title='{esc(day)} &middot; {n} session{'' if n == 1 else 's'}'></span>")
    label = (f"Sessions per day, {esc(days[0])} to {esc(days[-1])}, "
             f"peak {mx} in one day")
    return (f"<div class='spark' role='img' aria-label='{label}'>{''.join(cols)}</div>"
            f"<div class='spark-axis'><span>{esc(days[0])}</span><span>{esc(days[-1])}</span></div>")


# Self-contained stylesheet: semantic HSL tokens (light + dark), editorial type,
# layered shadows, staggered entrances. No external assets — the report must render
# offline and never phone home. Theme is user-toggled via html[data-theme]
# (default light), not the OS preference.
REPORT_CSS = """
:root {
  color-scheme: light;
  --background: 40 33% 97%;
  --foreground: 222 30% 13%;
  --card: 0 0% 100%;
  --muted: 40 22% 93%;
  --muted-foreground: 222 12% 40%;
  --border: 40 14% 87%;
  --accent: 12 62% 42%;
  --ink: 224 32% 13%;
  --ink-foreground: 40 30% 96%;
  --ink-muted: 224 16% 72%;
  --chart-1: 221 68% 56%;
  --chart-2: 152 30% 47%;
  --chart-3: 251 48% 63%;
  --chart-4: 12 66% 56%;
  --chart-5: 42 78% 47%;
  --radius: 12px;
  --radius-inner: 8px;
  --shadow-card: 0 1px 2px hsl(224 32% 13% / .04), 0 2px 6px hsl(224 32% 13% / .05),
                 0 10px 28px hsl(224 32% 13% / .05);
  --ease-out: cubic-bezier(0.23, 1, 0.32, 1);
  --font-display: "Charter", "Iowan Old Style", "Palatino", Georgia, "Times New Roman", serif;
  --font-body: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif;
  --font-mono: ui-monospace, "SF Mono", "Cascadia Code", Menlo, Consolas, monospace;
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --background: 224 26% 9%;
  --foreground: 40 22% 92%;
  --card: 224 22% 13%;
  --muted: 224 18% 18%;
  --muted-foreground: 224 10% 68%;
  --border: 224 14% 23%;
  --accent: 12 72% 70%;
  --ink: 224 28% 11%;
  --ink-foreground: 40 25% 94%;
  --ink-muted: 224 12% 66%;
  --chart-1: 221 66% 66%;
  --chart-2: 152 32% 56%;
  --chart-3: 251 52% 72%;
  --chart-4: 12 68% 66%;
  --chart-5: 42 70% 60%;
  --shadow-card: 0 0 0 1px hsl(224 14% 23%), 0 10px 28px hsl(224 40% 4% / .5);
}
* { box-sizing: border-box; }
html {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}
body {
  margin: 0;
  font-family: var(--font-body);
  font-size: 15px;
  line-height: 1.6;
  background: hsl(var(--background));
  color: hsl(var(--foreground));
}
.wrap { max-width: 920px; margin: 0 auto; padding: 0 24px; }
h1, h2, h3 { text-wrap: balance; }
p, li { text-wrap: pretty; }
a { color: hsl(var(--accent)); }

/* hero */
.hero {
  background:
    radial-gradient(52rem 26rem at 88% -10%, hsl(12 66% 56% / .16), transparent 60%),
    radial-gradient(40rem 22rem at 0% 110%, hsl(221 68% 56% / .14), transparent 55%),
    hsl(var(--ink));
  color: hsl(var(--ink-foreground));
  padding: 56px 0 48px;
}
.hero-kicker {
  margin: 0 0 12px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: .14em;
  text-transform: uppercase;
  color: hsl(var(--ink-muted));
}
.hero h1 {
  margin: 0 0 28px;
  font-family: var(--font-display);
  font-size: clamp(34px, 6vw, 48px);
  font-weight: 400;
  letter-spacing: -0.01em;
  line-height: 1.1;
}
.hero-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 24px;
  margin: 0 0 28px;
}
.stat-num {
  display: block;
  font-family: var(--font-display);
  font-size: 38px;
  line-height: 1.1;
  font-variant-numeric: tabular-nums;
}
.stat-label {
  display: block;
  margin-top: 4px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: .1em;
  text-transform: uppercase;
  color: hsl(var(--ink-muted));
}
.hero-meta { margin: 0; font-size: 13px; color: hsl(var(--ink-muted)); }
.hero-meta strong { color: hsl(var(--ink-foreground)); font-weight: 600; }

/* sections */
main { padding: 16px 0 64px; }
.section { margin-top: 48px; animation: rise 480ms var(--ease-out) both; animation-delay: calc(var(--i, 0) * 70ms); }
@keyframes rise { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
.sec-head {
  display: flex;
  align-items: baseline;
  gap: 12px;
  border-bottom: 1px solid hsl(var(--border));
  padding-bottom: 10px;
  margin-bottom: 20px;
}
.sec-num { font-family: var(--font-mono); font-size: 12px; color: hsl(var(--accent)); }
.sec-head h2 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 26px;
  font-weight: 400;
  letter-spacing: -0.01em;
}
.persona {
  margin: 0 0 20px;
  padding: 4px 0 4px 16px;
  border-left: 3px solid hsl(var(--accent));
  font-family: var(--font-display);
  font-size: 20px;
  line-height: 1.45;
}
.key { font-weight: 600; color: hsl(var(--accent)); }
.muted { color: hsl(var(--muted-foreground)); }

/* cards */
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 700px) { .grid2 { grid-template-columns: 1fr; } }
.card {
  background: hsl(var(--card));
  border-radius: var(--radius);
  padding: 20px;
  box-shadow: var(--shadow-card);
}
.card h3 {
  margin: 0 0 10px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: hsl(var(--muted-foreground));
}
.card p { margin: 8px 0; font-size: 14px; }
.card ul { margin: 8px 0; padding-left: 20px; font-size: 14px; }
.card li { margin: 4px 0; }

/* bar charts */
.chart { display: flex; flex-direction: column; gap: 6px; }
.bar-row { display: flex; align-items: center; gap: 8px; font-size: 13px; }
.bar-label { width: 38%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bar-track { flex: 1; height: 14px; background: hsl(var(--muted)); border-radius: 7px; overflow: hidden; }
.bar { display: block; height: 100%; border-radius: 7px; }
.bar-val { min-width: 48px; text-align: right; font-variant-numeric: tabular-nums; color: hsl(var(--muted-foreground)); }

/* daily activity */
.spark { display: flex; align-items: flex-end; gap: 3px; height: 88px; }
.spark-col { flex: 1; min-width: 2px; background: hsl(var(--chart-1)); border-radius: 3px 3px 0 0; }
.spark-col.zero { height: 3px; background: hsl(var(--muted)); }
.spark-axis {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-family: var(--font-mono);
  font-size: 11px;
  color: hsl(var(--muted-foreground));
}

/* table */
.table-card {
  background: hsl(var(--card));
  border-radius: var(--radius);
  box-shadow: var(--shadow-card);
  overflow-x: auto;
  margin-top: 16px;
}
table { width: 100%; border-collapse: collapse; font-size: 13.5px; }
th, td { text-align: left; padding: 10px 16px; border-bottom: 1px solid hsl(var(--border)); }
th {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: hsl(var(--muted-foreground));
}
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
tbody tr:last-child td { border-bottom: none; }
tfoot td { font-weight: 600; border-top: 2px solid hsl(var(--border)); border-bottom: none; }
@media (hover: hover) and (pointer: fine) { tbody tr:hover { background: hsl(var(--muted) / .5); } }

/* code */
pre {
  background: hsl(var(--muted));
  padding: 12px 14px;
  border-radius: var(--radius-inner);
  font-family: var(--font-mono);
  font-size: 12.5px;
  line-height: 1.5;
  overflow-x: auto;
  white-space: pre-wrap;
  overflow-wrap: break-word;
}
code {
  background: hsl(var(--muted));
  padding: 2px 5px;
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 12.5px;
  overflow-wrap: break-word;
}

footer { padding: 24px 0 48px; font-size: 12.5px; color: hsl(var(--muted-foreground)); border-top: 1px solid hsl(var(--border)); }
footer p { margin: 4px 0; }

/* theme toggle */
.theme-toggle {
  position: fixed;
  top: 16px;
  right: 16px;
  z-index: 10;
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  padding: 0;
  border: 1px solid hsl(var(--border));
  border-radius: 50%;
  background: hsl(var(--card) / .92);
  color: hsl(var(--foreground));
  cursor: pointer;
  box-shadow: var(--shadow-card);
  transition: transform 120ms var(--ease-out), background-color 120ms var(--ease-out);
}
.theme-toggle:active { transform: scale(0.94); }
.theme-toggle:focus-visible { outline: 2px solid hsl(var(--accent)); outline-offset: 2px; }
@media (hover: hover) and (pointer: fine) { .theme-toggle:hover { background: hsl(var(--card)); } }
.theme-toggle svg { width: 18px; height: 18px; }
.theme-toggle .icon-sun { display: none; }
:root[data-theme="dark"] .theme-toggle .icon-sun { display: block; }
:root[data-theme="dark"] .theme-toggle .icon-moon { display: none; }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: .01ms !important;
    animation-delay: 0ms !important;
    transition-duration: .01ms !important;
  }
}
@media print {
  .hero { background: none; color: hsl(var(--foreground)); padding: 24px 0; }
  .hero-kicker, .stat-label, .hero-meta { color: hsl(var(--muted-foreground)); }
  .section { animation: none; }
  .card, .table-card { box-shadow: none; border: 1px solid hsl(var(--border)); }
  .theme-toggle { display: none; }
}
"""

# Theme toggle: light by default; the saved choice is applied in <head> before first
# paint (no flash), and the button swaps html[data-theme] + persists to localStorage.
# Plain strings, not f-strings — the JS braces must survive verbatim.
THEME_INIT_JS = """
try {
  if (localStorage.getItem('agent-insights-theme') === 'dark')
    document.documentElement.dataset.theme = 'dark';
} catch (e) {}
"""

THEME_TOGGLE_HTML = """
<button id="theme-toggle" class="theme-toggle" type="button" aria-pressed="false" aria-label="Switch to dark theme">
<svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
<svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
</button>
"""

THEME_TOGGLE_JS = """
(function () {
  var btn = document.getElementById('theme-toggle');
  function apply(dark) {
    document.documentElement.dataset.theme = dark ? 'dark' : 'light';
    btn.setAttribute('aria-pressed', String(dark));
    btn.setAttribute('aria-label', dark ? 'Switch to light theme' : 'Switch to dark theme');
  }
  apply(document.documentElement.dataset.theme === 'dark');
  btn.addEventListener('click', function () {
    var dark = document.documentElement.dataset.theme !== 'dark';
    apply(dark);
    try { localStorage.setItem('agent-insights-theme', dark ? 'dark' : 'light'); } catch (e) {}
  });
})();
"""


def cmd_render(args):
    data_dir = Path(args.data_dir).expanduser()
    agg = load_json(data_dir / "aggregate.json")
    if not agg:
        print(json.dumps({"error": "aggregate.json missing; run aggregate first."}))
        return 2
    nar = load_json(data_dir / "narrative.json") or {}

    t = agg["totals"]
    analysis_model = agg.get("analysis_model") or "unknown"
    version = agg.get("version") or "unknown"

    sections = []  # (title, body_html); numbered + stagger-animated at assembly

    glance = nar.get("at_a_glance") or {}
    if glance:
        persona = ""
        if glance.get("persona"):
            persona = f"<p class='persona'>{md_inline(glance['persona'])}</p>"
        labels = [("whats_working", "What's working"), ("whats_hindering", "What's hindering you"),
                  ("quick_wins", "Quick wins to try"), ("ambitious_workflows", "Ambitious workflows")]
        cards = "".join(card(lbl, f"<p>{md_inline(glance.get(key, ''))}</p>")
                        for key, lbl in labels if glance.get(key))
        sections.append(("At a Glance", f"{persona}<div class='grid2'>{cards}</div>"))

    per_tool = agg.get("per_tool", {})
    # One chart per collected metric, all in the same tool order (by sessions desc)
    # so the eye can compare a tool's rank across metrics.
    tools_sorted = sorted(per_tool.items(), key=lambda kv: -kv[1]["sessions"])
    metric_charts = "".join(
        card(label, bar_chart({k: v[key] for k, v in tools_sorted}, tone))
        for key, label, tone in (
            ("sessions", "Sessions", "chart-1"),
            ("hours", "Hours", "chart-2"),
            ("user_messages", "User messages", "chart-3"),
            ("tool_calls", "Tool calls", "chart-4")))
    def top_models(v, n=3):
        ms = v.get("models") or {}
        return ", ".join(sorted(ms, key=lambda k: -ms[k])[:n])

    tbl_rows = "".join(
        f"<tr><td>{esc(k)}</td><td class='num'>{fmt_num(v['sessions'])}</td>"
        f"<td class='num'>{fmt_num(v['hours'])}</td>"
        f"<td class='num'>{fmt_num(v['user_messages'])}</td>"
        f"<td class='num'>{fmt_num(v['tool_calls'])}</td><td>{esc(top_models(v))}</td></tr>"
        for k, v in tools_sorted)
    distinct_models = {m for _k, v in tools_sorted for m in v.get("models") or {}}
    tbl_foot = (
        f"<tr><td>Total</td><td class='num'>{fmt_num(sum(v['sessions'] for _k, v in tools_sorted))}</td>"
        f"<td class='num'>{fmt_num(round(sum(v['hours'] for _k, v in tools_sorted), 2))}</td>"
        f"<td class='num'>{fmt_num(sum(v['user_messages'] for _k, v in tools_sorted))}</td>"
        f"<td class='num'>{fmt_num(sum(v['tool_calls'] for _k, v in tools_sorted))}</td>"
        f"<td>{len(distinct_models)} distinct</td></tr>")
    sections.append((
        "Per-Tool Breakdown",
        f"<div class='grid2'>{metric_charts}</div>"
        "<div class='table-card'><table>"
        "<thead><tr><th>Tool</th><th class='num'>Sessions</th><th class='num'>Hours</th>"
        "<th class='num'>User msgs</th><th class='num'>Tool calls</th><th>Models</th></tr></thead>"
        f"<tbody>{tbl_rows}</tbody><tfoot>{tbl_foot}</tfoot></table></div>"))

    day_hist = agg.get("sessions_per_day") or {}
    if day_hist:
        sections.append(("Daily Activity", card("Sessions per day", day_chart(day_hist))))

    tc = nar.get("tool_comparison") or {}
    if tc.get("narrative"):
        body = f"<p>{md_inline(tc['narrative'])}</p>"
        if tc.get("key_difference"):
            body += f"<p class='key'>{md_inline(tc['key_difference'])}</p>"
        sections.append(("Tool Comparison", body))

    pa = nar.get("project_areas") or {}
    if pa.get("areas"):
        cards = "".join(card(f"{a.get('name', '?')} ({a.get('session_count', '?')} sessions)",
                             f"<p>{md_inline(a.get('description', ''))}</p>") for a in pa["areas"])
        sections.append(("Project Areas", f"<div class='grid2'>{cards}</div>"))

    ist = nar.get("interaction_style") or {}
    if ist.get("narrative"):
        body = f"<p>{md_inline(ist['narrative'])}</p>"
        if ist.get("key_pattern"):
            body += f"<p class='key'>{md_inline(ist['key_pattern'])}</p>"
        sections.append(("Interaction Style", body))

    ww = nar.get("what_works") or {}
    if ww.get("impressive_workflows"):
        body = f"<p>{md_inline(ww.get('intro', ''))}</p><div class='grid2'>" + "".join(
            card(w.get("title", "?"), f"<p>{md_inline(w.get('description', ''))}</p>")
            for w in ww["impressive_workflows"]) + "</div>"
        sections.append(("What Works", body))

    fr = nar.get("friction_analysis") or {}
    friction_body = ""
    if fr.get("categories"):
        friction_body += f"<p>{md_inline(fr.get('intro', ''))}</p><div class='grid2'>"
        for c in fr["categories"]:
            ex = "".join(f"<li>{md_inline(e)}</li>" for e in c.get("examples", []))
            friction_body += card(c.get("category", "?"),
                                  f"<p>{md_inline(c.get('description', ''))}</p><ul>{ex}</ul>")
        friction_body += "</div>"
    if agg["distributions"].get("friction"):
        friction_body += card("Friction signals (from session facets)",
                              bar_chart(agg["distributions"]["friction"], "chart-4"))
    if friction_body:
        sections.append(("Friction", friction_body))

    sg = nar.get("suggestions") or {}
    if sg:
        body = ""
        for add in sg.get("memory_file_additions", sg.get("claude_md_additions", []) or []):
            body += card("Instruction file addition",
                         f"<p><code>{esc(add.get('addition', ''))}</code></p>"
                         f"<p>{md_inline(add.get('why', ''))}</p>")
        for ft in sg.get("features_to_try", []) or []:
            body += card(ft.get("feature", "?"),
                         f"<p>{md_inline(ft.get('one_liner', ''))} {md_inline(ft.get('why_for_you', ''))}</p>"
                         + (f"<pre>{esc(ft.get('example_code', ''))}</pre>" if ft.get("example_code") else ""))
        for up in sg.get("usage_patterns", []) or []:
            body += card(up.get("title", "?"),
                         f"<p>{md_inline(up.get('suggestion', ''))} {md_inline(up.get('detail', ''))}</p>"
                         + (f"<pre>{esc(up.get('copyable_prompt', ''))}</pre>" if up.get("copyable_prompt") else ""))
        if body:
            sections.append(("Suggestions", f"<div class='grid2'>{body}</div>"))

    nuc = nar.get("new_use_cases") or {}
    if nuc.get("use_cases"):
        body = f"<p>{md_inline(nuc.get('intro', ''))}</p>" if nuc.get("intro") else ""
        cards = "".join(
            card(u.get("title", "?"),
                 f"<p>{md_inline(u.get('description', ''))}</p>"
                 + (f"<p class='key'>{md_inline(u.get('relevance', ''))}</p>" if u.get("relevance") else "")
                 + (f"<pre>{esc(u.get('copyable_prompt', ''))}</pre>" if u.get("copyable_prompt") else ""))
            for u in nuc["use_cases"])
        sections.append(("New Use Cases to Try", f"{body}<div class='grid2'>{cards}</div>"))

    d = agg["distributions"]
    sections.append(("Stats", "<div class='grid2'>"
                     + card("Goals", bar_chart(d.get("goal_categories", {}), "chart-1"))
                     + card("Outcomes", bar_chart(d.get("outcomes", {}), "chart-2"))
                     + card("Model Uses (by session)", bar_chart(d.get("models", {}), "chart-3"))
                     + card("Agent tools used", bar_chart(d.get("agent_tools_used", {}), "chart-4"))
                     + card("User Expertise (per session)", bar_chart(d.get("expertise_level", {}), "chart-5"))
                     + "</div>"))

    fe = nar.get("fun_ending") or {}
    if fe.get("headline"):
        sections.append(("One More Thing",
                         card(fe["headline"], f"<p>{md_inline(fe.get('detail', ''))}</p>")))

    sections_html = "".join(
        f"<section class='section' style='--i:{i}'>"
        f"<div class='sec-head'><span class='sec-num'>{i + 1:02d}</span><h2>{esc(title)}</h2></div>"
        f"{body}</section>"
        for i, (title, body) in enumerate(sections))

    hero_stats = "".join(
        f"<div><span class='stat-num'>{fmt_num(num)}</span><span class='stat-label'>{esc(label)}</span></div>"
        for num, label in (
            (t["sessions"], "sessions"),
            (t["user_messages"], "user messages"),
            (t["hours"], "hours"),
            (len(t["tools_detected"]), "agent tools"),
            (len(t.get("models_detected") or []), "models")))

    html_doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Agent Insights &middot; last {agg['window_days']} days</title>
<script>{THEME_INIT_JS}</script>
<style>{REPORT_CSS}</style></head><body>
{THEME_TOGGLE_HTML}
<header class="hero"><div class="wrap">
<p class="hero-kicker">Agent Insights &middot; last {agg['window_days']} days</p>
<h1>How you worked with AI coding agents</h1>
<div class="hero-stats">{hero_stats}</div>
<p class="hero-meta">{esc(agg['date_range']['from'])} &rarr; {esc(agg['date_range']['to'])}
&middot; generated {esc(agg['generated_at'])}
&middot; analysis model <strong>{esc(analysis_model)}</strong>
&middot; skill v{esc(version)}</p>
</div></header>
<main><div class="wrap">
{sections_html}
</div></main>
<footer><div class="wrap">
<p>Generated locally by the agent-insights skill. All session data stays on this machine.</p>
<p>Analysis model (main agent): {esc(analysis_model)}. Sources: {esc(', '.join(t['tools_detected']))}.</p>
</div></footer>
<script>{THEME_TOGGLE_JS}</script>
</body></html>"""

    out = data_dir / f"report-{datetime.now().strftime('%Y-%m-%d')}_{agg['window_days']}-days.html"
    out.write_text(html_doc, encoding="utf-8")
    os.chmod(out, 0o600)
    print(json.dumps({"report": str(out)}))
    return 0


# --- main -----------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("detect", cmd_detect), ("scan", cmd_scan),
                     ("aggregate", cmd_aggregate), ("render", cmd_render)):
        p = sub.add_parser(name)
        p.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
        p.set_defaults(fn=fn)
        if name in ("scan", "aggregate"):
            p.add_argument("--days", type=int, default=30)
        if name == "aggregate":
            p.add_argument("--analysis-model", default=None,
                           help="model id of the main agent running this skill, recorded for benchmarking")
        if name in ("scan", "detect"):
            p.add_argument("--home", default=None, help="override home dir (tests/fixtures)")
    args = ap.parse_args()
    if hasattr(args, "days"):
        args.days = max(1, min(365, args.days))
    sys.exit(args.fn(args))


if __name__ == "__main__":
    main()
