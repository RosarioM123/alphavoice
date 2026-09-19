# Friction log

What it is: a running list of every point of friction hit while building with the hackathon's provided tools and platforms (MCP SDK, transports, Alexa+ dev tooling, hosting). Why it exists: the hackathon awards up to a 10 percent judging bonus for honest friction reporting, and these entries feed the Challenges section of the final submission. Builders append entries as they happen.

## Template

Copy the block below for each new entry. Be concrete: what you tried, what failed, and what you did about it.

```
### <date, e.g. 2026-09-18> — <short title>

- Context: <what you were building or testing when it happened>
- Tried: <the exact step that hit friction>
- Result: <what failed or behaved unexpectedly>
- Workaround: <what you did instead, or "none yet">
- Impact: <minutes lost, or blocked/not blocked>
```

## Entries

### 2026-09-18 — Web client: MCP server command not yet known at build time

- Context: building the simulated Alexa+ web experience in `web/`, which must tell the user how to start the MCP server when it is not running.
- Tried: looked for the server entrypoint; `server/` contained only empty `tools/` and `adapters/` dirs, and `server/main.py` did not exist yet (sibling agent still building).
- Result: could not confirm the exact run command from code, only from the sibling agent's README (`python -m server.main` from `~/workspace/alphavoice`, port 8000).
- Workaround: the "server not reachable" banner quotes the README's command. If the server agent changes the entrypoint, this copy goes stale.
- Impact: not blocked; parent should confirm the final command before the demo video.

### 2026-09-18 — Web client: tool input schemas unknown, arguments built generically

- Context: the web client must call `signal_scan`, `mispricing_check`, `news_microstructure` via `tools/call`, but the tool schemas did not exist yet at build time.
- Tried: nothing to read; schemas are defined by the sibling agent's in-progress server.
- Result: hard-coding argument shapes would have been guessing.
- Workaround: the client fetches `tools/list` at startup and builds arguments from each tool's `inputSchema` at runtime (string fields that look like a question slot get the user's question; other required fields get neutral defaults). Verified against a throwaway stub server with plausible schemas; will work with the real schemas as long as they are standard JSON Schema.
- Impact: not blocked; if a tool requires a non-string argument with domain meaning (e.g. a ticker), the generic default may be wrong and the tool should return an honest error, which the UI renders as-is.

### 2026-09-18 — Web client: Streamable HTTP response shape (JSON vs SSE)

- Context: per the MCP spec, a Streamable HTTP server may answer a POST with plain JSON or with `text/event-stream` SSE. The sibling server implementation was not finished, so its choice was unknown.
- Tried: read the spec and the `mcp` Python SDK conventions (single POST `/mcp`, `Accept: application/json, text/event-stream`, `Mcp-Session-Id` header).
- Result: had to support both shapes without knowing which the server uses.
- Workaround: the client inspects `Content-Type` and parses either plain JSON or SSE `data:` lines; protocol version negotiation tries `2025-11-25` (per the project README) then falls back to `2025-06-18` and `2024-11-05`. Verified the SSE path against a stub; the plain-JSON path follows the same JSON-RPC envelope.
- Impact: not blocked.

### 2026-09-18 — Web client: no headless browser in this VM for screenshots

- Context: wanted to screenshot the page for visual verification.
- Tried: looked for chromium / google-chrome binaries.
- Result: none installed; installing a browser just for a screenshot was out of proportion.
- Workaround: verified with (1) `node --check` on app.js, (2) HTML well-formedness via `html.parser`, (3) a Node harness that loaded the real app.js and ran the full MCP handshake (initialize, tools/list, tools/call) against a throwaway stub server on :8000, covering routing, argument building, SSE parsing, answer extraction, and error paths: 26/26 checks passed. CSS brace balance and JS/HTML id cross-checks also passed.
- Impact: not blocked; visual polish still unreviewed, recommend a human glance before recording.

### 2026-09-18 — MCP SDK 2.x renamed FastMCP and client helper

- Context: building the AlphaVoice MCP server against a fresh `pip install mcp`.
- Tried: `from mcp.server.fastmcp import FastMCP` (the v1 import path).
- Result: ModuleNotFoundError. mcp 2.2.0 renamed FastMCP to `mcp.server.mcpserver.MCPServer`, and the client helper is `streamable_http_client` (was `streamablehttp_client`).
- Workaround: import from `mcp.server.mcpserver`; serve via `MCPServer.streamable_http_app(streamable_http_path="/mcp")` under uvicorn. Tool definitions via `@mcp.tool(...)`; registry checked with `await mcp.list_tools()`.
- Impact: ~15 minutes; not blocked.

### 2026-09-18 — tick installed cleanly on Python 3.12 (expected failure did not happen)

- Context: recon warned `tick` (compiled C++) might not install on Python 3.12.
- Tried: `pip install tick` in the project venv.
- Result: installed tick 0.8.0.2 from a prebuilt wheel on the first try. So `news_microstructure` uses the real `tick.hawkes.HawkesExpKern` maximum-likelihood fit on synthetic streams; no simulated-path fallback was needed.
- Workaround: none needed.
- Impact: not blocked.

### 2026-09-18 — Did not import hawkes_fit.py (import-time side effects)

- Context: wiring the Hawkes microstructure adapter.
- Tried: reading `~/workspace/hawkes/hawkes_fit.py` for the metric computation.
- Result: the module simulates, fits, and prints at import time, so importing it would run a demo on every server start.
- Workaround: vendored only the metric math (alpha_10 = alpha[1,0], half-life = ln(2)/beta, spectral radius of alpha for sub-critical vs explosive regime) in `server/adapters/hawkes_adapter.py`, following the user's code. Documented in `server/adapters/README.md`.
- Impact: not blocked.

### 2026-09-18 — ODDS sizer guards: kelly fraction set and p_win placeholder

- Context: wiring `backend.arbitrage.sizing.size_position`.
- Tried: calling it with an arbitrary fraction.
- Result: it raises unless `fraction` is one of (0.25, 0.50, 1.00); `p_win` defaults to a hardcoded 0.55 placeholder.
- Workaround: the adapter validates `kelly_fraction` upfront (honest silence on bad input), passes `p_win=0.55` explicitly with `p_win_is_placeholder=True`, and labels it an assumption in `data_freshness` and `detail`.
- Impact: not blocked.

### 2026-09-18 — Server entrypoint differs from what web/ expects

- Context: `web/` quotes `python -m server.main` as the server start command, but the server entrypoint is `server/mcp_server.py` (`python -m server.mcp_server`).
- Tried: n/a, found while reading the shared friction log.
- Result: mismatch between the two agents' assumptions.
- Workaround: added a thin `server/main.py` shim that re-exports `mcp_server.main`, so both commands work. Parent should confirm the canonical command for the demo.
- Impact: not blocked.

### 2026-09-18 — tick 0.8.0.2 learner/model constructors broken (missing attr registry)

- Context: wiring `news_microstructure` to the real `tick.hawkes.HawkesExpKern` fit.
- Tried: `HawkesExpKern(decays=2.0, ...)` then `.fit(timestamps)`.
- Result: `AttributeError: 'HawkesExpKern' object has no settable attribute 'events'` at construction, then the same class of failure for `dtype` on the model/solver classes (`ModelHawkesExpKernLeastSq`, `AGD`, `ProxL2Sq`, `History`, ...). The BaseMeta metaclass rejects attributes its own constructors set because the docstring-scraped attr registry is missing them (e.g. `events` and `dtype` are documented but absent). Also `SimuHawkesExpKern` was renamed to `SimuHawkesExpKernels` in this version.
- Workaround: `server/adapters/hawkes_adapter.py` registers each missing attribute into the class's `_attrinfos` at runtime (bounded retry loop, `_repair_from_error`), preferring the BaseMeta-managed Python wrapper over the raw pybind11 binding. The real tick maximum-likelihood fit then runs and recovers the planted parameters. Logged here rather than fixed upstream: it is a vendored-environment quirk, not our code.
- Impact: ~45 minutes; not blocked.

### 2026-09-18 — httpx2 proxy handling chokes on bracketed IPv6 in no_proxy

- Context: end-to-end test of the MCP client over Streamable HTTP to localhost.
- Tried: `streamable_http_client("http://127.0.0.1:8123/mcp")` with the sandbox proxy env vars set (`no_proxy` includes `[::1]`).
- Result: `httpx2.InvalidURL: Invalid port: ':1]'` (scheme parsed as `all`): httpx2 turns the `no_proxy` entry `[::1]` into a mount pattern `all://*[::1]` whose naive URL split breaks.
- Workaround: tests pass a pre-configured `httpx2.AsyncClient(trust_env=False)` to `streamable_http_client`; the server subprocess gets a proxy-stripped env. Localhost traffic never needed the proxy.
- Impact: ~20 minutes; not blocked.

### 2026-09-18 - speak_number mangled values that round to trailing zeros

- Context: building the composed `market_brief` verdict, which renders the Hawkes half-life through the shared speech-rules helper in `server/tools/contract.py`.
- Tried: `speak_number(29.7)` for a half-life of 29.7 seconds.
- Result: returned "about 3" instead of "about 30". The `.rstrip("0")` meant for decimal tails was also stripping integer zeros, so any value rounding to 30, 100, 250, etc. lost a digit. This would have corrupted the spoken brief ("about 3 seconds" for a 30-second half-life).
- Workaround: fixed `speak_number` to strip trailing zeros only when a decimal point is present. All existing contract tests still pass; added regression coverage in `tests/test_compose.py` via the shared precision helpers.
- Impact: ~20 minutes; not blocked. The bug lived in shared contract code, not just the new path.

### 2026-09-18 - Eval keyword lists had to drop generic tokens to protect honest silence

- Context: building the tool-routing eval (`evals/`), which scores routing on 15 questions including out-of-scope ones that must route to no tool.
- Tried: first keyword lists included "today" and "news".
- Result: they fire on nearly any phrasing ("what's the weather today" matched a tool), which would break the honest-silence cases the eval is supposed to prove.
- Workaround: removed "today" and "news" from the eval router's keyword lists, and added "position" to `mispricing_check` so "my prediction-market position" routes without needing the literal phrase "paper position". Documented in the router docstring and the eval report notes.
- Impact: not blocked. Deliberate difference from `web/app.js`: the web sim falls back to `signal_scan` on zero keyword hits, while the eval router returns the empty set. The demo narrative must not claim the two agree on out-of-scope questions.

### 2026-09-18 - TTS: no headless browser in this environment, so no real playback test

- Context: adding SpeechSynthesis read-aloud buttons and an auto-speak toggle to `web/`.
- Tried: looked for chromium, google-chrome, firefox in PATH and /usr/bin.
- Result: none present. The page was never loaded in a real browser, so observer-driven button rendering, voice selection, and actual utterance playback are unverified in practice.
- Workaround: `node --check` passes on `web/tts.js`, plus a static review (every referenced id/class exists, observer guards against double-attachment, graceful degradation when `speechSynthesis` is missing). The user must click a speak button once during the demo recording to confirm audio works in their browser.
- Impact: not blocked, but flag for demo prep. Related quirk: Chrome may silently block `speechSynthesis.speak()` without a prior user gesture, so the auto-speak toggle is only meaningful after the user has interacted with the page. Also, `app.js` already fakes a "Speaking..." ring glow on a timer; that timing was deliberately left untouched.

(No entries yet. Append new incidents above this line using the template.)

## 2026-09-18, coordinator verification
- Snag: verifying the live server with the stock MCP Python client crashed on `httpx2.InvalidURL: Invalid port: ':1]'`. Root cause: the sandbox sets a `no_proxy`/`NO_PROXY` env var containing bracketed `[::1]`, which httpx2's URLPattern parser cannot parse. This is the same issue the server builder logged; it affects any MCP client run in this environment, not just tests.
- Workaround: run clients with `trust_env=False` (e.g. `httpx.AsyncClient(trust_env=False)` passed as `http_client` to `streamable_http_client`), which bypasses proxy env parsing entirely. Verified: full initialize, tools/list, and tools/call round-trip for all three tools then succeeded.
- Note for the demo: on machines without this proxy quirk the stock client works unmodified; no repo code change was needed.
