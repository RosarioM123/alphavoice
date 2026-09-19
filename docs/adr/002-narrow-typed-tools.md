# ADR 002: Narrow typed tool interfaces

Date: 2026-09-18
Status: Accepted

## Context

An Alexa+ agent picks tools from their descriptions and schemas mid-conversation.
Broad, many-parameter tools are hard to route reliably and invite hallucinated
arguments. The tool-routing eval (`evals/`) exists to measure exactly this.

## Decision

Four tools, each with a small typed input surface:

- `signal_scan(query, symbols, horizon_days, top_n)`
- `mispricing_check(query, size, bankroll, kelly_fraction)`
- `news_microstructure(query, window_minutes)`
- `market_brief(query)` - the composed path, runs the other three in-process

Each description names the engine, the math, and the paper-only guarantee
where relevant. Sensible defaults cover the demo so the agent rarely needs
to fill arguments.

## Consequences

- The routing eval scores 15/15 (macro F1 1.000) on the demo question set,
  wired into CI so a schema change that breaks routing fails the build.
- The composed `market_brief` gives the agent one button for the flagship
  demo turn, while the three primitive tools stay available for follow-ups.
- Adding a fifth tool later is cheap, but every new tool dilutes routing
  confidence, so the bar for a new tool is high.
