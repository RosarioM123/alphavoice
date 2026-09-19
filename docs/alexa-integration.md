# Alexa+ integration guide: from the web simulation to production

This document describes how a real Alexa+ agent or custom skill would connect
to the AlphaVoice MCP server. The current repo ships a simulated web
experience (`web/`) as a stand-in for the Alexa+ agent; everything below is
the production path it is standing in for.

Status: design documented, not yet tested against Alexa+ developer tooling.
Anything marked unverified is an honest gap, not a claim.

## What the server already exposes

- `server/mcp_server.py` serves the official MCP Python SDK server
  `MCPServer("alphavoice")` over Streamable HTTP at `/mcp` (MCP spec
  2025-11-25). Default: `http://localhost:8000/mcp`.
- Four tools with JSON Schema generated from Python type annotations:
  `signal_scan`, `mispricing_check`, `news_microstructure`, `market_brief`.
- Every tool returns the summary/detail contract (`server/tools/contract.py`):
  a speakable one-sentence `summary.verdict`, rounded `key_numbers` with
  exact `value`s, qualitative `confidence`, a `data_freshness` string, and
  a follow-up `offer`, plus the full `detail` payload and a `simulated`
  boolean.

A production integration does not change the server. It adds a client that
speaks MCP and a voice layer that reads the contract.

## Step 1: host the MCP server with HTTPS

The Streamable HTTP transport is designed for remote, self-hosted servers.
Any always-on Python host works; the only requirements are:

1. `pip install -r requirements.txt` and `python -m server.mcp_server`.
2. A public HTTPS URL, e.g. `https://alphavoice.example.com/mcp`.
3. Optional bearer-token auth in front of `/mcp` (the paper data needs no
   secrets, so this is abuse control, not credential protection).

## Step 2: connect an Alexa+ agent as an MCP client (preferred)

If the Alexa+ agent supports remote MCP servers, point it at the hosted
`/mcp` URL. Tool discovery is automatic: the agent calls `tools/list`,
receives the four tool schemas and descriptions, and selects tools from
natural utterances, exactly as the routing eval measures in `evals/`.

Utterance to tool mapping for the demo intents:

| Say | Tool | Spoken from |
|---|---|---|
| "Morning brief roundup: CPI print, anything mispriced, today's signals" | `market_brief` | `summary.verdict` of the composed brief |
| "How fast did the market absorb the CPI print?" | `news_microstructure` | half-life and regime from `summary` |
| "Anything mispriced between Polymarket and Kalshi?" | `mispricing_check` | net edge and Kelly size, paper only |
| "Any unusual signals today?" | `signal_scan` | top-ranked symbol and expected return |

Rendering rule for the voice layer: speak `summary.verdict`, offer the
`summary.offer` as the follow-up prompt, and expand `detail` when the user
says "tell me more". This is the same rule the web sim follows, so the
behavior judges see in the simulation is the behavior the skill would
produce.

## Step 3 (fallback): a custom skill with an MCP client backend

If native MCP support is unavailable, a custom Alexa skill can act as the
MCP client:

1. Define four intents matching the tool schemas above, with slot types
   for `symbols`, `horizon_days`, `size`, and `window_minutes`.
2. The skill backend (e.g. AWS Lambda) posts JSON-RPC to the hosted
   `/mcp` endpoint and parses the summary/detail contract.
3. Speak `summary.verdict` as SSML, rounding handled server-side by
   `speak_number`, so the skill reads `key_numbers[].spoken` verbatim.
4. Map `summary.offer` to a reprompt so the conversation stays open.

This path is more code for the same result and should be treated as a
fallback to option 2.

## Step 4: swap simulated data for live data

The simulation is honest about its inputs today. To go live, change only
the three synthetic factories, one per adapter
(see `server/adapters/README.md`):

- `make_synthetic_panel` (signal_adapter): point at a real price/volume
  feed.
- `make_synthetic_books` (odds_adapter): point at the Polymarket and Kalshi
  order books.
- `simulate_streams` (hawkes_adapter): point at a real news/event stream.

Then set `simulated` to False and write a real freshness string in the
tool. Everything downstream keeps working; the speech contract does not
change.

## Unverified items

- End-to-end certification of a real Alexa skill or Alexa+ agent against
  this server has not been performed in this repo.
- Bearer-token auth on `/mcp` is recommended but not implemented; the
  server currently assumes a trusted network.
- Latency over a real network hop has not been measured; local per-tool
  timings belong in `docs/performance.md` once they exist.
