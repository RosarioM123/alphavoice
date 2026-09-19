"""Contract tests: summary/detail shape, precision rules, honest silence."""

import pytest

from tools.contract import (
    make_key_number,
    make_result,
    no_data_result,
    speak_number,
)


def _valid(**over):
    kw = dict(
        verdict="Signal scan ranks AAPL first",
        key_numbers=[make_key_number("AAPL expected return", 0.023)],
        confidence="medium",
        data_freshness="Simulated panel, computed just now.",
        offer="Say detail for the full ranking.",
        detail={"n": 1},
        simulated=True,
    )
    kw.update(over)
    return make_result(**kw)


def test_valid_result_shape():
    r = _valid()
    assert set(r.keys()) == {"summary", "detail", "simulated"}
    assert set(r["summary"].keys()) == {
        "verdict",
        "key_numbers",
        "confidence",
        "data_freshness",
        "offer",
    }


def test_verdict_gets_trailing_period():
    assert _valid()["summary"]["verdict"] == "Signal scan ranks AAPL first."


def test_verdict_two_sentences_rejected():
    with pytest.raises(ValueError):
        _valid(verdict="Scan done. Here is more")


def test_verdict_question_rejected():
    with pytest.raises(ValueError):
        _valid(verdict="Scan done?")


def test_verdict_decimal_in_number_allowed():
    r = _valid(verdict="Edge is about 0.6 percent after costs")
    assert r["summary"]["verdict"].startswith("Edge is about 0.6 percent")


def test_bad_confidence_rejected():
    with pytest.raises(ValueError):
        _valid(confidence="certain")


def test_each_confidence_level_accepted():
    for c in ("high", "medium", "low"):
        assert _valid(confidence=c)["summary"]["confidence"] == c


def test_empty_offer_rejected():
    with pytest.raises(ValueError):
        _valid(offer="")


def test_empty_freshness_rejected():
    with pytest.raises(ValueError):
        _valid(data_freshness="")


def test_detail_must_be_dict():
    with pytest.raises(ValueError):
        _valid(detail=[1, 2])


def test_simulated_must_be_bool():
    with pytest.raises(ValueError):
        _valid(simulated="yes")


def test_simulated_true_requires_disclosure():
    with pytest.raises(ValueError):
        _valid(simulated=True, data_freshness="Fresh live data, just now.")


def test_simulated_false_no_disclosure_needed():
    r = _valid(simulated=False, data_freshness="Live feed, 2 minutes old.")
    assert r["simulated"] is False


def test_key_number_exact_keys():
    with pytest.raises(ValueError):
        _valid(key_numbers=[{"label": "x", "value": 1.0}])


def test_key_number_bool_value_rejected():
    with pytest.raises(ValueError):
        make_key_number("flag", True)


def test_key_number_empty_label_rejected():
    with pytest.raises(ValueError):
        make_key_number("", 1.0)


def test_spoken_too_precise_rejected():
    kn = {"label": "edge", "spoken": "0.63412", "value": 0.6341}
    with pytest.raises(ValueError):
        _valid(key_numbers=[kn])


def test_spoken_rounded_ok():
    kn = {"label": "edge", "spoken": "about 0.6", "value": 0.6341}
    assert _valid(key_numbers=[kn])


def test_speak_number_examples():
    assert speak_number(0.6341) == "about 0.6"
    assert speak_number(42.73) == "about 43"
    assert speak_number(1234.5) == "about 1230"
    assert speak_number(-0.3) == "minus 0.3"
    assert speak_number(0) == "0"
    assert speak_number(0.05) == "about 0.05"


def test_make_key_number_auto_spoken():
    kn = make_key_number("edge", 0.6341)
    assert kn["spoken"] == "about 0.6"
    assert kn["value"] == 0.6341


def test_no_data_result_honest_silence():
    r = no_data_result("the book was empty")
    assert r["summary"]["confidence"] == "low"
    assert r["summary"]["key_numbers"] == []
    assert "do not have usable data" in r["summary"]["verdict"]
    assert "the book was empty" in r["summary"]["verdict"]
    assert r["simulated"] is True
    assert r["summary"]["offer"]  # still ends with an offer
