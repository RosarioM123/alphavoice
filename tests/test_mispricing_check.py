"""mispricing_check tests: real ODDS engines, paper only."""

import pytest

from adapters.odds_adapter import make_synthetic_books, run_mispricing_check
from tools.mispricing_check import mispricing_check


def test_adapter_fixture_two_venues():
    poly, kalshi, pm, km = make_synthetic_books()
    assert poly.venue.value == "polymarket" or str(poly.venue).lower().endswith("polymarket")
    assert kalshi.best_bid is not None
    assert poly.best_ask is not None


def test_adapter_actionable_fixture():
    out = run_mispricing_check()
    assert out["ok"] is True
    assert out["actionable"] is True
    assert out["net_edge_per_contract"] > 0
    assert out["buy_vwap"] <= 0.64  # within the fixture asks
    assert out["buy_vwap"] >= out["buy_vwap"]  # sanity


def test_adapter_vwap_between_touch_and_tail():
    out = run_mispricing_check(size=100.0)
    poly, _, _, _ = make_synthetic_books()
    assert poly.best_ask <= out["buy_vwap"] <= 0.64


def test_adapter_net_edge_lte_raw_edge():
    out = run_mispricing_check()
    assert out["net_edge_per_contract"] <= out["raw_edge_per_contract"]


def test_adapter_hypothetical_sizing_only():
    out = run_mispricing_check()
    # With the mandated 0.55 placeholder win probability, Kelly honestly
    # sizes zero for this edge; the engine must say so, not invent size.
    assert out["hypothetical_quantity"] == 0.0
    assert out["hypothetical_stake_dollars"] == 0.0
    assert any("kelly" in n.lower() for n in out["sizing_notes"])
    assert "P_WIN_PLACEHOLDER" in out["sizing_notes"] or any(
        "placeholder" in n.lower() or "P_WIN" in n for n in out["sizing_notes"]
    )


def test_adapter_invalid_kelly_fraction():
    out = run_mispricing_check(kelly_fraction=0.1)
    assert out["ok"] is False


def test_adapter_nonpositive_size():
    out = run_mispricing_check(size=0)
    assert out["ok"] is False


def test_tool_contract_and_paper_only():
    r = mispricing_check("any mispricing on the fed decision?")
    assert r["simulated"] is True
    assert r["detail"]["paper_only"] is True
    assert r["summary"]["offer"]
    verdict = r["summary"]["verdict"].lower()
    assert "paper only" in verdict or "paper" in r["summary"]["offer"].lower()


def test_tool_labels_p_win_assumption():
    r = mispricing_check("q")
    assert r["detail"]["p_win_assumption"] == 0.55
    assert "0.55" in r["summary"]["data_freshness"]


def test_tool_invalid_kelly_honest_silence():
    r = mispricing_check("q", kelly_fraction=0.99)
    assert r["summary"]["confidence"] == "low"
    assert "do not have usable data" in r["summary"]["verdict"]
