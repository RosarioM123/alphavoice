# Adapters: how AlphaVoice talks to the user's quant engines

Thin wrapper modules only. No engine code is copied into this repo; each
adapter adds the engine repo's root to `sys.path` and imports its public
entry points (verified clean imports, no import-time side effects).

## SIGNAL (`~/workspace/signal-build`)

`adapters/signal_adapter.py` imports:

- `signals.momentum.momentum_features(prices, volumes)`
- `signals.mean_reversion.mean_reversion_features(prices, volumes)`
- `signals.volatility.volatility_features(prices)`
- `signals.volume.volume_features(prices, volumes)`
- `signals.xsectional.xsectional_features(prices)` (needs a SPY column; the adapter appends one)
- `signals.regime.regime_features(prices)`
- `models.combine.RidgeCombiner(alpha=1.0)` with `.fit(X, y)`, `.predict(X)`, `.standardized_coefs()`

Inputs are DataFrames with chronological rows and ticker columns. Each
family returns a MultiIndex-column panel (feature x symbol); the adapter
reshapes per symbol (stack/groupby) and stacks families into one design
matrix, then fits the ridge combiner against forward returns. Runtime deps:
numpy, pandas, pyyaml (all in requirements.txt).

Because no live market feed is attached, the adapter generates a small
deterministic synthetic price/volume panel (seed 7) in
`make_synthetic_panel`. Every number downstream of it is labeled
`simulated: true`. The signal-family and combiner code paths are the real
ones.

## ODDS (`~/workspace/odds-prediction-mispricing`)

`adapters/odds_adapter.py` imports:

- `backend.schemas.OrderBook`, `OrderBookLevel`, `Market`, `Venue`, `Outcome`
- `backend.arbitrage.costs.walk_book(book, side, size)` -> full-book VWAP
- `backend.arbitrage.costs.FeeModel().taker_fee(market, contracts, price)`
- `backend.arbitrage.costs.half_spread_cost(book)` (spread is informational)
- `backend.arbitrage.costs.build_cost_breakdown(...)` -> `.net_edge`
- `backend.arbitrage.sizing.size_position(...)` -> fractional Kelly size

`size_position` requires `fraction` in (0.25, 0.50, 1.00) and raises
otherwise; `p_win` defaults to a hardcoded 0.55 placeholder, so the adapter
passes it explicitly and labels it an assumption in `data_freshness` and
`detail`. The two book views come from a synthetic two-venue fixture in
`make_synthetic_books` (labeled simulated).

PAPER ONLY: the adapter computes a hypothetical size and reports it. There
are no order paths, no venue clients, and no API keys anywhere in this repo.

## Hawkes microstructure (`~/workspace/hawkes`)

`adapters/hawkes_adapter.py` uses the real `tick` package
(`tick.hawkes.SimuHawkesExpKern` to synthesize, `tick.hawkes.HawkesExpKern`
for the maximum-likelihood fit). The metric math is vendored in
`fit_hawkes`, following `~/workspace/hawkes/hawkes_fit.py`:

- news-to-price impact = `alpha[1, 0]` (alpha_10)
- half-life = `ln(2) / beta`
- endogeneity = spectral radius (max |eigenvalue|) of the alpha matrix;
  regime is sub-critical below 1, explosive at or above 1

`hawkes_fit.py` itself is deliberately NOT imported: it simulates, fits,
and prints at import time. Only `compute_compensator` in that file is
reusable, and the adapter does not need it.

The event streams are synthetic (seeded SimuHawkesExpKern), so the tool is
`simulated: true`; the estimator is the real tick fit. One stream time unit
is treated as one minute of the requested window.

## Swapping in live data later

Each adapter has one clearly marked synthetic-data factory
(`make_synthetic_panel`, `make_synthetic_books`, `simulate_streams`).
Point those at a real feed and everything downstream keeps working; flip
`simulated` to False and write a real freshness string in the tool when the
data stops being synthetic.
