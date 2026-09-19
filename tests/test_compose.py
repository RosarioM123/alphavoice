"""composed_brief tests: contract shape, one-sentence verdict, speech rules,
precision budget, honest failure path."""

import re

import pytest

import compose
from compose import composed_brief
from tools.contract import _sig_budget, _spoken_sig_digits

QUESTION = "Morning brief: this morning's CPI print, anything mispriced, and today's signals"


def _result(question=QUESTION):
    return composed_brief(question)


def test_contract_shape_simulated_and_freshness():
    r = _result()
    assert set(r.keys()) == {"summary", "detail", "simulated"}
    assert set(r["summary"].keys()) == {
        "verdict",
        "key_numbers",
        "confidence",
        "data_freshness",
        "offer",
    }
    assert r["simulated"] is True
    freshness = r["summary"]["data_freshness"].lower()
    assert "simulat" in freshness or "synthetic" in freshness
    assert r["summary"]["confidence"] == "medium"
    assert r["summary"]["offer"]  # every summary ends with an offer


def test_verdict_is_one_sentence_with_three_clauses():
    verdict = _result()["summary"]["verdict"]
    assert verdict.endswith(".")
    body = verdict[:-1]
    scrubbed = re.sub(r"\d[\d,]*\.\d+", "NUM", body)
    assert "." not in scrubbed and "?" not in scrubbed and "!" not in scrubbed
    assert body.count(";") >= 2  # three clauses: news, mispricing, signals


def test_key_numbers_three_entries_one_per_tool():
    keys = _result()["summary"]["key_numbers"]
    assert len(keys) == 3
    labels = [k["label"] for k in keys]
    assert any("half life" in label for label in labels)
    assert any("net edge" in label for label in labels)
    assert any("expected return" in label for label in labels)
    for k in keys:
        assert _spoken_sig_digits(k["spoken"]) <= _sig_budget(k["value"]) + 1


def test_verdict_covers_all_three_lenses_with_real_numbers():
    verdict = _result()["summary"]["verdict"].lower()
    assert "30 seconds" in verdict  # half-life 0.495 min, from news tool
    assert "0.05" in verdict  # net edge per contract, from mispricing tool
    assert "msft" in verdict  # top symbol, from signal tool
    assert "1.6 percent" in verdict  # MSFT expected return 0.01597 as percent


def test_verdict_numbers_not_over_precise():
    verdict = _result()["summary"]["verdict"]
    for m in re.finditer(r"\d\.\d+", verdict):
        assert len(m.group(0).split(".")[1]) <= 2, f"over-precise: {m.group(0)}"
    for m in re.finditer(r"\d{4,}", verdict.replace(",", "")):
        pytest.fail(f"unrounded integer in verdict: {m.group(0)}")


def test_detail_contains_all_three_tool_outputs():
    detail = _result()["detail"]
    assert detail["question"] == QUESTION
    assert detail["failed"] == []
    for name in ("news_microstructure", "mispricing_check", "signal_scan"):
        out = detail[name]
        assert set(out.keys()) == {"summary", "detail", "simulated"}, name
        assert out["simulated"] is True
    assert detail["mispricing_check"]["detail"]["paper_only"] is True


def _boom(*args, **kwargs):
    raise RuntimeError("fixture exploded")


def test_one_tool_failure_still_returns_with_low_confidence(monkeypatch):
    monkeypatch.setattr(compose, "signal_scan", _boom)
    r = _result()
    failed_tools = [f["tool"] for f in r["detail"]["failed"]]
    assert "signal_scan" in failed_tools
    assert r["summary"]["confidence"] == "low"
    assert len(r["summary"]["key_numbers"]) == 2  # the other two lenses
    verdict = r["summary"]["verdict"]
    assert verdict.endswith(".")
    assert "msft" not in verdict.lower()


def test_all_tools_failure_is_honest_silence(monkeypatch):
    for name in ("signal_scan", "mispricing_check", "news_microstructure"):
        monkeypatch.setattr(compose, name, _boom)
    r = _result()
    assert len(r["detail"]["failed"]) == 3
    assert r["summary"]["confidence"] == "low"
    assert r["summary"]["key_numbers"] == []
    assert "failed" in r["summary"]["verdict"].lower()
    assert r["summary"]["offer"]
    assert r["simulated"] is True
