"""signal_scan: scan market signals with the SIGNAL engine."""

from __future__ import annotations

from adapters.signal_adapter import run_signal_scan
from tools.contract import make_key_number, make_result, no_data_result


def signal_scan(
    query: str,
    symbols: str = "AAPL,MSFT,NVDA",
    horizon_days: int = 5,
    top_n: int = 3,
) -> dict:
    """Scan the six SIGNAL signal families and rank symbols by expected return.

    Runs the real SIGNAL engines on a synthetic price panel (simulated).
    """
    syms = [s.strip().upper() for s in (symbols or "").split(",") if s.strip()]
    if not syms:
        return no_data_result("no ticker symbols were provided", detail={"query": query})
    if horizon_days <= 0:
        return no_data_result("horizon_days must be positive", detail={"query": query})

    out = run_signal_scan(syms, horizon_days=horizon_days, top_n=max(1, top_n))
    if not out.get("ok"):
        return no_data_result(out.get("reason", "unknown failure"), detail={"query": query})

    top = out["top_symbols"]
    lead = top[0] if top else {"symbol": syms[0], "expected_return": 0.0}
    feat = out["top_features"][0] if out["top_features"] else {"feature": "none", "standardized_coef": 0.0}
    verdict = (
        f"Signal scan ranks {lead['symbol']} first, with about "
        f"{round(lead['expected_return'] * 100, 1)} percent expected return over "
        f"{horizon_days} days, driven mainly by {feat['feature'].replace('_', ' ')}"
    )
    keys = [make_key_number(f"{t['symbol']} expected return", t["expected_return"]) for t in top]
    keys.append(make_key_number("top feature weight", feat["standardized_coef"]))
    return make_result(
        verdict=verdict,
        key_numbers=keys,
        confidence="medium",
        data_freshness=out["freshness"],
        offer="Say detail for the full ranking and the top signal weights.",
        detail={
            "query": query,
            "symbols": out["symbols"],
            "top_symbols": out["top_symbols"],
            "top_features": out["top_features"],
            "n_features": out["n_features"],
            "n_rows": out["n_rows"],
            "engine": "SIGNAL six families + RidgeCombiner(alpha=1.0)",
        },
        simulated=True,
    )
