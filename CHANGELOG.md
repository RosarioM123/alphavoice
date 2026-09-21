# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.3.0] - 2026-09-20

### Added
- `docs/sample-utterances.md`: a "try saying..." list mapped to the web demo's
  chips, so a judge can drive the demo in 30 seconds.
- `docs/speech-examples.md`: before/after pairs of raw quant output versus the
  spoken summary each tool returns.
- `docs/performance.md`: per-tool latency benchmark table measured on local
  synthetic fixtures.
- `docs/security.md`: paper-only guarantee (no order paths, no keys, no
  execution code), input validation, and the threat model.

## [1.2.0] - 2026-09-19

### Added
- `docs/architecture.svg`: voice to Alexa+ agent to MCP server to three engines
  to spoken answer, referenced from the README.
- README badges: CI status, MIT license, Python 3.12.
- `docs/adr/`: five numbered architecture decision records (MCP over custom API;
  narrow typed tools; summary/detail contract; honest numbers or silence;
  simulated web experience).
- `docs/alexa-integration.md`: the path from the simulated web experience to a
  production Alexa+ agent or skill.

## [1.1.0] - 2026-09-18

### Added
- Fourth MCP tool `market_brief`: composes the three quant engines into one
  spoken verdict; centerpiece of the demo.
- Tool-routing eval harness wired into CI: 15/15 utterances routed to the
  correct tool (macro F1 1.000).
- Browser SpeechSynthesis (TTS) controls in the simulated web experience.
- Fixed spoken number formatting that rounded 29.7 to "about 3" (recorded in
  `docs/friction-log.md`).

## [1.0.0] - 2026-09-18

### Added
- MCP server (spec 2025-11-25, Streamable HTTP) over three quant engines:
  `signal_scan` (six signal families plus ridge combiner), `mispricing_check`
  (Polymarket/Kalshi full-book VWAP, fractional Kelly, paper only),
  `news_microstructure` (Hawkes news-to-price impact fit).
- Speakable summary plus detail payload contract on every tool.
- Simulated web experience (`web/`) with demo chips and a spoken demo script
  (`docs/demo-script.md`).
- CI workflow: pytest suite plus MCP server smoke test, with the SIGNAL and
  ODDS engine repos cloned as siblings.
