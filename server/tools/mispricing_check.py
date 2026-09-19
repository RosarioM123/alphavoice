"""mispricing_check: check cross-venue mispricing with the ODDS engine.

PAPER ONLY. Reports a hypothetical fractional-Kelly size. Never executes,
never touches order paths, never needs API keys.
"""

from __future__ import annotations

from adapters.odds_adapter import KELLY_FRACTIONS, P_WIN_ASSUMED, run_mispricing_check
from tools.contract import make_key_number, make_result, no_data_result


def mispricing_check(
    query: str,
    size: float = 100.0,
    bankroll: float = 100.0,
    kelly_fraction: float = 0.25,
) -> dict:
    """Walk the synthetic two-venue books, build the cost waterfall, size it."""
    if kelly_fraction not in KELLY_FRACTIONS:
        return no_data_result(
            f"kelly_fraction must be one of {KELLY_FRACTIONS}",
            detail={"query": query},
        )
    out = run_mispricing_check(
        size=size, bankroll=bankroll, kelly_fraction=kelly_fraction
    )
    if not out.get("ok"):
        return no_data_result(out.get("reason", "unknown failure"), detail={"query": query})

    if not out["actionable"]:
        return make_result(
            verdict="No actionable mispricing after costs: the edge does not survive fees and slippage",
            key_numbers=[
                make_key_number("net edge per contract", out["net_edge_per_contract"]),
                make_key_number("buy VWAP", out["buy_vwap"]),
            ],
            confidence="medium",
            data_freshness=out["freshness"],
            offer="Say detail for the full cost waterfall, or paper only, nothing executes.",
            detail={**out, "query": query, "paper_only": True},
            simulated=True,
        )

    if out["hypothetical_quantity"] > 0:
        verdict = (
            f"Mispricing found: buy on {out['buy_venue']} and the reference sell on "
            f"{out['sell_venue']} leaves a positive edge, sizing about "
            f"{round(out['hypothetical_quantity'], 1)} contracts, paper only"
        )
    else:
        verdict = (
            f"Mispricing found after costs, but at the assumed "
            f"{int(P_WIN_ASSUMED * 100)} percent win probability the Kelly sizer "
            f"recommends no position, paper only"
        )
    return make_result(
        verdict=verdict,
        key_numbers=[
            make_key_number("net edge per contract", out["net_edge_per_contract"]),
            make_key_number("hypothetical contracts", out["hypothetical_quantity"]),
            make_key_number("hypothetical stake dollars", out["hypothetical_stake_dollars"]),
            make_key_number("buy VWAP", out["buy_vwap"]),
        ],
        confidence="medium",
        data_freshness=out["freshness"],
        offer="Say detail for the full cost waterfall, or paper only, nothing executes.",
        detail={**out, "query": query, "paper_only": True, "p_win_assumption": P_WIN_ASSUMED},
        simulated=True,
    )
