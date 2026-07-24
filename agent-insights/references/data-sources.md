# agent-insights data sources

Where each supported agent tool stores session logs, and how the scanner parses them.
All adapters are equal: if a source exists it is processed, if not it is skipped silently.
The scan errors only when zero sessions are found across ALL sources.

| Tool | macOS | Linux | Windows | Format |
|---|---|---|---|---|
| Claude Code | `~/.claude/projects/<encoded-path>/*.jsonl` | same | same | JSONL |
| Claude Cowork | `~/Library/Application Support/Claude/local-agent-mode-sessions/` | `~/.config/Claude/local-agent-mode-sessions/` | `%APPDATA%\Claude\local-agent-mode-sessions\` or (Store build) `%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\local-agent-mode-sessions\` | JSON + JSONL |
| Copilot (VS Code) | `~/Library/Application Support/Code/User/workspaceStorage/<hash>/chatSessions/*` | `~/.config/Code/User/workspaceStorage/...` | `%APPDATA%\Code\User\workspaceStorage\...` | JSON or JSONL |
| Copilot CLI | `~/.copilot/session-state/<id>/events.jsonl` + `~/.copilot/session-store.db` (newer), `~/.copilot/history-session-state/` (older) | same | same | JSONL + SQLite (newer), JSON (older) |
| Copilot (JetBrains) | `~/.config/github-copilot/<ide>/*-sessions/<id>/00000000000.xd` (Xodus) + `.../copilot-*-nitrite.db` (Nitrite) | same | `%LOCALAPPDATA%\github-copilot\<ide>\...` | Xodus binary log + Nitrite/MVStore (Java-serialized) |
| Cursor | `~/Library/Application Support/Cursor/User/globalStorage/state.vscdb` | `~/.config/Cursor/...` | `%APPDATA%\Cursor\...` | SQLite |
| Codex | `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` (+ `archived_sessions/`) | same | same | JSONL |
| Kiro | `~/Library/Application Support/Kiro/User/workspaceStorage/*/state.vscdb` | `~/.config/Kiro/...` | `%APPDATA%\Kiro\...` | SQLite |
| OpenCode | `~/.local/share/opencode/opencode.db` (newer) and `~/.local/share/opencode/storage/{session,message,part}/` (older) | same | `%USERPROFILE%\.local\share\opencode\`, plus `%LOCALAPPDATA%\opencode\` and `%APPDATA%\opencode\` | SQLite + JSON |
| Antigravity | `~/.gemini/antigravity/brain/<session-id>/.system_generated/logs/transcript*.jsonl` | same | `%USERPROFILE%\.gemini\antigravity\brain\...` | JSONL |

"Code - Insiders" is probed alongside "Code" for Copilot VS Code.

Antigravity's main session data lives under the `~/.gemini/antigravity/` home dir on every
OS (Windows: `%USERPROFILE%\.gemini\antigravity\`). The Electron app/UI state, indexes, and
cache (`~/Library/Application Support/Antigravity/` on macOS, `%APPDATA%`/`%LOCALAPPDATA%\Antigravity\`
on Windows, `~/.config/antigravity/` + `~/.cache/antigravity/` on Linux) hold no session
transcripts and are not scanned. The per-session `conversations/<id>.db` is a protobuf-blob
SQLite store and is intentionally skipped in favor of the plain-text JSONL transcripts.

Windows notes:

- Tools rooted in `~` (Claude Code, Copilot CLI, Codex) resolve via `%USERPROFILE%` —
  no special handling needed.
- For VS Code-family apps (Code, Cursor, Kiro) the scanner probes the default
  `<home>\AppData\Roaming\<app>\...` AND the `%APPDATA%` env var, in case the
  roaming profile was relocated. Env vars are only consulted when scanning the real
  home directory, so fixture runs (`--home`) stay deterministic.
- OpenCode on Windows usually keeps the XDG-style `\.local\share\opencode` layout
  under the user profile; `%LOCALAPPDATA%`/`%APPDATA%` variants are probed as well.
- Copilot for JetBrains roots at `~/.config/github-copilot` on macOS + Linux but at
  `%LOCALAPPDATA%\github-copilot` (`<home>\AppData\Local\github-copilot`) on Windows; the
  `%LOCALAPPDATA%` env var is honored too, only when scanning the real home.

## Parsing notes per adapter

### claude-code
- One JSONL file per session; line `type` of `user` / `assistant` carries `message.content`
  (string or content-block list), `timestamp` (ISO), `cwd` (project).
- Skips `isSidechain: true` (subagent transcripts) and `isMeta: true` lines.
- User texts starting with `<` (injected command/caveat wrappers) are not counted as prompts.
- Tool calls: assistant content blocks with `type: tool_use` (block `name`).
- Model: assistant lines carry `message.model`; `<synthetic>` entries are ignored.

### claude-cowork
- Claude desktop's local agent mode ("Cowork"). Layout per session under the root:
  `<account-id>/<workspace-id>/local_<session-id>.json` (metadata) plus a sibling
  sandbox dir `local_<session-id>/`.
- Metadata JSON: `sessionId`, `title` (used as project), `model` (may carry a
  context-size suffix like `[1m]`, stripped), `createdAt` / `lastActivityAt` (epoch ms).
- Transcript: `local_<sid>/.claude/projects/<encoded>/<cli-session-id>.jsonl` —
  Cowork runs Claude Code under the hood, so the JSONL is parsed with the exact
  claude-code rules above (multiple JSONL files are merged into the one Cowork session).
- Model comes from transcript `message.model`; the metadata `model` field is the
  fallback when no transcript exists.

### copilot-vscode
- Newer VS Code writes `chatSessions/*.jsonl` as an update log:
  - `kind: 0` -> full state snapshot in `v`
  - `kind: 1` -> set value at path `k` (array)
  - `kind: 2` -> append list items to the array at path `k` (this is how `requests` and
    response parts arrive; a parser that ignores kind 2 sees empty sessions)
- Older releases write plain `chatSessions/*.json` (the snapshot shape directly).
- Per request: `message.text` = user prompt, `response[]` parts: `value` strings are
  assistant markdown, `kind: toolInvocationSerialized` parts are tool calls,
  `result.timings.totalElapsed` (ms) marks turn end.
- Project comes from sibling `workspace.json` (`folder` URI).

### copilot-cli
- Newer builds: one dir per session under `~/.copilot/session-state/<conversationId>/`
  with an append-only `events.jsonl`: `session.start` (cwd, selected model),
  `user.message` (`content` is the clean prompt; `transformedContent` carries the
  injected wrappers, and `<`-leading contents are context injections, not prompts),
  `assistant.message` (`model`, text, `toolRequests`), `tool.execution_start` (one tool
  call, `toolName`), `skill.invoked` (executed skill name). The shared
  `~/.copilot/session-store.db` SQLite (`sessions`: id/cwd/summary + ISO timestamps;
  `turns`: user_message/assistant_response/timestamp) is merged in as a fallback for
  sessions whose session-state dir was pruned — it carries no tool calls or model.
  Dedup by conversation id prefers the events.jsonl variant. Sessions whose
  conversationId a JetBrains Nitrite metadata DB references belong to the IDE and are
  claimed by copilot-jetbrains instead.
- Older builds: `~/.copilot/history-session-state/<session>/*.json`, layout varies by
  version and was not observable during development: the adapter does a tolerant deep
  search for a list of message dicts (`role`/`type` + `content`/`text`) under common
  keys (`messages`, `chatMessages`, `history`, `timeline`, `events`).

### copilot-jetbrains
- GitHub Copilot plugin for JetBrains IDEs (IntelliJ, WebStorm, PyCharm, Rider, Android
  Studio, ...). Root: `~/.config/github-copilot/` (macOS + Linux) or
  `%LOCALAPPDATA%\github-copilot\` (Windows). The user-facing `intellij/` subdir holds
  only config (`global-*-instructions.md`, `mcp.json`) — **no transcripts**. Chat sessions
  live under per-IDE product-code dirs (`iu` IntelliJ, `ws` WebStorm, `py`/`pc` PyCharm,
  `rd` Rider, `ai` Android Studio, ...): `<product>/<*-sessions>/<session-id>/`, holding a
  Xodus `00000000000.xd` and/or a Nitrite `copilot-*-nitrite.db`. The adapter globs both
  `<root>/*/*-sessions/*/00000000000.xd` and `<root>/*/*-sessions/*/copilot-*-nitrite.db`,
  so the old `intellij/`-rooted layout is covered too; the session id is the session dir name.
- `00000000000.xd` is a **JetBrains Xodus** embedded-DB log: binary, Java-serialized, no
  stdlib reader. The adapter is best-effort (like copilot-cli/kiro): it extracts
  ASCII-printable text runs (breaking on control AND high bytes, which Xodus uses as
  length prefixes / record tags) and rebuilds turns from the `query` (user) and `response`
  (assistant) property markers that immediately precede each message's content. Xodus also
  stores a lowercased search-index copy of every string; those are deduped case-insensitively.
- Project: inferred from the common parent dir of the session's `file://` references; if a
  session spans multiple repos the common parent is the home dir and the field is left blank.
- Timestamps: Xodus stores them as binary longs, not decimal strings, so they are not
  recovered — the session uses the `.xd` file mtime as last-activity (window membership)
  and leaves duration unknown.
- Newer agent / edit / chat sessions (`chat-agent-sessions/`, `chat-edit-sessions/`,
  `chat-sessions/`) keep their messages in a sibling **Nitrite** DB
  (`copilot-*-nitrite.db`, Nitrite v4 on an H2 MVStore with Java serialization). The DB
  itself is not stdlib-decodable, but the message payloads are stored as Java-serialized
  UTF strings (TC_STRING `0x74` + u2 length, TC_LONGSTRING `0x7c` + u8 length), so
  `_parse_jetbrains_nitrite` recovers them the same best-effort way as the Xodus path:
  it walks the serialized strings in file order and rebuilds turns from the
  `query`/`response` field markers (the message text is the first content-like string in
  a short lookahead, skipping status/author tokens like `ok` and `GitHub Copilot`).
  Unlike Xodus, the Nitrite log also exposes decimal `created_at` epoch-ms timestamps
  (so real duration + window membership are recovered) and the selected `model` (e.g.
  `auto` for agent sessions; classic chat turns carry none). A session dir can hold both
  a content-bearing Nitrite DB and a metadata-only `.xd`; the adapter keeps whichever
  variant recovered more user messages. For very large agent logs (hundreds of MB) only
  the trailing 96 MB is read — MVStore appends, so the newest (in-window) chunks live
  near the end.
- Plugin 1.13+ delegates agent chat to the embedded Copilot CLI: the per-project
  `copilot-agent-sessions-nitrite.db` then keeps only `NtAgentSession` *metadata*
  (session title, `modelName`, `conversationId`) with no turn text at all — its parse
  yields 0 user messages and the substantive filter drops it. The real turns live in
  the Copilot CLI store (`~/.copilot/session-state/<conversationId>/events.jsonl` +
  `session-store.db`); the adapter recovers each `conversationId` from the Nitrite
  metadata, claims the matching CLI sessions, and re-attributes them to
  copilot-jetbrains (`scan_copilot_cli` skips those same ids, so nothing is counted
  twice).
- The top-level `~/.config/github-copilot/copilot-intellij.db` and `auth.db` are plain
  SQLite stores (UI state / auth, e.g. a single `mcp-first-boot-completed` flag) — they
  hold NO chat transcripts and are intentionally not scanned. The `bg-agent-sessions/`
  `copilot-session-metadata.db` / `copilot-agent-snapshots.db` hold only background-agent
  bookkeeping and file snapshots, likewise skipped (the `copilot-*-nitrite.db` glob
  excludes them).

### cursor
- Everything in globalStorage `state.vscdb`, table `cursorDiskKV`:
  - `composerData:<composerId>`: session metadata (`createdAt`/`lastUpdatedAt` epoch ms,
    `name`, `fullConversationHeadersOnly` = ordered bubble refs)
  - `bubbleId:<composerId>:<bubbleId>`: one message; `type` 1 = user, 2 = assistant;
    `text` = content; `toolFormerData.name` = tool call
- No per-bubble timestamps: duration = wall-clock span capped at 8h.
- SQLite gotcha: bubble lookups need a second cursor; reusing the iterating cursor
  resets the outer query.

### codex
- One `rollout-*.jsonl` per session. `type: session_meta` payload gives id/cwd/start.
- `type: event_msg` payloads: `user_message` / `agent_message` (plain `message` string).
- `type: response_item` payload `function_call` = tool call (`name`).

### kiro
- VS Code fork; agent chat state lives in per-workspace `state.vscdb` `ItemTable`
  (keys like `kiro.kiroAgent`). Format is undocumented: the adapter deep-searches values
  for message lists, best effort.

### opencode
- Newer builds: `opencode.db` tables `session` (id, directory, title, time_created/updated
  ms, parent_id), `message` (`data` JSON: role, time.created), `part` (`data` JSON:
  type text/tool, `text`, `tool`). Sessions with `parent_id` are subagent children and
  skipped. The db is read first; JSON file storage is merged in, deduped by session id.
- Older builds: `storage/session/**/ses_*.json`, `storage/message/<sid>/*.json`,
  `storage/part/<msgid>/*.json`.

### antigravity
- Gemini IDE. One session per dir under `brain/`; the session id is the dir name. Each
  `transcript*.jsonl` is one JSON object per step: `source` (`USER_EXPLICIT` / `MODEL` /
  `SYSTEM`), `type`, `created_at` (ISO), and optional `content` / `thinking` / `tool_calls`
  / `error`. `transcript_full.jsonl` (untruncated) is preferred over `transcript.jsonl`.
- User prompts: `USER_INPUT` rows; the real text is unwrapped from `<USER_REQUEST>...</USER_REQUEST>`
  (the surrounding `<ADDITIONAL_METADATA>` / `<USER_SETTINGS_CHANGE>` blocks are dropped).
- Assistant turns: `PLANNER_RESPONSE` rows — `content` is the reply text, `tool_calls[]`
  (`{name, args}`) are the tool calls. `SYSTEM`/`EPHEMERAL_MESSAGE` reminders and the
  `MODEL` tool-result rows (`VIEW_FILE`, `GREP_SEARCH`, `LIST_DIRECTORY`, ...) are ignored
  so tools aren't double-counted.
- Project: transcripts carry no cwd, so it's inferred as the common parent dir of the
  absolute paths in tool-call args (`AbsolutePath` / `DirectoryPath` / `SearchPath`, whose
  values are JSON-encoded strings and are de-quoted first).
- Model: Antigravity exposes models as display names. A `<USER_SETTINGS_CHANGE>` model
  switch yields both the prior and new model (slugified, dropping the `(Thinking)`/`(Low)`
  reasoning-effort qualifier, e.g. `claude-sonnet-4-6`, `gemini-3-1-pro`). When a session
  has no switch, the machine id from any `ERROR_MESSAGE` (`...model <id> on the server`) is
  the fallback; sessions with neither record no model.

## Shared rules

- Window prefilter by file mtime, then by parsed timestamps (`end_ts >= now - days`).
- SQLite opened read-only (`mode=ro`); on lock failure the db (+`-wal`/`-shm`) is copied
  to a temp dir and the copy is read.
- Malformed JSON/JSONL entries are skipped, never fatal. A whole-adapter crash prints a
  warning to stderr and the scan continues with the other adapters.
- Substantive filter: >= 1 user message, and active duration >= 1 minute (unknown
  duration passes). Active duration = sum of inter-message gaps capped at 30 min, so
  resumed multi-day sessions don't inflate hours.
- Dedup by (tool, session id), keeping the variant with the most user messages.
- Self-exclusion: transcripts whose first 4000 chars contain the facet-extraction marker
  strings are insight-analysis sessions (this skill's own runs or builtin /insights) and
  are dropped.
- Transcript normalization: `[User]:` lines truncated to 500 chars, `[Assistant]:` to
  300 chars, `[Tool: name]` markers; per-session transcript capped at 30k chars.
- Models: each session records a `models` map (model name -> use count) where the source
  exposes it — claude-code/claude-cowork `message.model`, copilot-vscode request
  `modelId`, cursor composer `modelConfig.modelName`, codex `turn_context` payload
  `model`, opencode message `modelID`, antigravity `<USER_SETTINGS_CHANGE>` switch /
  `ERROR_MESSAGE` machine id, generic adapters (copilot-cli, kiro) any
  `model`/`modelId`/`modelID` message key. copilot-jetbrains classic Xodus chat logs carry
  no recoverable model id; the Nitrite agent logs do expose a selected model (e.g. `auto`)
  via the `model`,<value>,`modelProviderName` token triple, and CLI-backed sessions
  (plugin 1.13+) get per-message models from events.jsonl `assistant.message`.
  Aggregation counts sessions per model.
- Skill invocations: each session records a `skill_invocations` map (skill name -> count).
  Three sources feed it. (1) claude-code / claude-cowork: the `Skill` tool (assistant
  `tool_use` block named `Skill`), with the name read from its input (`skill` / `command`).
  (2) cursor / opencode: a leading `/name` slash command in the user's message text — how
  skills are invoked there (a real-log probe found these tokens are overwhelmingly installed
  skills). The `/name` must be followed by whitespace/colon/end, so file paths (`/Users/...`,
  `/dev/null`) are not miscounted. The name is stored without the slash, so `/spec-lint` and
  the `spec-lint` `Skill` tool call merge into one skill across tools. (3) copilot-cli
  and CLI-backed copilot-jetbrains sessions: `skill.invoked` events in events.jsonl
  carry the executed skill's name directly. Other adapters (codex, copilot-vscode, kiro,
  antigravity) contribute none: codex expands custom prompts before logging (the `/name`
  is lost) and the rest expose no reliable per-invocation marker.
  Aggregation sums invocations into a per-tool total and a `skills_used` distribution.
