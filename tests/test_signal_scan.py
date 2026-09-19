"""signal_scan tests: real SIGNAL engines on a synthetic panel."""

import re

import pytest

from adapters.signal_adapter import FAMILIES, run_signal_scan
from tools.signal_scan import signal_scan


def test_adapter_runs_all_six_families():
    assert set(FAMILIES.keys()) == {
        "momentum",
        "mean_reversion",
        "volatility",
        "volume",
        "xsectional",
        "regime",
    }
    out = run_signal_scan(["AAPL", "MSFT", "NVDA"])
    assert out["ok"] is True
    assert out["n_features"] > 10  # six families contribute


def test_adapter_uses_real_ridge_combiner():
    out = run_signal_scan(["AAPL", "MSFT"])
    # standardized coefs exist for every feature: real RidgeCombiner path
    assert len(out["top_features"]) == 5
    assert all("standardized_coef" in f for f in out["top_features"])


def test_adapter_deterministic():
    a = run_signal_scan(["AAPL"])
    b = run_signal_scan(["AAPL"])
    assert a["top_symbols"] == b["top_symbols"]
    assert a["top_features"] == b["top_features"]


def test_adapter_empty_symbols():
    out = run_signal_scan([])
    assert out["ok"] is False


def test_tool_contract_shape():
    r = signal_scan("scan tech stocks", symbols="AAPL,MSFT,NVDA")
    assert set(r.keys()) == {"summary", "detail", "simulated"}
    assert r["simulated"] is True
    assert r["summary"]["confidence"] in ("high", "medium", "low")
    assert r["summary"]["offer"]
    assert "Simulat" in r["summary"]["data_freshness"] or "simulat" in r["summary"]["data_freshness"]


def test_tool_verdict_single_sentence():
    r = signal_scan("q", symbols="AAPL")
    v = r["summary"]["verdict"]
    scrubbed = re.sub(r"\d[\d,]*\.\d+", "NUM", v.rstrip("."))
    assert "." not in scrubbed


def test_tool_ranks_requested_symbols():
    r = signal_scan("q", symbols="AAPL,MSFT", top_n=2)
    syms = [t["symbol"] for t in r["detail"]["top_symbols"]]
    assert set(syms) <= {"AAPL", "MSFT"}
    assert len(syms) <= 2


def test_tool_spy_not_ranked():
    r = signal_scan("q", symbols="AAPL,MSFT")
    syms = [t["symbol"] for t in r["detail"]["top_symbols"]]
    assert "SPY" not in syms  # benchmark column only


def test_tool_empty_symbols_honest_silence():
    r = signal_scan("q", symbols="   ")
    assert r["summary"]["confidence"] == "low"
    assert "do not have usable data" in r["summary"]["verdict"]


def test_tool_bad_horizon_honest_silence():
    r = signal_scan("q", symbols="AAPL", horizon_days=0)
    assert r["summary"]["confidence"] == "low"
