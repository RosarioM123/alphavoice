# Product feedback: MCP Python SDK and Streamable HTTP transport

**Status: DRAFT.** This document is a scaffold for the user to finalize after real usage of the MCP Python SDK during this build. Nothing below reports firsthand experience; every section is pre-labeled with what it is based on. Sections marked "to fill after usage" must be completed by the person who actually built with the SDK.

## 1. MCP Python SDK

**Used for:** implementing the AlphaVoice MCP server, defining the three tool schemas (signal_scan, mispricing_check, news_microstructure), and serving them over the Streamable HTTP transport.

**What worked:** (to fill after usage)

- Publicly documented facts we relied on going in: the Python SDK provides low-level and FastMCP high-level server builders, JSON Schema-based tool definitions generated from Python type annotations, and lifecycle management over stdio, SSE, and Streamable HTTP transports.

**What needs work:** (to fill after usage)

**Onboarding feel:** (to fill after usage)

**Would-build-again verdict:** (to fill after usage)

## 2. Streamable HTTP transport

**Used for:** hosting the AlphaVoice server as a self-hosted endpoint reachable by an Alexa+ agent, instead of running the server in-process or over stdio.

**What worked:** (to fill after usage)

- Publicly documented facts we relied on going in: the Streamable HTTP transport (specified in MCP spec 2025-11-25) carries JSON-RPC messages over HTTP POST with optional server-sent event streams for server-initiated messages, and supports session IDs for stateful conversations. It is the transport intended for remote, self-hosted MCP servers.

**What needs work:** (to fill after usage)

**Onboarding feel:** (to fill after usage)

**Would-build-again verdict:** (to fill after usage)

## 3. Overall assessment (to fill after usage)

- Summary:
- Top request for the SDK maintainers:
- Top request for the spec/transport maintainers:
