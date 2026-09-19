"""ODDS engine adapter. PAPER ONLY.

Wraps the user's real ODDS engines from ~/workspace/odds-prediction-mispricing
by adding the repo root to sys.path (clean import, no vendoring):

- backend.arbitrage.costs.walk_book: full-book VWAP for a target size
- backend.arbitrage.costs.FeeModel.taker_fee: venue taker fees
- backend.arbitrage.costs.build_cost_breakdown: cost waterfall -> net_edge
- backend.arbitrage.sizing.size_position: fractional Kelly sizing

There are NO order paths here: no venue clients, no API keys, no execution
code. The tool reports a hypothetical size on a synthetic two-venue book
fixture (labeled simulated). Nothing is bought, sold, or sent anywhere.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ODDS_ROOT = Path(os.environ.get("ODDS_ROOT", Path.home() / "workspace" / "odds-prediction-mispricing"))
if str(ODDS_ROOT) not in sys.path:
    sys.path.insert(0, str(ODDS_ROOT))

from backend.arbitrage.costs import (  # noqa: E402
    FeeModel,
    build_cost_breakdown,
    half_spread_cost,
    walk_book,
)
from backend.arbitrage.sizing import size_position  # noqa: E402
from backend.schemas import Market, OrderBook, OrderBookLevel, Outcome, Venue  # noqa: E402

KELLY_FRACTIONS = (0.25, 0.50, 1.00)
P_WIN_ASSUMED = 0.55  # explicit assumption, labeled upstream


def _levels(prices_sizes: list[tuple[float, float]]) -> list[OrderBookLevel]:
    return [OrderBookLevel(price=p, size=s) for p, s in prices_sizes]


def make_synthetic_books() -> tuple[OrderBook, OrderBook, Market, Market]:
    """Two-venue synthetic fixture for the same event outcome. Labeled simulated."""
    poly_book = OrderBook(
        market_id="POLY-FED-SEP25-YES",
        venue=Venue.POLYMARKET,
        outcome=Outcome.YES,
        bids=_levels([(0.58, 200.0), (0.57, 300.0)]),
        asks=_levels([(0.60, 120.0), (0.62, 200.0), (0.64, 150.0)]),
    )
    kalshi_book = OrderBook(
        market_id="KALSHI-FED-SEP25-YES",
        venue=Venue.KALSHI,
        outcome=Outcome.YES,
        bids=_levels([(0.65, 80.0), (0.64, 150.0)]),
        asks=_levels([(0.67, 100.0), (0.69, 120.0)]),
    )
    poly_market = Market(
        market_id="POLY-FED-SEP25-YES",
        venue=Venue.POLYMARKET,
        event_id="FED-SEP25",
        question="Fed funds target cut at September meeting? (fixture)",
        outcome=Outcome.YES,
        taker_fee_rate=0.0,
    )
    kalshi_market = Market(
        market_id="KALSHI-FED-SEP25-YES",
        venue=Venue.KALSHI,
        event_id="FED-SEP25",
        question="Fed funds target cut at September meeting? (fixture)",
        outcome=Outcome.YES,
    )
    return poly_book, kalshi_book, poly_market, kalshi_market


def run_mispricing_check(
    size: float = 100.0,
    bankroll: float = 100.0,
    kelly_fraction: float = 0.25,
    max_position: float = 50.0,
) -> dict:
    """Full-book VWAP + cost waterfall + fractional Kelly size on the fixture."""
    if kelly_fraction not in KELLY_FRACTIONS:
        return {"ok": False, "reason": f"kelly_fraction must be one of {KELLY_FRACTIONS}"}
    if size <= 0:
        return {"ok": False, "reason": "size must be positive"}

    poly_book, kalshi_book, poly_market, _ = make_synthetic_books()

    buy = walk_book(poly_book, "buy", size)
    if buy.filled <= 0 or buy.vwap is None:
        return {"ok": False, "reason": "Polymarket fixture book has no asks to walk"}

    kalshi_bid = kalshi_book.best_bid
    if kalshi_bid is None:
        return {"ok": False, "reason": "Kalshi fixture book has no bids"}

    fees = FeeModel()
    taker = fees.taker_fee(poly_market, buy.filled, buy.vwap)
    half_spread, _ = half_spread_cost(poly_book)
    slippage_total = max(0.0, buy.vwap - poly_book.best_ask) * buy.filled

    raw_edge = kalshi_bid - buy.vwap
    breakdown = build_cost_breakdown(
        raw_edge_per_contract=raw_edge,
        size=buy.filled,
        fees_total=taker.fee_dollars,
        slippage_total=slippage_total,
        spread_info_per_contract=half_spread or 0.0,
        latency_total=0.0,
    )
    net_edge = breakdown.net_edge

    sizing = None
    if net_edge > 0:
        sizing = size_position(
            net_edge_per_contract=net_edge,
            cost_per_contract=buy.vwap,
            liquidity=buy.filled,
            bankroll=bankroll,
            fraction=kelly_fraction,
            max_position=max_position,
            p_win=P_WIN_ASSUMED,
            p_win_is_placeholder=True,
        )

    return {
        "ok": True,
        "simulated": True,
        "freshness": (
            "Synthetic two-venue order books (fixture, not live markets); "
            "computed just now with the real ODDS walk_book, FeeModel, cost "
            "breakdown, and fractional Kelly sizer. PAPER ONLY: hypothetical size, "
            f"p_win {P_WIN_ASSUMED} is an uncalibrated assumption."
        ),
        "actionable": net_edge > 0,
        "buy_venue": "Polymarket",
        "sell_venue": "Kalshi",
        "contracts_filled": buy.filled,
        "contracts_shortfall": buy.shortfall,
        "buy_vwap": buy.vwap,
        "sell_reference": kalshi_bid,
        "raw_edge_per_contract": round(raw_edge, 6),
        "fees_total": round(taker.fee_dollars, 6),
        "slippage_total": round(slippage_total, 6),
        "net_edge_per_contract": net_edge,
        "hypothetical_quantity": sizing.quantity if sizing else 0.0,
        "hypothetical_stake_dollars": sizing.stake_dollars if sizing else 0.0,
        "kelly_full": sizing.kelly_full if sizing else 0.0,
        "capped_by": sizing.capped_by if sizing else None,
        "sizing_notes": sizing.notes if sizing else [],
    }
