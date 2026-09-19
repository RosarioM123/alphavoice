# ADR 004: Honest numbers or silence

Date: 2026-09-18
Status: Accepted

## Context

Quant tools fail loudly in demos: missing data, a mis-specified parameter,
or an engine that raises. A voice assistant that invents a number to fill
the silence is worse than one that admits it has nothing. The ODDS adapter
exposed this concretely: `size_position` raises unless `fraction` is one of
(0.25, 0.50, 1.00), and its `p_win` defaults to a hardcoded 0.55
placeholder.

## Decision

- `no_data_result()` in `server/tools/contract.py` is the only acceptable
  empty path: low confidence, a plain-spoken reason, and an offer to retry.
- The contract requires `simulated` results to say so in `data_freshness`;
  the validator raises otherwise.
- Adapters never silently substitute assumptions: the ODDS adapter passes
  `p_win=0.55` explicitly with `p_win_is_placeholder=True` and labels it an
  assumption in `data_freshness` and `detail`.
- `mispricing_check` is paper only: it reports hypothetical Kelly sizes and
  there are no order paths, venue clients, or API keys in the repo.

## Consequences

- Judges can trust that any number they hear was computed, and that
  assumptions are labeled where they are heard.
- The 30-second spoken budget never competes with honesty: silence is one
  sentence, delivered in the same shape as a real answer.
- This rule is load-bearing for the mispricing tool in particular, where
  the placeholder probability could otherwise masquerade as an estimate.
