"""SIGNAL engine adapter.

Wraps the user's real SIGNAL engines from ~/workspace/signal-build by adding
the repo root to sys.path (clean import, no vendoring, no copies):

- signals.momentum.momentum_features / mean_reversion / volatility / volume /
  xsectional / regime (six signal families)
- models.combine.RidgeCombiner (ridge combiner with standardized coefs)

The adapter generates a small synthetic price/volume panel (deterministic
seed, labeled simulated) because no live market feed is attached, runs the
REAL signal families and the REAL RidgeCombiner on it, and returns ranked
signals. The numbers are simulated; the engine code path is real.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SIGNAL_ROOT = Path(os.environ.get("SIGNAL_ROOT", Path.home() / "workspace" / "signal-build"))
if str(SIGNAL_ROOT) not in sys.path:
    sys.path.insert(0, str(SIGNAL_ROOT))

from models.combine import RidgeCombiner  # noqa: E402
from signals.mean_reversion import mean_reversion_features  # noqa: E402
from signals.momentum import momentum_features  # noqa: E402
from signals.regime import regime_features  # noqa: E402
from signals.volatility import volatility_features  # noqa: E402
from signals.volume import volume_features  # noqa: E402
from signals.xsectional import xsectional_features  # noqa: E402

FAMILIES = {
    "momentum": lambda p, v: momentum_features(p, v),
    "mean_reversion": lambda p, v: mean_reversion_features(p, v),
    "volatility": lambda p, v: volatility_features(p),
    "volume": lambda p, v: volume_features(p, v),
    "xsectional": lambda p, v: xsectional_features(p),
    "regime": lambda p, v: regime_features(p),
}

BENCHMARK_SYMBOL = "SPY"  # xsectional_features expects a SPY column


def make_synthetic_panel(symbols: list[str], days: int = 300, seed: int = 7) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Deterministic synthetic price/volume panel. Labeled simulated upstream."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=days)
    cols = list(dict.fromkeys(symbols + [BENCHMARK_SYMBOL]))
    drift = rng.normal(0.0004, 0.0006, size=len(cols))
    vol = rng.uniform(0.008, 0.02, size=len(cols))
    rets = rng.normal(drift, vol, size=(days, len(cols)))
    prices = pd.DataFrame(np.cumprod(1 + rets, axis=0) * 100.0, index=dates, columns=cols)
    volumes = pd.DataFrame(
        rng.integers(1_000_000, 8_000_000, size=(days, len(cols))).astype(float),
        index=dates,
        columns=cols,
    )
    return prices, volumes


def _stack_panel(panel: pd.DataFrame, symbols: list[str]) -> pd.DataFrame:
    """Reshape a feature panel to (date, symbol) rows.

    Most families return MultiIndex columns (feature x symbol); stack those.
    Market-wide families (regime) return flat columns: broadcast them to every
    symbol.
    """
    if isinstance(panel.columns, pd.MultiIndex):
        stacked = panel.stack(level=1).sort_index()
    else:
        idx = pd.MultiIndex.from_product(
            [panel.index, symbols], names=["date", "symbol"]
        )
        stacked = pd.DataFrame(
            np.repeat(panel.to_numpy(), len(symbols), axis=0),
            index=idx,
            columns=panel.columns,
        )
    stacked.index = stacked.index.set_names(["date", "symbol"])
    return stacked.sort_index()


def run_signal_scan(
    symbols: list[str],
    horizon_days: int = 5,
    top_n: int = 3,
    seed: int = 7,
) -> dict:
    """Run all six SIGNAL families + ridge combiner on a synthetic panel."""
    if not symbols:
        return {"ok": False, "reason": "no symbols were provided"}
    prices, volumes = make_synthetic_panel(symbols, seed=seed)
    syms = list(prices.columns)

    panels = {name: fn(prices, volumes) for name, fn in FAMILIES.items()}
    features = pd.concat(
        [_stack_panel(p, syms) for p in panels.values()], axis=1
    )
    features = features.loc[:, ~features.columns.duplicated()]

    fwd = prices.pct_change(horizon_days).shift(-horizon_days).stack()
    y = fwd.rename("target").reindex(features.index)

    data = features.copy()
    data["target"] = y
    data = data.dropna()
    if data.empty or data.shape[0] < 20:
        return {"ok": False, "reason": "not enough clean bars to fit the combiner"}

    X = data.drop(columns=["target"])
    target = data["target"]
    combiner = RidgeCombiner(alpha=1.0)
    combiner.fit(X, target)
    coefs = combiner.standardized_coefs().sort_values(key=abs, ascending=False)

    last_date = X.index.get_level_values(0).max()
    X_now = X.xs(last_date, level=0)
    preds = combiner.predict(X_now).sort_values(ascending=False)

    top_symbols = [
        {"symbol": sym, "expected_return": float(preds.loc[sym])}
        for sym in preds.head(top_n).index
        if sym != BENCHMARK_SYMBOL
    ]
    top_features = [
        {"feature": name, "standardized_coef": float(coefs.loc[name])}
        for name in coefs.head(5).index
    ]
    return {
        "ok": True,
        "simulated": True,
        "freshness": (
            "Simulated price and volume panel (deterministic seed 7, 300 bars); "
            "computed just now with the real SIGNAL signal families and ridge combiner."
        ),
        "symbols": [s for s in prices.columns if s != BENCHMARK_SYMBOL],
        "top_symbols": top_symbols,
        "top_features": top_features,
        "n_features": int(X.shape[1]),
        "n_rows": int(X.shape[0]),
    }
