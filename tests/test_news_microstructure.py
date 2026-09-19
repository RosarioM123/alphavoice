"""news_microstructure tests: real tick fit on synthetic streams."""

import numpy as np
import pytest

from adapters.hawkes_adapter import fit_hawkes, run_news_microstructure, simulate_streams
from tools.news_microstructure import news_microstructure


@pytest.fixture(scope="module")
def small_run():
    ts = simulate_streams(end_time=120.0, seed=3)
    return fit_hawkes(ts, betas=np.linspace(1.0, 4.0, 4))


def test_fit_metrics_sane(small_run):
    m = small_run
    assert 0.0 <= m["alpha_10"] <= 1.0
    assert m["half_life"] > 0
    assert 0.0 < m["spectral_radius"] < 2.0
    assert m["regime"] in ("sub-critical", "explosive")


def test_fit_recovers_planted_impact(small_run):
    # planted alpha[1,0] = 0.5; the fit should be in the right neighborhood
    assert abs(small_run["alpha_10"] - 0.5) < 0.3


def test_fit_recovers_planted_beta(small_run):
    # planted beta = 2.0
    assert abs(small_run["beta"] - 2.0) < 1.5


def test_half_life_matches_beta(small_run):
    assert small_run["half_life"] == pytest.approx(np.log(2) / small_run["beta"])


def test_run_microstructure_window():
    out = run_news_microstructure(window_minutes=120, seed=5)
    assert out["ok"] is True
    assert out["simulated"] is True
    assert out["n_events"] > 20
    assert "synthetic" in out["freshness"].lower()


def test_run_deterministic_seed():
    a = run_news_microstructure(window_minutes=120, seed=5)
    b = run_news_microstructure(window_minutes=120, seed=5)
    assert a["alpha_10"] == b["alpha_10"]
    assert a["beta"] == b["beta"]


def test_run_bad_window_honest():
    out = run_news_microstructure(window_minutes=0)
    assert out["ok"] is False


def test_tool_contract_shape():
    r = news_microstructure("how does news move prices?", window_minutes=120)
    assert r["simulated"] is True
    assert r["detail"]["regime"] in ("sub-critical", "explosive")
    labels = [k["label"] for k in r["summary"]["key_numbers"]]
    assert any("alpha" in l for l in labels)
    assert any("half" in l for l in labels)


def test_tool_verdict_names_regime():
    r = news_microstructure("q", window_minutes=120)
    assert r["detail"]["regime"] in r["summary"]["verdict"]


def test_tool_bad_window_honest_silence():
    r = news_microstructure("q", window_minutes=-3)
    assert r["summary"]["confidence"] == "low"
    assert "do not have usable data" in r["summary"]["verdict"]
