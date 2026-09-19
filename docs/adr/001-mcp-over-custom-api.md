# ADR 001: MCP over a custom API

Date: 2026-09-18
Status: Accepted

## Context

The quant engines (SIGNAL, ODDS, Hawkes) already existed as plain Python
libraries. To expose them to an Alexa+ agent we needed a remote protocol.
Two options were on the table: a bespoke REST API we design ourselves, or
the Model Context Protocol (MCP), a standard the Alexa+ track explicitly
encourages.

## Decision

We built the server on the official MCP Python SDK, spec 2025-11-25, over
Streamable HTTP at `/mcp` (see `server/mcp_server.py`). No custom HTTP
endpoints exist; the tools are declared with JSON Schema generated from
Python type annotations.

## Consequences

- The server is agent-agnostic. Any MCP client, not just our agent, can
  discover and call the tools.
- Hosting is ordinary: any always-on Python host that can serve HTTPS works,
  which keeps the free-infrastructure story intact.
- We inherit the MCP SDK's rough edges (logged in `docs/friction-log.md`
  and `docs/product-feedback.md`) instead of owning our own protocol's.
- The voice demo needed a client, so we also built the thin simulated web
  experience in `web/` rather than claiming a live Alexa+ integration (see
  ADR 005).
