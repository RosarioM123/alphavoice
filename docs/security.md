# Security: nothing to steal, nothing to execute

AlphaVoice is safe to demo because of what it does not have. This page
documents the paper-only guarantee, the validation on every tool input, and
the threat model, so a judge can verify the claims instead of taking them
on trust.

## Paper only, by construction

There is no order path in this repo. Nothing to audit, nothing to disable:

- No function places, routes, or signs orders. The only size math is the
  fractional-Kelly sizer in `mispricing_check`, which returns a
  `hypothetical_quantity` labeled `paper_only` in every response.
- No venue API keys exist anywhere: not in code, not in config, not in CI.
  The tools read synthetic fixtures from local sibling repos
  (`SIGNAL_ROOT`, `ODDS_ROOT`), which are directory paths, not credentials.
- A repo-wide grep for `api_key`, `secret`, `bearer`, and `sk-` matches only
  third-party library internals in `.venv` (checked 2026-09-20). If a key
  ever appears in this project, it is a bug; file it as one.

## Input validation

Every tool validates before it computes. Bad input returns the honest-silence
response (confidence low, empty key numbers), never a stack trace:

| Tool | Check | Bad input behavior |
|---|---|---|
| `signal_scan` | At least one ticker symbol; `horizon_days > 0`; `top_n` clamped to >= 1 | `no_data_result` naming the missing input |
| `mispricing_check` | `kelly_fraction` must be in {0.25, 0.50, 1.00} | `no_data_result` naming the allowed values |
| `news_microstructure` | `window_minutes` passed to the adapter, which rejects non-positive windows | `no_data_result` |
| `market_brief` | Inherits the three checks above; composition never overrides a silence | A failing tool yields a silent clause, not a fabricated one |

Tool inputs are typed (strings, floats, ints) over the MCP schema, so the
agent cannot smuggle in objects, callbacks, or shell text. Nothing in the
tool code calls `eval`, `exec`, `subprocess`, or the network.

## Network posture

- The MCP server binds to `127.0.0.1` (`server/mcp_server.py`). It is not
  reachable from the network unless the operator puts a reverse proxy in
  front of it, which is the documented Alexa+ path
  (see `docs/alexa-integration.md`).
- The tool code makes zero outbound network calls. All data comes from the
  synthetic fixtures on local disk.
- MCP authorization is the SDK's standard bearer-token support; this repo
  ships no default token. A production deployment must add TLS and its own
  token at the proxy. The local dev server is unauthenticated by design, the
  same way a local database is: it listens on loopback and expects a trusted
  machine.

## Threat model

| Threat | Assessment |
|---|---|
| Prompt injection steering a tool into a bad action | The tools have no actions. The worst a hostile prompt can produce is a misleading spoken sentence, and the summary/detail contract always keeps the raw numbers one question away for verification. |
| Malformed or adversarial tool input | Handled by the validation table above; the contract guarantees a shaped response or silence, never an exception to the agent. |
| Resource exhaustion (huge symbol lists, huge windows) | Inputs are small by schema (`top_n`, `horizon_days`, `window_minutes`); a single machine serves one demo session. No rate limiting is built in, which is fine for a loopback demo server and documented as an operator concern for hosted use. |
| Secret leakage through logs or errors | There are no secrets to leak. Detail payloads contain only synthetic market numbers. |
| Real-money confusion | Every size is labeled hypothetical and paper only, in the tool description, the verdict text, and the `detail` payload. Simulated data is labeled simulated in every response. |

## What this document does not claim

This is a hackathon demo server, not hardened infrastructure. It has not had
a third-party audit, and the hosted path inherits the security of whatever
proxy the operator chooses. The guarantees above are narrow and checkable:
no execution code, no keys, validated inputs, loopback by default.
