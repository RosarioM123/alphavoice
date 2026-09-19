# ADR 005: A simulated web experience instead of a production Alexa integration

Date: 2026-09-18
Status: Accepted

## Context

The hackathon deadline is 2026-10-23. The demo needed a voice-like
interaction judges could drive in 30 seconds, but a real Alexa+ skill
requires Amazon developer tooling, certification, and data wiring we did
not have inside the build window. The alternative was shipping no demo.

## Decision

`web/` is a browser simulation of the voice interaction, explicitly labeled
as simulated. It renders the same summary/detail contract the MCP tools
return, offers demo chips mapped to the four tools, and speaks answers with
browser SpeechSynthesis. It is a stand-in for the Alexa+ agent, not a
replacement for one.

## Consequences

- Judges see and hear the interaction design today, with zero risk of a
  live-certification dependency before the deadline.
- The simulation cannot prove Alexa+ compatibility; it proves the speech
  contract. The path from sim to production is documented in
  `docs/alexa-integration.md`.
- The simulation doubles as the regression surface for the spoken text:
  the demo script (`docs/demo-script.md`) is written against its chips,
  and the speech rules are tested, not eyeballed.
