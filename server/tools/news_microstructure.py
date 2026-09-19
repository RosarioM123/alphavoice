"""news_microstructure: measure how news moves prices with a Hawkes model."""

from __future__ import annotations

from adapters.hawkes_adapter import run_news_microstructure
from tools.contract import make_key_number, make_result, no_data_result


def news_microstructure(query: str, window_minutes: int = 390) -> dict:
    """Fit a bivariate Hawkes model (news -> price) on synthetic streams.

    Reports alpha_10 (news-to-price impact), the half-life ln(2)/beta, and the
    sub-critical vs explosive regime from the spectral radius. Simulated.
    """
    out = run_news_microstructure(window_minutes=window_minutes)
    if not out.get("ok"):
        return no_data_result(out.get("reason", "unknown failure"), detail={"query": query})

    verdict = (
        f"News impact is {out['regime']}: each news event adds about "
        f"{round(out['alpha_10'], 2)} expected price jumps, decaying with a half-life "
        f"of about {round(out['half_life'], 1)} minutes"
    )
    return make_result(
        verdict=verdict,
        key_numbers=[
            make_key_number("news to price impact alpha 10", out["alpha_10"]),
            make_key_number("impact half life minutes", out["half_life"]),
            make_key_number("spectral radius", out["spectral_radius"]),
        ],
        confidence="medium",
        data_freshness=out["freshness"],
        offer="Say detail for the full fit, including beta and the event counts.",
        detail={
            "query": query,
            "beta": out["beta"],
            "regime": out["regime"],
            "log_likelihood": out["log_likelihood"],
            "n_events": out["n_events"],
            "estimator": "tick.hawkes.HawkesExpKern maximum likelihood",
        },
        simulated=True,
    )
